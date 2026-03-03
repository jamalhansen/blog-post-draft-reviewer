# Blog Draft Reviewer
This is a Python CLI tool that reviews blog post drafts against a fixed rubric and returns structured feedback.

## What This Tool Does
Takes a blog post draft (markdown file) and the Blog Post Writing Checklist rubric, runs them through a local LLM, and returns structured feedback per rubric category. Output is JSON -- machine-readable, but also readable as plain text if you print it nicely.

## How to Run It
```bash
uv run reviewer.py --post examples/sample-draft.md
uv run reviewer.py --post examples/sample-draft.md --backend anthropic # swap to Haiku
uv run reviewer.py --post examples/sample-draft.md --output json # raw JSON
uv run reviewer.py --post examples/sample-draft.md --output text # human-readable (default)
```

## Tech Stack
- Python 3.11+
- Ollama (local inference, default backend) -- model: phi4-mini or llama3.2
- Anthropic Python SDK (optional backend -- Haiku or Sonnet)
- Pydantic -- output schema validation
- Rich -- pretty terminal output (human-readable mode)
- python-frontmatter -- parse markdown + YAML frontmatter
- uv -- package management
