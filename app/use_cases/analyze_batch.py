import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Union

from app.domain.models import TranscriptAnalysis
from app.domain.ports import LLm
from app.infra.memory_repository import MemoryRepository
from app.use_cases.analyze_transcript import AnalyzeTranscriptUseCase

logger = logging.getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 5


class BatchAnalysisResult:
    def __init__(self, transcript: str, analysis: TranscriptAnalysis = None, error: str = None):
        self.transcript = transcript
        self.analysis = analysis
        self.error = error
        self.success = analysis is not None


class AnalyzeBatchUseCase:
    def __init__(self, llm_port: LLm, repository: MemoryRepository):
        self._llm_port = llm_port
        self._repository = repository
        self._analyze_use_case = AnalyzeTranscriptUseCase(llm_port, repository)

    async def execute(self, transcripts: List[str]) -> List[BatchAnalysisResult]:
        logger.info(f"Starting batch analysis for {len(transcripts)} transcripts")
        start_time = datetime.now(timezone.utc)
        
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
        async def analyze_single(transcript: str) -> BatchAnalysisResult:
            async with semaphore:
                try:
                    analysis = await self._analyze_use_case.execute(transcript)
                    return BatchAnalysisResult(transcript=transcript, analysis=analysis)
                except Exception as e:
                    logger.error(f"Failed to analyze transcript: {str(e)}")
                    return BatchAnalysisResult(transcript=transcript, error=str(e))
        
        tasks = [analyze_single(transcript) for transcript in transcripts]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        successful_count = sum(1 for result in results if result.success)
        
        logger.info(
            f"Batch analysis completed - total: {len(transcripts)}, "
            f"successful: {successful_count}, duration: {duration}s"
        )
        
        return results