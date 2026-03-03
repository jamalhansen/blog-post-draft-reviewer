from prompts import build_system_prompt, build_user_prompt


class TestBuildSystemPrompt:
    def test_includes_rubric(self):
        rubric = "## Tone\n- Be conversational"
        prompt = build_system_prompt(rubric)
        assert "Tone" in prompt
        assert "Be conversational" in prompt

    def test_includes_json_instruction(self):
        prompt = build_system_prompt("rubric content")
        assert "JSON" in prompt

    def test_returns_string(self):
        prompt = build_system_prompt("anything")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestBuildUserPrompt:
    def test_includes_content(self):
        content = "This is my blog post about Rust."
        prompt = build_user_prompt(content)
        assert content in prompt

    def test_returns_string(self):
        prompt = build_user_prompt("hello")
        assert isinstance(prompt, str)

    def test_empty_content(self):
        prompt = build_user_prompt("")
        assert isinstance(prompt, str)
