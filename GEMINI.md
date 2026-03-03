Blog Draft Reviewer
This is a Python CLI tool that reviews blog post drafts against a fixed rubric and returns structured feedback. It is Tool #1 in the local-ai-tools series built alongside the Local-First AI: Small Models, Sharp Tools blog series.

What This Tool Does
Takes a blog post draft (markdown file) and the Blog Post Writing Checklist rubric, runs them through a local LLM, and returns structured feedback per rubric category. Output is JSON -- machine-readable, but also readable as plain text if you print it nicely.
Examples of what it flags:

"Opening lacks a hook in the first 2-3 sentences."
"Tone shifts toward preachy in paragraph 4."
"No call-to-action found at the end."
"Code examples present but no output shown."
"Word count 1847 -- over the deep dive threshold. Consider trimming."

This is a rubric checker, not a rewriter. It identifies problems and explains them. It does not fix them.

How to Run It
bashpython reviewer.py --post path/to/draft.md
python reviewer.py --post path/to/draft.md --backend anthropic # swap to Haiku
python reviewer.py --post path/to/draft.md --output json # raw JSON
python reviewer.py --post path/to/draft.md --output text # human-readable (default)

Tech Stack

Python 3.11+
use uv rather than pip
Ollama (local inference, default backend) -- model: phi4-mini or llama3.2
Anthropic Python SDK (optional backend -- Haiku or Sonnet)
Pydantic -- output schema validation
Rich -- pretty terminal output (human-readable mode)
python-frontmatter -- parse markdown + YAML frontmatter

No LangChain. No LlamaIndex. Just direct API calls through the ModelClient wrapper.

Project Structure
blog-draft-reviewer/
├── GEMINI.md # this file
├── README.md
├── reviewer.py # CLI entry point
├── client.py # ModelClient abstraction
├── rubric.py # loads and structures the checklist
├── schema.py # Pydantic output models
├── prompts.py # system prompt and user prompt builders
├── display.py # Rich terminal formatting
├── checklist.md # the rubric (copied from vault)
├── requirements.txt
└── examples/
└── sample-draft.md # a test draft to run against

Design Decisions
Single-shot, not agentic
One LLM call. System prompt contains the full rubric. User prompt is the draft. Response is structured JSON. No tool calls, no loops, no follow-up prompts. This is intentional -- the rubric is fixed, so a single well-structured call is sufficient and predictable.
If the model can't fit the full draft in context, chunk it and aggregate results. But try single-shot first.
ModelClient abstraction (build this first)
Every LLM call goes through client.py, not directly to Ollama or Anthropic. The interface is:
pythonclass ModelClient:
def **init**(self, backend: str = "ollama", model: str = None):
...

    def complete(self, system: str, user: str) -> str:
        ...

Backend is set via --backend flag or MODEL_BACKEND env var. Valid values: ollama, anthropic. Default: ollama.
This abstraction exists so every other tool in the local-ai-tools series can reuse the same pattern. Build it right here, in the first tool.
Structured output via Pydantic
The LLM is prompted to return JSON matching this schema. Validate with Pydantic. If validation fails, retry once with an error message appended to the prompt.
pythonclass ChecklistItem(BaseModel):
category: str
status: Literal["pass", "fail", "warn"]
note: str # specific, actionable -- not generic

class ReviewResult(BaseModel):
overall: Literal["pass", "fail", "warn"]
word_count: int
post_type: str # inferred: "manifesto", "setup", "concept", "practical"
items: list[ChecklistItem]
summary: str # 2-3 sentence plain-language verdict
Rubric categories
The system prompt organizes checks into these categories, drawn directly from the Blog Post Writing Checklist:
Hook & Opening

Strong hook in first 2-3 sentences
Clear thesis statement early

Tone

Helpful, not preachy
Pragmatic, not dogmatic
Personal experience, not abstract theory
Conversational -- "explaining to a dev friend over coffee"

Structure

At least one concrete example or story
Appropriate length for post type (standard: 800-1500w, setup: 500-800w, deep dive: 1500-2000w)
Preview of what's coming next (if series post)
Clear call-to-action at the end

Code

Code examples present if the topic warrants them
Output/results shown alongside code

Non-negotiables (always fail if violated, no warn)

Code blocks present but clearly broken syntax
No CTA of any kind

System prompt strategy
Keep the system prompt focused. Include the full rubric as a structured list. Tell the model:

What it is (a technical blog post reviewer)
What the author's style goal is (conversational, Python analogies, no em dashes, not preachy)
That feedback must be specific -- quote the offending sentence or paragraph when flagging a failure
That it must return only valid JSON matching the schema, no preamble

Do not include examples of good vs. bad writing in the system prompt -- it adds tokens and the rubric is specific enough.
Rubric file is external, not hardcoded
checklist.md lives in the project root and is loaded at runtime. This means the rubric can be updated without touching Python code. The rubric.py module parses the markdown into a structured list that gets injected into the system prompt.
No streaming
Wait for the full response, validate, display. Streaming adds complexity for no user benefit in a CLI tool that runs in under 10 seconds.

What "Done" Looks Like
Running python reviewer.py --post examples/sample-draft.md should:

Print a clean summary with overall verdict (pass/warn/fail)
List each checklist item with its status and a specific note
Print word count and inferred post type
Return exit code 0 on pass, 1 on fail

JSON mode should return the raw Pydantic model as pretty-printed JSON.
Swapping --backend anthropic should produce the same output structure, possibly with different notes. That difference is intentional -- it's the start of the comparison story for Post 10 of the series.

What This Tool Is Not

Not a rewriter. It identifies problems, it does not fix them.
Not a grammar checker. Use a linter for that.
Not a brand voice scorer (that's Tool #16). This tool checks structure and rubric compliance. Brand voice is a separate concern.
Not an agentic loop. One call, one result.

Context: Where This Fits
This is Tool #1 in the local-ai-tools series. The toolkit grows across the Local-First AI: Small Models, Sharp Tools blog series (launching Dec 2026). Each tool adds a module; readers who follow the whole series end up with a working toolkit.
The ModelClient abstraction built here is reused by every subsequent tool. Get it right.
Related tools in the series:

Tool #16 (Brand Voice Scorer) -- separate tool, checks tone/style against brand guidelines
Tool #11 (Model Router) -- will import ModelClient from this project
Tool #22 (Model Comparison Harness) -- uses ModelClient to run same prompt across backends

Series post: Tool #1 maps to Post 7 (The Summarizer in Your Pocket) or appears as a component in Post 8 (Pipelines and Routing). Exact placement TBD when writing begins.

Notes for Vibe Coding

Build client.py and schema.py first. Everything depends on them.
Use phi4-mini as the default local model. It's fast and handles constrained evaluation well.
The first test draft to run against: write a deliberately flawed post (missing hook, no CTA, preachy tone) and verify the tool catches it.
Keep the CLI surface simple. Two flags matter: --post and --backend. Everything else is optional.
If you hit a context length issue with a long draft, truncate to the first 3000 words for now and log a warning. Handle chunking later.
