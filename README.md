# Blog Post Draft Reviewer

A Python CLI tool that reviews blog post drafts against a fixed rubric and returns structured feedback.

## Features
- Reviews markdown drafts against a custom checklist (`checklist.md`).
- Supports local LLMs via Ollama (default: `phi4-mini`).
- Supports Anthropic's Claude models.
- Provides structured feedback in JSON or human-readable text.

## Installation
Ensure you have `uv` installed.
```bash
uv sync
```

## Usage
```bash
uv run reviewer.py --post <path_to_draft.md>
```

## Options
- `--post`: Path to the blog post markdown file (required).
- `--backend`: LLM backend (`ollama` or `anthropic`, default: `ollama`).
- `--model`: Specific model name (optional).
- `--output`: Output format (`text` or `json`, default: `text`).
