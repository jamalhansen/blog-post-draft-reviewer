import click
import json
import frontmatter
import sys
from client import ModelClient
from rubric import load_rubric
from schema import ReviewResult
from prompts import build_system_prompt, build_user_prompt
from display import display_review

@click.command()
@click.option('--post', required=True, type=click.Path(exists=True), help='Path to the blog post markdown file.')
@click.option('--backend', default='ollama', type=click.Choice(['ollama', 'anthropic', 'gemini', 'groq', 'deepseek']), help='LLM backend.')
@click.option('--model', help='Model name (optional).')
@click.option('--output', default='text', type=click.Choice(['text', 'json']), help='Output format.')
def main(post, backend, model, output):
    """Review a blog post draft against a rubric."""
    
    # Load the post content
    with open(post, 'r') as f:
        post_data = frontmatter.load(f)
        content = post_data.content

    # Load the rubric
    rubric = load_rubric()
    
    # Initialize the client
    client = ModelClient(backend=backend, model=model)
    
    # Build prompts
    system_prompt = build_system_prompt(rubric)
    user_prompt = build_user_prompt(content)
    
    # Call the LLM with retry logic
    # Ollama, Groq, DeepSeek, and Gemini support some form of JSON response format parameter
    response_format = None
    if backend == "ollama":
        response_format = ReviewResult.model_json_schema()
    elif backend in ["groq", "deepseek", "gemini"]:
        response_format = {"type": "json_object"}
    
    raw_response = None
    
    for attempt in range(2):
        try:
            raw_response = client.complete(system_prompt, user_prompt, response_format=response_format)
            
            # Some models might wrap JSON in code blocks
            processed_response = raw_response.strip()
            if processed_response.startswith("```json"):
                processed_response = processed_response[7:]
            elif processed_response.startswith("```"):
                processed_response = processed_response[3:]
            
            if processed_response.endswith("```"):
                processed_response = processed_response[:-3]
            
            processed_response = processed_response.strip()
            
            # Parse and validate response
            parsed_json = json.loads(processed_response)
            if "ReviewResult" in parsed_json:
                parsed_json = parsed_json["ReviewResult"]
            
            result = ReviewResult.model_validate(parsed_json)
            
            # Display the result
            if output == 'json':
                click.echo(result.model_dump_json(indent=2))
            else:
                display_review(result)
                
            # Exit codes
            if result.overall == "fail":
                sys.exit(1)
            
            return # Success!
            
        except Exception as e:
            if attempt == 0:
                # click.echo(f"Validation failed (attempt 1): {e}. Retrying...", err=True)
                user_prompt += f"\n\nERROR FROM PREVIOUS ATTEMPT:\n{e}\n\nPlease ensure your response is a valid JSON object matching the required schema exactly."
                continue
            else:
                click.secho(f"Error parsing LLM response: {e}", fg='red')
                click.echo(f"Raw Response: {raw_response}")
                sys.exit(1)

if __name__ == '__main__':
    main()
