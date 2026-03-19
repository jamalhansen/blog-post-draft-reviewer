import json
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner
from logic import app
from local_first_common.testing import MockProvider

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_DRAFT = str(FIXTURES / "sample-draft.md")

VALID_RESPONSE = json.dumps({
    "overall": "fail",
    "word_count": 150,
    "post_type": "manifesto",
    "items": [
        {"category": "Hook & Opening", "status": "fail", "note": "No hook."},
        {"category": "Tone", "status": "fail", "note": "Preachy."},
    ],
    "summary": "Post needs significant work on tone and structure.",
})


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
        mock_llm = MockProvider(response=VALID_RESPONSE)
        with patch("logic.resolve_provider", return_value=mock_llm):
            runner.invoke(app, ["-f", SAMPLE_DRAFT, "-n"])
        assert len(mock_llm.calls) == 0

    def test_dry_run_prints_done(self):
        runner = CliRunner()
        mock_llm = MockProvider(response=VALID_RESPONSE)
        with patch("logic.resolve_provider", return_value=mock_llm):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-n"])
        assert "dry-run" in result.output.lower() or "Skipped" in result.output


class TestReviewRun:
    def test_json_output(self):
        runner = CliRunner()
        mock_llm = MockProvider(response=VALID_RESPONSE)
        with patch("logic.resolve_provider", return_value=mock_llm):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-o", "json"])
        assert result.exit_code == 1  # overall=fail -> exit 1
        output_json = json.loads(result.output.split("Done.")[0])
        assert output_json["overall"] == "fail"

    def test_summary_line_printed(self):
        runner = CliRunner()
        mock_llm = MockProvider(response=VALID_RESPONSE)
        with patch("logic.resolve_provider", return_value=mock_llm):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-o", "json"])
        assert "Done." in result.output

    def test_verbose_shows_model(self):
        runner = CliRunner()
        mock_llm = MockProvider(response=VALID_RESPONSE, model="phi4-mini")
        with patch("logic.resolve_provider", return_value=mock_llm):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "ollama", "-v", "-o", "json"])
        assert "phi4-mini" in result.output

    def test_provider_runtime_error_exits_cleanly(self):
        runner = CliRunner()
        with patch("logic.resolve_provider", side_effect=RuntimeError("GROQ_API_KEY not set.")):
            result = runner.invoke(app, ["-f", SAMPLE_DRAFT, "-p", "groq"])
        assert result.exit_code == 1
