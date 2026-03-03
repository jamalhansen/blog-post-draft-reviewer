import pytest
from pathlib import Path
from rubric import load_rubric

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoadRubric:
    def test_loads_fixture(self):
        rubric = load_rubric(str(FIXTURES / "checklist.md"))
        assert "Hook" in rubric
        assert "Tone" in rubric

    def test_missing_file_returns_message(self):
        result = load_rubric("nonexistent_file.md")
        assert result == "Rubric not found."

    def test_returns_string(self):
        rubric = load_rubric(str(FIXTURES / "checklist.md"))
        assert isinstance(rubric, str)

    def test_file_from_tmp_path(self, tmp_path):
        rubric_file = tmp_path / "rubric.md"
        rubric_file.write_text("## My Rubric\n- Check this")
        result = load_rubric(str(rubric_file))
        assert "My Rubric" in result
