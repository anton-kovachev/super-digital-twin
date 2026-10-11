from typing import Optional
from pydantic import BaseModel, Field


class ModerationResult(BaseModel):
    """Result of content moderation check"""

    is_safe: bool = Field(description="Whether the content is safe to process")
    reason: Optional[str] = Field(description="Reason if content is flagged as unsafe")
    category: Optional[str] = Field(description="Category of the issue if unsafe")
