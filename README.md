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

| Flag | Short | Default | Description |
|---|---|---|---|
| `--file` | `-f` | *(required)* | Path to the blog post markdown file |
| `--provider` | `-p` | `ollama` | LLM provider (`ollama`, `anthropic`, `gemini`, `groq`, `deepseek`) |
| `--model` | `-m` | provider default | Model name override |
| `--output` | `-o` | `text` | Output format: `text` or `json` |
| `--dry-run` | `-n` | off | Build prompts and show config without calling the LLM |
| `--verbose` | `-v` | off | Print provider/model info and raw LLM response |

### Provider defaults and API keys

| Provider | Default model | Env var |
|---|---|---|
| `ollama` | `phi4-mini` | *(none — local)* |
| `anthropic` | `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| `gemini` | `gemini-2.0-flash` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |
| `groq` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `deepseek` | `deepseek-chat` | `DEEPSEEK_API_KEY` |

## Running Tests

```bash
uv run pytest
```

## Project Structure

```
blog-post-draft-reviewer/
├── reviewer.py          # CLI entry point
├── providers/           # One class per LLM provider
│   ├── __init__.py      # PROVIDERS registry dict
│   ├── base.py          # Abstract BaseProvider
│   ├── ollama_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── groq_provider.py
│   └── deepseek_provider.py
├── schema.py            # Pydantic output schema
├── rubric.py            # Rubric loader
├── prompts.py           # Prompt builders
├── display.py           # Rich terminal output
├── checklist.md         # The review rubric
├── examples/
│   └── sample-draft.md
└── tests/
    ├── fixtures/        # Sample data for tests
    ├── test_schema.py
    ├── test_rubric.py
    ├── test_prompts.py
    ├── test_providers.py
    └── test_reviewer.py
```
