import pytest
from schema import ReviewResult, ChecklistItem


class TestChecklistItem:
    def test_valid_pass(self):
        item = ChecklistItem(category="Tone", status="pass", note="Sounds great.")
        assert item.status == "pass"

    def test_valid_fail(self):
        item = ChecklistItem(category="Hook", status="fail", note="Weak opener.")
        assert item.category == "Hook"

    def test_valid_warn(self):
        item = ChecklistItem(category="Code", status="warn")
        assert item.note == ""

    def test_invalid_status(self):
        with pytest.raises(Exception):
            ChecklistItem(category="Tone", status="maybe")


class TestReviewResult:
    def _valid_payload(self):
        return {
            "overall": "pass",
            "word_count": 1200,
            "post_type": "practical",
            "items": [
                {"category": "Tone", "status": "pass", "note": "Good tone."},
            ],
            "summary": "Post is solid.",
        }

    def test_valid_result(self):
        result = ReviewResult.model_validate(self._valid_payload())
        assert result.overall == "pass"
        assert result.word_count == 1200
        assert len(result.items) == 1

    def test_overall_fail(self):
        payload = self._valid_payload()
        payload["overall"] = "fail"
        result = ReviewResult.model_validate(payload)
        assert result.overall == "fail"

    def test_missing_required_field(self):
        payload = self._valid_payload()
        del payload["overall"]
        with pytest.raises(Exception):
            ReviewResult.model_validate(payload)

    def test_model_dump_json(self):
        result = ReviewResult.model_validate(self._valid_payload())
        dumped = result.model_dump_json()
        assert "overall" in dumped
        assert "word_count" in dumped
