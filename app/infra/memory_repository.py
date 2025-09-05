import asyncio
from typing import Dict, Optional
from uuid import UUID

from app.domain.models import TranscriptAnalysis


class MemoryRepository:
    def __init__(self):
        self._storage: Dict[UUID, TranscriptAnalysis] = {}
        self._lock = asyncio.Lock()

    async def save(self, analysis: TranscriptAnalysis) -> None:
        async with self._lock:
            self._storage[analysis.id] = analysis

    async def get_by_id(self, analysis_id: UUID) -> Optional[TranscriptAnalysis]:
        async with self._lock:
            return self._storage.get(analysis_id)

    async def get_all(self) -> list[TranscriptAnalysis]:
        async with self._lock:
            return list(self._storage.values())

    async def count(self) -> int:
        async with self._lock:
            return len(self._storage)