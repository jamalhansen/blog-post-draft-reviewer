"""Domain logic and errors for blog-post-draft-reviewer."""

from .schema import ReviewResult


class BlogPostReviewerError(Exception):
    """Base error for strict blog-post reviewer operations."""


class ProviderResolutionError(BlogPostReviewerError):
    """Raised when provider/model resolution fails."""


class ReviewExecutionError(BlogPostReviewerError):
    """Raised when the review call or parsing fails."""


def review_post(
    llm, system_prompt: str, user_prompt: str, verbose: bool = False
) -> ReviewResult:
    """Core logic to call LLM and parse the review result."""
    result = llm.complete(system_prompt, user_prompt, response_model=ReviewResult)
    return ReviewResult.model_validate(result)
