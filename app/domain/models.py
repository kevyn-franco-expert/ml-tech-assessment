from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TranscriptAnalysis(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    summary: str
    next_actions: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LLMAnalysisDTO(BaseModel):
    summary: str
    action_items: list[str]