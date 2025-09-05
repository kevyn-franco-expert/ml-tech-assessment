from functools import lru_cache

from app.configurations import EnvConfigs
from app.infra.memory_repository import MemoryRepository
from app.adapters.openai import OpenAIAdapter
from app.use_cases.analyze_batch import AnalyzeBatchUseCase
from app.use_cases.analyze_transcript import AnalyzeTranscriptUseCase
from app.use_cases.get_analysis import GetAnalysisUseCase


@lru_cache()
def get_config() -> EnvConfigs:
    return EnvConfigs()


@lru_cache()
def get_repository() -> MemoryRepository:
    return MemoryRepository()


@lru_cache()
def get_llm_adapter() -> OpenAIAdapter:
    config = get_config()
    return OpenAIAdapter(
        api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_MODEL
    )


def get_analyze_transcript_use_case() -> AnalyzeTranscriptUseCase:
    return AnalyzeTranscriptUseCase(
        llm_port=get_llm_adapter(),
        repository=get_repository()
    )


def get_get_analysis_use_case() -> GetAnalysisUseCase:
    return GetAnalysisUseCase(repository=get_repository())


def get_analyze_batch_use_case() -> AnalyzeBatchUseCase:
    return AnalyzeBatchUseCase(
        llm_port=get_llm_adapter(),
        repository=get_repository()
    )