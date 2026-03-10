import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from reviewer import app

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_DRAFT = str(FIXTURES / "sample-draft.md")

VALID_RESPONSE = {
    "overall": "fail",
    "word_count": 150,
    "post_type": "manifesto",
    "items": [
        {"category": "Hook & Opening", "status": "fail", "note": "No hook."},
        {"category": "Tone", "status": "fail", "note": "Preachy."},
    ],
    "summary": "Post needs significant work on tone and structure.",
}


class TestCLIFlags:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--file" in result.output
        assert "--provider" in result.output
        assert "--model" in result.output
        assert "--output" in result.output
        assert "--dry-run" in result.output
        assert "--verbose" in result.output

    def test_short_flags_exist(self):
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])
        assert "-f" in result.output
        assert "-p" in result.output
        assert "-m" in result.output
        assert "-o" in result.output
        assert "-n" in result.output
        assert "-v" in result.output

    def test_missing_file_fails(self):
        runner = CliRunner()
        result = runner.invoke(app, [])
        assert result.exit_code != 0

    def test_nonexistent_file_fails(self):
        runner = CliRunner()
        result = runner.invoke(app, ["-f", "no_such_file.md"])
        assert result.exit_code != 0


class TestDryRun:
    def test_dry_run_skips_llm(self):
        runner = CliRunner()
        with patch("reviewer.PROVIDERS") as mock_providers:
            mock_llm = MagicMock()
            mock_llm.model = "phi4-mini"
            mock_providers.__getitem__ = MagicMock(return_value=lambda model=None, **kw: mock_llm)
            mock_providers.__contains__ = MagicMock(return_value=True)
            mock_providers.keys.return_value = ["ollama"]
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-n"])
        mock_llm.complete.assert_not_called()

    def test_dry_run_prints_done(self):
        runner = CliRunner()
        with patch("reviewer.PROVIDERS") as mock_providers:
            mock_llm = MagicMock()
            mock_llm.model = "phi4-mini"
            mock_providers.__getitem__ = MagicMock(return_value=lambda model=None, **kw: mock_llm)
            mock_providers.__contains__ = MagicMock(return_value=True)
            mock_providers.keys.return_value = ["ollama"]
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-n"])
        assert "dry-run" in result.output.lower() or "Skipped" in result.output


class TestReviewRun:
    def _make_llm(self, response=None):
        mock_llm = MagicMock()
        mock_llm.model = "phi4-mini"
        mock_llm.complete.return_value = response if response is not None else VALID_RESPONSE
        return mock_llm

    def test_json_output(self):
        runner = CliRunner()
        mock_llm = self._make_llm()
        with patch("reviewer.PROVIDERS", {"ollama": lambda model=None, **kw: mock_llm}):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-o", "json"])
        assert result.exit_code == 1  # overall=fail -> exit 1
        output_json = json.loads(result.output.split("Done.")[0])
        assert output_json["overall"] == "fail"

    def test_summary_line_printed(self):
        runner = CliRunner()
        mock_llm = self._make_llm()
        with patch("reviewer.PROVIDERS", {"ollama": lambda model=None, **kw: mock_llm}):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-o", "json"])
        assert "Done." in result.output

    def test_verbose_shows_model(self):
        runner = CliRunner()
        mock_llm = self._make_llm()
        with patch("reviewer.PROVIDERS", {"ollama": lambda model=None, **kw: mock_llm}):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-v", "-o", "json"])
        assert "phi4-mini" in result.output

    def test_provider_runtime_error_exits_cleanly(self):
        runner = CliRunner()
        def bad_provider(model=None, **kw):
            raise RuntimeError("GROQ_API_KEY not set.")
        with patch("reviewer.PROVIDERS", {"groq": bad_provider}):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "groq"])
        assert result.exit_code == 1
