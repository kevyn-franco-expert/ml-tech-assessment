import logging
from uuid import UUID

from app.domain.errors import AnalysisNotFoundError
from app.domain.models import TranscriptAnalysis
from app.infra.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)


class GetAnalysisUseCase:
    def __init__(self, repository: MemoryRepository):
        self._repository = repository

    async def execute(self, analysis_id: UUID) -> TranscriptAnalysis:
        logger.info(f"Retrieving analysis - id: {analysis_id}")
        
        analysis = await self._repository.get_by_id(analysis_id)
        
        if analysis is None:
            logger.warning(f"Analysis not found - id: {analysis_id}")
            raise AnalysisNotFoundError(str(analysis_id))
        
        logger.info(f"Analysis retrieved successfully - id: {analysis_id}")
        return analysis