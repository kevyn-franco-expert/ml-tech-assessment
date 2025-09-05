import logging
from datetime import datetime, timezone
from uuid import uuid4

import openai

from app.domain.errors import EmptyTranscriptError, TranscriptTooLargeError, LLMServiceError, LLMTimeoutError, LLMRateLimitError
from app.domain.models import TranscriptAnalysis, LLMAnalysisDTO
from app.domain.ports import LLm
from app.infra.memory_repository import MemoryRepository
from app.prompts import SYSTEM_PROMPT, RAW_USER_PROMPT

logger = logging.getLogger(__name__)

MAX_TRANSCRIPT_SIZE = 100 * 1024  # 100KB


class AnalyzeTranscriptUseCase:
    def __init__(self, llm_port: LLm, repository: MemoryRepository):
        self._llm_port = llm_port
        self._repository = repository

    async def execute(self, transcript: str) -> TranscriptAnalysis:
        correlation_id = str(uuid4())
        logger.info(f"Starting transcript analysis - correlation_id: {correlation_id}")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            self._validate_transcript(transcript)
            
            user_prompt = RAW_USER_PROMPT.format(transcript=transcript)
            
            try:
                if hasattr(self._llm_port, 'run_completion_async'):
                    llm_response = await self._llm_port.run_completion_async(
                        SYSTEM_PROMPT, user_prompt, LLMAnalysisDTO
                    )
                else:
                    llm_response = self._llm_port.run_completion(
                        SYSTEM_PROMPT, user_prompt, LLMAnalysisDTO
                    )
            except openai.RateLimitError as e:
                logger.error(f"OpenAI rate limit exceeded: {e}")
                raise LLMRateLimitError()
            except openai.APITimeoutError as e:
                logger.error(f"OpenAI request timed out: {e}")
                raise LLMTimeoutError()
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
                raise LLMServiceError(str(e))
            
            analysis = self._map_to_domain_model(llm_response, correlation_id)
            
            await self._repository.save(analysis)
            
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.info(f"Transcript analysis completed - correlation_id: {correlation_id}, duration: {duration}s")
            
            return analysis
            
        except Exception as e:
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Transcript analysis failed - correlation_id: {correlation_id}, duration: {duration}s, error: {str(e)}")
            raise

    def _validate_transcript(self, transcript: str) -> None:
        if not transcript or not transcript.strip():
            raise EmptyTranscriptError()
        
        if len(transcript.encode('utf-8')) > MAX_TRANSCRIPT_SIZE:
            raise TranscriptTooLargeError(
                len(transcript.encode('utf-8')), 
                MAX_TRANSCRIPT_SIZE
            )

    def _map_to_domain_model(self, llm_response: LLMAnalysisDTO, correlation_id: str) -> TranscriptAnalysis:
        from uuid import UUID
        return TranscriptAnalysis(
            id=UUID(correlation_id),
            summary=llm_response.summary,
            next_actions=llm_response.action_items,
            created_at=datetime.now(timezone.utc)
        )