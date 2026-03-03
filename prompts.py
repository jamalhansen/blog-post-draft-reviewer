import json
from schema import ReviewResult

def build_system_prompt(rubric_content: str) -> str:
    return f"""You are an expert technical blog post reviewer. Your goal is to review a blog post draft against a specific rubric and provide structured, actionable feedback.

AUTHOR'S STYLE GOALS:
- Conversational ("explaining to a dev friend over coffee")
- Python analogies (if applicable)
- No em dashes
- Helpful, not preachy
- Specific and actionable feedback (quote the offending sentence/paragraph when flagging failure)

RUBRIC:
{rubric_content}

OUTPUT REQUIREMENTS:
- Return ONLY a valid JSON object matching the ReviewResult schema.
- For EVERY category mentioned in the rubric above, you MUST include a corresponding item in the "items" list.
- DO NOT summarize the rubric; evaluate each point individually.
- The "summary" field must provide a 2-3 sentence plain-language verdict.
- DO NOT wrap the response in a top-level key like "ReviewResult".
- No preamble, no conversational filler.
- Be specific but concise.

EXAMPLE JSON STRUCTURE:
{{
  "overall": "fail",
  "word_count": 1200,
  "post_type": "practical",
  "items": [
    {{
      "category": "Hook & Opening",
      "status": "fail",
      "note": "Opening lacks a hook. Quote: 'Rust is a programming language...'"
    }},
    {{
      "category": "Tone",
      "status": "pass",
      "note": "Helpful and conversational throughout."
    }}
  ],
  "summary": "Overall the post covers the technical aspects well but needs a stronger opening hook to engage readers."
}}
"""

def build_user_prompt(post_content: str) -> str:
    return f"""Please review the following blog post draft:

{post_content}
"""
