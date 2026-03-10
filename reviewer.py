import json
import os
import sys
from pathlib import Path
from typing import Annotated, Optional

import frontmatter
import typer

from local_first_common.providers import PROVIDERS
from rubric import load_rubric
from schema import ReviewResult
from prompts import build_system_prompt, build_user_prompt
from display import display_review

app = typer.Typer()

_PROVIDER_CHOICES = list(PROVIDERS.keys())
_PROVIDER_DEFAULT = os.environ.get("MODEL_PROVIDER", "ollama")


@app.command()
def review(
    file: Annotated[Path, typer.Option("--file", "-f", help="Path to blog post markdown file.")],
    provider: Annotated[str, typer.Option("--provider", "-p", help=f"LLM provider. Choices: {', '.join(_PROVIDER_CHOICES)}")] = _PROVIDER_DEFAULT,
    model: Annotated[Optional[str], typer.Option("--model", "-m", help="Override the provider's default model.")] = None,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format: text or json.")] = "text",
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Preview without calling the LLM.")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show extra debug output.")] = False,
):
    """Review a blog post draft against a rubric."""

    # --- Fail fast: validate file exists ---
    if not file.exists():
        typer.secho(f"Error: File '{file}' not found.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    # --- Fail fast: validate provider ---
    if provider not in PROVIDERS:
        typer.secho(
            f"Error: Unknown provider '{provider}'. Valid options: {', '.join(PROVIDERS.keys())}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    # --- Fail fast: validate rubric ---
    rubric = load_rubric()
    if rubric == "Rubric not found.":
        typer.secho("Error: checklist.md not found in the current directory.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    try:
        llm = PROVIDERS[provider](model=model)
    except RuntimeError as e:
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

    if dry_run:
        typer.echo("\n--- System Prompt ---")
        typer.echo(system_prompt)
        typer.echo("\n--- User Prompt (first 500 chars) ---")
        typer.echo(user_prompt[:500])
        typer.echo("\n[dry-run] No LLM call made.")
        typer.echo("Done. Processed: 0, Skipped: 1")
        return

    raw_response = None
    for attempt in range(2):
        try:
            raw_response = llm.complete(system_prompt, user_prompt, response_model=ReviewResult)

            if verbose:
                typer.echo("\n--- Raw LLM Response ---")
                typer.echo(raw_response)

            # The new complete() with response_model returns a dict directly
            if isinstance(raw_response, dict):
                parsed_json = raw_response
            else:
                # Fallback: strip markdown code fences some models add
                processed = str(raw_response).strip()
                if processed.startswith("```json"):
                    processed = processed[7:]
                elif processed.startswith("```"):
                    processed = processed[3:]
                if processed.endswith("```"):
                    processed = processed[:-3]
                processed = processed.strip()

                parsed_json = json.loads(processed)
                if "ReviewResult" in parsed_json:
                    parsed_json = parsed_json["ReviewResult"]

            result = ReviewResult.model_validate(parsed_json)

            if output == "json":
                typer.echo(result.model_dump_json(indent=2))
            else:
                display_review(result)

            typer.echo("Done. Processed: 1, Skipped: 0")

            if result.overall == "fail":
                raise typer.Exit(code=1)
            return

        except typer.Exit:
            raise
        except RuntimeError as e:
            typer.secho(f"Error: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            if attempt == 0:
                user_prompt += (
                    f"\n\nERROR FROM PREVIOUS ATTEMPT:\n{e}\n\n"
                    "Please ensure your response is a valid JSON object matching the required schema exactly."
                )
                continue
            typer.secho(f"Error parsing LLM response: {e}", fg=typer.colors.RED, err=True)
            if verbose:
                typer.echo(f"Raw response: {raw_response}")
            typer.echo("Done. Processed: 0, Skipped: 1")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
