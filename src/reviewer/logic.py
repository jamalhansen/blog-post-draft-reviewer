import json
from pathlib import Path
from typing import Annotated, Optional

import frontmatter
import typer

from local_first_common.llm import strip_json_fences
from local_first_common.providers import PROVIDERS
from local_first_common.cli import (
    dry_run_option,
    no_llm_option,
    verbose_option,
    debug_option,
    resolve_provider,
)
from local_first_common.tracking import register_tool, timed_run
from .rubric import load_rubric
from .schema import ReviewResult
from .prompts import build_system_prompt, build_user_prompt
from .display import display_review

_TOOL = register_tool("blog-post-draft-reviewer")

app = typer.Typer()

def review_post(llm, system_prompt: str, user_prompt: str, verbose: bool = False) -> ReviewResult:
    """Core logic to call LLM and parse the review result."""
    current_user_prompt = user_prompt
    raw_response = None
    
    for attempt in range(2):
        try:
            raw_response = llm.complete(system_prompt, current_user_prompt, response_model=ReviewResult)

            if verbose:
                typer.echo("\n--- Raw LLM Response ---")
                typer.echo(raw_response)

            # The new complete() with response_model returns a dict directly
            if isinstance(raw_response, dict):
                parsed_json = raw_response
            else:
                # Fallback: strip markdown code fences some models add
                parsed_json = json.loads(strip_json_fences(str(raw_response)))
                if "ReviewResult" in parsed_json:
                    parsed_json = parsed_json["ReviewResult"]

            return ReviewResult.model_validate(parsed_json)

        except Exception as e:
            if attempt == 0:
                current_user_prompt += (
                    f"\n\nERROR FROM PREVIOUS ATTEMPT:\n{e}\n\n"
                    "Please ensure your response is a valid JSON object matching the required schema exactly."
                )
                continue
            raise RuntimeError(f"Error parsing LLM response after 2 attempts: {e}")

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
):
    """Review a blog post draft against a rubric."""

    # Standard behavior: no_llm implies dry_run
    if no_llm:
        dry_run = True

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
        llm = resolve_provider(PROVIDERS, provider, model, debug=debug, no_llm=no_llm)
    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    with open(file) as f:
        post_data = frontmatter.load(f)
        content = post_data.content

    if verbose:
        typer.echo(f"Provider : {provider}")
        typer.echo(f"Model    : {llm.model}")
        typer.echo(f"File     : {file}")
        typer.echo(f"Output   : {output}")

    system_prompt = build_system_prompt(rubric)
    user_prompt = build_user_prompt(content)

    if no_llm:
        typer.echo("\n--- System Prompt ---")
        typer.echo(system_prompt)
        typer.echo("\n--- User Prompt (first 500 chars) ---")
        typer.echo(user_prompt[:500])
        typer.echo("\n[no-llm] No LLM call made.")
        typer.echo("Done. Processed: 0, Skipped: 1")
        return

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
