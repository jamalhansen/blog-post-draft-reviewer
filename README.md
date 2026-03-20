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
uv run python src/main.py -f examples/sample-draft.md

# Use Anthropic (requires ANTHROPIC_API_KEY)
uv run python src/main.py -f examples/sample-draft.md -p anthropic

# Override the model
uv run python src/main.py -f examples/sample-draft.md -p anthropic -m claude-3-5-sonnet-latest

# Output raw JSON
uv run python src/main.py -f examples/sample-draft.md -o json

# Dry-run: build prompts without calling the LLM
uv run python src/main.py -f examples/sample-draft.md -n

# Verbose: show provider, model, and raw LLM response
uv run python src/main.py -f examples/sample-draft.md -v
```

## CLI Reference

All tools in this series share a common set of CLI flags for model management via [local-first-common](https://github.com/jamalhansen/local-first-common).

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
├── src/
│   ├── main.py          # Typer CLI entry point
│   ├── logic.py         # Core processing logic
│   ├── schema.py        # Pydantic output models
│   ├── prompts.py       # System and user prompt builders
│   ├── display.py       # Rich-based terminal formatting
│   └── rubric.py        # Rubric loading and parsing
├── checklist.md         # The review rubric
├── pyproject.toml       # Managed by uv
└── tests/
    ├── test_main.py     # CLI integration tests via MockProvider
    └── ...
```
