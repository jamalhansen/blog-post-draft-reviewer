from pathlib import Path
from typing import Annotated, Optional

import frontmatter
import typer

from local_first_common.providers import PROVIDERS
from local_first_common.cli import (
    init_config_option,
    dry_run_option,
    no_llm_option,
    verbose_option,
    debug_option,
    resolve_provider,
    resolve_dry_run,
)
from local_first_common.config import get_setting
from local_first_common.tracking import register_tool, timed_run
from .rubric import load_rubric
from .schema import ReviewResult
from .prompts import build_system_prompt, build_user_prompt
from .display import display_review

TOOL_NAME = "blog-post-draft-reviewer"
DEFAULTS = {'provider': 'ollama', 'model': 'llama3'}

_TOOL = register_tool("blog-post-draft-reviewer")

app = typer.Typer()

def review_post(llm, system_prompt: str, user_prompt: str, verbose: bool = False) -> ReviewResult:
    """Core logic to call LLM and parse the review result."""
    # complete() now handles retries and validation automatically
    result = llm.complete(system_prompt, user_prompt, response_model=ReviewResult)
    return ReviewResult.model_validate(result)

@app.command()
def review(
    file: Annotated[Path, typer.Option("--file", "-f", help="Path to blog post markdown file.")],
    provider: Annotated[str, typer.Option("--provider", "-p", help="LLM provider.")] = "ollama",
    model: Annotated[Optional[str], typer.Option("--model", "-m", help="Model name.")] = None,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format: text or json.")] = "text",
    dry_run: bool = dry_run_option(),
    no_llm: bool = no_llm_option(),
    verbose: bool = verbose_option(),
    debug: bool = debug_option(),
    init_config: bool = init_config_option(TOOL_NAME, DEFAULTS),
):
    """Review a blog post draft against a rubric."""
    actual_provider = get_setting(TOOL_NAME, "provider", cli_val=provider, default="ollama")
    actual_model = get_setting(TOOL_NAME, "model", cli_val=model)

    dry_run = resolve_dry_run(dry_run, no_llm)

    # --- Fail fast: validate file exists ---
    if not file.exists():
        typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # --- Fail fast: validate rubric ---
    rubric = load_rubric()
    if rubric == "Rubric not found.":
        typer.secho("Error: checklist.md not found in the current directory.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        actual_provider = get_setting(TOOL_NAME, "provider", cli_val=provider, default="ollama")
    actual_model = get_setting(TOOL_NAME, "model", cli_val=model)
    llm = resolve_provider(PROVIDERS, actual_provider, actual_model, debug=debug, no_llm=no_llm)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    with open(file) as f:
        post_data = frontmatter.load(f)
        content = post_data.content

    if verbose:
        typer.echo(f"Provider : {actual_provider}")
        typer.echo(f"Model    : {actual_model}")
        typer.echo(f"File     : {file}")
        typer.echo(f"Output   : {output}")

    system_prompt = build_system_prompt(rubric)
    user_prompt = build_user_prompt(content)

    try:
        with timed_run("blog-post-draft-reviewer", llm.model, source_location=str(file)) as run:
            result = review_post(llm, system_prompt, user_prompt, verbose=verbose)
            run.item_count = 1
            run.input_tokens = getattr(llm, "input_tokens", None) or None
            run.output_tokens = getattr(llm, "output_tokens", None) or None
        if output == "json":
            typer.echo(result.model_dump_json(indent=2))
        else:
            display_review(result)

        if dry_run:
            typer.echo("\n[dry-run] Results printed to stdout. No files would be modified.")

        typer.echo("Done. Processed: 1, Skipped: 0")

        if result.overall == "fail":
            raise typer.Exit(code=1)

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        typer.echo("Done. Processed: 0, Skipped: 1")
        raise typer.Exit(code=1)
