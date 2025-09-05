from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TranscriptAnalysisResponse(BaseModel):
    id: UUID
    summary: str
    next_actions: List[str]
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchAnalysisRequest(BaseModel):
    transcripts: List[str] = Field(..., min_items=1, max_items=10)


class BatchAnalysisItemResponse(BaseModel):
    transcript: str
    success: bool
    analysis: Optional[TranscriptAnalysisResponse] = None
    error: Optional[str] = None


class BatchAnalysisResponse(BaseModel):
    results: List[BatchAnalysisItemResponse]
    total_count: int
    successful_count: int


class ErrorResponse(BaseModel):
    detail: str
    error_type: Optional[str] = None