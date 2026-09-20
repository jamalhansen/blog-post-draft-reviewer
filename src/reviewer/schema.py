from typing import Literal

from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    category: str
    status: Literal["pass", "fail", "warn"]
    note: str = ""

class ReviewResult(BaseModel):
    overall: Literal["pass", "fail", "warn"]
    word_count: int
    post_type: str = Field(description="Inferred: 'manifesto', 'setup', 'concept', 'practical'")
    items: list[ChecklistItem]
    summary: str = Field(description="2-3 sentence plain-language verdict")
