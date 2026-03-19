# Blog Post Draft Reviewer

A Python CLI tool that reviews blog post drafts against a fixed rubric and returns structured feedback.

## What It Does

Takes a blog post draft (markdown file) and the `checklist.md` rubric, runs them through a local or cloud LLM, and returns structured feedback per rubric category. Output is JSON (machine-readable) or pretty-printed text (default).

## Installation

Requires [uv](https://github.com/astral-sh/uv) and [Ollama](https://ollama.ai) for local inference.

```bash
uv sync
```

## Usage

```bash
# Review with the default local provider (Ollama, phi4-mini)
uv run reviewer.py -f examples/sample-draft.md

# Use Anthropic (requires ANTHROPIC_API_KEY)
uv run reviewer.py -f examples/sample-draft.md -p anthropic

# Override the model
uv run reviewer.py -f examples/sample-draft.md -p anthropic -m claude-sonnet-4-6

# Output raw JSON
uv run reviewer.py -f examples/sample-draft.md -o json

# Dry-run: build prompts without calling the LLM
uv run reviewer.py -f examples/sample-draft.md -n

# Verbose: show provider, model, and raw LLM response
uv run reviewer.py -f examples/sample-draft.md -v
```

## CLI Reference

All tools in this series share a common set of CLI flags for model management.

| Flag | Short | Default | Description |
|---|---|---|---|
| `--file` | `-f` | *(required)* | Path to the blog post markdown file |
| `--provider` | `-p` | `ollama` | LLM provider (`ollama`, `anthropic`, `gemini`, `groq`, `deepseek`) |
| `--model` | `-m` | provider default | Model name override |
| `--output` | `-o` | `text` | Output format: `text` or `json` |
| `--dry-run` | `-n` | off | Build prompts and show config without calling the LLM |
| `--verbose` | `-v` | off | Print info messages and extra context |
| `--debug` | `-d` | off | Show raw system/user prompts and raw LLM responses |

## Running Tests

```bash
uv run pytest
```

## Project Structure

This tool follows the [Local-First AI project blueprint](https://github.com/jamalhansen/local-first-common).

```
blog-post-draft-reviewer/
├── main.py              # Canonical entry point
├── reviewer.py          # CLI command definitions
├── logic.py             # Core processing logic
├── schema.py            # Pydantic output schema
├── prompts.py           # Prompt builders
├── display.py           # Rich terminal output
├── rubric.py            # Rubric loader
├── checklist.md         # The review rubric
├── pyproject.toml       # Managed by uv
└── tests/
    ├── fixtures/        # Sample data for tests
    ├── test_schema.py
    ├── test_reviewer.py # Integration tests via MockProvider
    └── ...
```
