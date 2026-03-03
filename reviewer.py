import click
import json
import sys
import frontmatter
from providers import PROVIDERS
from rubric import load_rubric
from schema import ReviewResult
from prompts import build_system_prompt, build_user_prompt
from display import display_review


@click.command()
@click.option("--file", "-f", required=True, type=click.Path(exists=True), help="Path to the blog post markdown file.")
@click.option("--provider", "-p", default="ollama", type=click.Choice(list(PROVIDERS.keys())), help="LLM provider.")
@click.option("--model", "-m", default=None, help="Model name override (uses provider default if omitted).")
@click.option("--output", "-o", default="text", type=click.Choice(["text", "json"]), help="Output format.")
@click.option("--dry-run", "-n", is_flag=True, help="Build prompts and show config without calling the LLM.")
@click.option("--verbose", "-v", is_flag=True, help="Print extra debug output.")
def main(file, provider, model, output, dry_run, verbose):
    """Review a blog post draft against a rubric."""

    # --- Fail fast ---
    rubric = load_rubric()
    if rubric == "Rubric not found.":
        click.secho("Error: checklist.md not found in the current directory.", fg="red", err=True)
        sys.exit(1)

    try:
        llm = PROVIDERS[provider](model=model)
    except RuntimeError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    with open(file) as f:
        post_data = frontmatter.load(f)
        content = post_data.content

    if verbose:
        click.echo(f"Provider : {provider}")
        click.echo(f"Model    : {llm.model}")
        click.echo(f"File     : {file}")
        click.echo(f"Output   : {output}")

    system_prompt = build_system_prompt(rubric)
    user_prompt = build_user_prompt(content)

    if dry_run:
        click.echo("\n--- System Prompt ---")
        click.echo(system_prompt)
        click.echo("\n--- User Prompt (first 500 chars) ---")
        click.echo(user_prompt[:500])
        click.echo("\n[dry-run] No LLM call made.")
        click.echo("Done. Processed: 0, Skipped: 1")
        return

    # Determine response_format for providers that support JSON mode
    response_format = None
    if provider == "ollama":
        response_format = ReviewResult.model_json_schema()
    elif provider in ("groq", "deepseek", "gemini"):
        response_format = {"type": "json_object"}

    raw_response = None
    for attempt in range(2):
        try:
            raw_response = llm.complete(system_prompt, user_prompt, response_format=response_format)

            if verbose:
                click.echo("\n--- Raw LLM Response ---")
                click.echo(raw_response)

            # Strip markdown code fences some models add
            processed = raw_response.strip()
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
                click.echo(result.model_dump_json(indent=2))
            else:
                display_review(result)

            click.echo("Done. Processed: 1, Skipped: 0")

            if result.overall == "fail":
                sys.exit(1)
            return

        except RuntimeError as e:
            click.secho(f"Error: {e}", fg="red", err=True)
            sys.exit(1)
        except Exception as e:
            if attempt == 0:
                user_prompt += (
                    f"\n\nERROR FROM PREVIOUS ATTEMPT:\n{e}\n\n"
                    "Please ensure your response is a valid JSON object matching the required schema exactly."
                )
                continue
            click.secho(f"Error parsing LLM response: {e}", fg="red", err=True)
            if verbose:
                click.echo(f"Raw response: {raw_response}")
            click.echo("Done. Processed: 0, Skipped: 1")
            sys.exit(1)


if __name__ == "__main__":
    main()
