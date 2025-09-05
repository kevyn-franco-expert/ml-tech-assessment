import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from datetime import datetime, timezone

from app.domain.errors import EmptyTranscriptError, TranscriptTooLargeError, AnalysisNotFoundError
from app.domain.models import TranscriptAnalysis, LLMAnalysisDTO
from app.infra.memory_repository import MemoryRepository
from app.use_cases.analyze_transcript import AnalyzeTranscriptUseCase
from app.use_cases.get_analysis import GetAnalysisUseCase
from app.use_cases.analyze_batch import AnalyzeBatchUseCase


class MockLLMPort:
    def __init__(self, response: LLMAnalysisDTO = None):
        self.response = response or LLMAnalysisDTO(
            summary="Test summary",
            action_items=["Action 1", "Action 2"]
        )
        self.run_completion = Mock(return_value=self.response)
        self.run_completion_async = AsyncMock(return_value=self.response)


@pytest.fixture
def mock_llm_port():
    return MockLLMPort()


@pytest.fixture
def repository():
    return MemoryRepository()


@pytest.fixture
def analyze_use_case(mock_llm_port, repository):
    return AnalyzeTranscriptUseCase(mock_llm_port, repository)


@pytest.fixture
def get_use_case(repository):
    return GetAnalysisUseCase(repository)


@pytest.fixture
def batch_use_case(mock_llm_port, repository):
    return AnalyzeBatchUseCase(mock_llm_port, repository)


class TestAnalyzeTranscriptUseCase:
    @pytest.mark.asyncio
    async def test_successful_analysis(self, analyze_use_case, repository):
        transcript = "This is a test transcript with meaningful content."
        
        result = await analyze_use_case.execute(transcript)
        
        assert result.summary == "Test summary"
        assert result.next_actions == ["Action 1", "Action 2"]
        assert result.id is not None
        assert result.created_at is not None
        
        # Verify it was saved to repository
        saved_analysis = await repository.get_by_id(result.id)
        assert saved_analysis is not None
        assert saved_analysis.id == result.id

    @pytest.mark.asyncio
    async def test_empty_transcript_error(self, analyze_use_case):
        with pytest.raises(EmptyTranscriptError):
            await analyze_use_case.execute("")
        
        with pytest.raises(EmptyTranscriptError):
            await analyze_use_case.execute("   ")

    @pytest.mark.asyncio
    async def test_transcript_too_large_error(self, analyze_use_case):
        large_transcript = "x" * (100 * 1024 + 1)  # 100KB + 1 byte
        
        with pytest.raises(TranscriptTooLargeError) as exc_info:
            await analyze_use_case.execute(large_transcript)
        
        assert exc_info.value.size > 100 * 1024
        assert exc_info.value.max_size == 100 * 1024

    @pytest.mark.asyncio
    async def test_llm_port_called_correctly(self, analyze_use_case, mock_llm_port):
        transcript = "Test transcript"
        
        await analyze_use_case.execute(transcript)
        
        mock_llm_port.run_completion_async.assert_called_once()
        call_args = mock_llm_port.run_completion_async.call_args
        assert "Test transcript" in call_args[0][1]  # user_prompt contains transcript


class TestGetAnalysisUseCase:
    @pytest.mark.asyncio
    async def test_successful_retrieval(self, get_use_case, repository):
        # Create and save an analysis
        analysis = TranscriptAnalysis(
            id=uuid4(),
            summary="Test summary",
            next_actions=["Action 1"],
            created_at=datetime.now(timezone.utc)
        )
        await repository.save(analysis)
        
        result = await get_use_case.execute(analysis.id)
        
        assert result.id == analysis.id
        assert result.summary == analysis.summary
        assert result.next_actions == analysis.next_actions

    @pytest.mark.asyncio
    async def test_analysis_not_found(self, get_use_case):
        non_existent_id = uuid4()
        
        with pytest.raises(AnalysisNotFoundError) as exc_info:
            await get_use_case.execute(non_existent_id)
        
        assert str(non_existent_id) in str(exc_info.value)


class TestAnalyzeBatchUseCase:
    @pytest.mark.asyncio
    async def test_successful_batch_analysis(self, batch_use_case):
        transcripts = [
            "First transcript",
            "Second transcript",
            "Third transcript"
        ]
        
        results = await batch_use_case.execute(transcripts)
        
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result.success is True
            assert result.transcript == transcripts[i]
            assert result.analysis is not None
            assert result.error is None

    @pytest.mark.asyncio
    async def test_mixed_success_failure_batch(self, mock_llm_port, repository):
        # Mock LLM to fail on empty transcripts
        def mock_run_completion_async(system_prompt, user_prompt, dto):
            if "Empty transcript" in user_prompt:
                raise Exception("Empty transcript error")
            return LLMAnalysisDTO(summary="Test", action_items=["Action"])
        
        mock_llm_port.run_completion_async.side_effect = mock_run_completion_async
        
        batch_use_case = AnalyzeBatchUseCase(mock_llm_port, repository)
        transcripts = [
            "Valid transcript",
            "",  # This will cause validation error
            "Another valid transcript"
        ]
        
        results = await batch_use_case.execute(transcripts)
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[2].success is True

    @pytest.mark.asyncio
    async def test_empty_batch(self, batch_use_case):
        results = await batch_use_case.execute([])
        assert len(results) == 0


class TestMemoryRepository:
    @pytest.mark.asyncio
    async def test_save_and_retrieve(self):
        repository = MemoryRepository()
        analysis = TranscriptAnalysis(
            id=uuid4(),
            summary="Test",
            next_actions=["Action"],
            created_at=datetime.now(timezone.utc)
        )
        
        await repository.save(analysis)
        retrieved = await repository.get_by_id(analysis.id)
        
        assert retrieved is not None
        assert retrieved.id == analysis.id
        assert retrieved.summary == analysis.summary

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        repository = MemoryRepository()
        result = await repository.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_count(self):
        repository = MemoryRepository()
        assert await repository.count() == 0
        
        analysis = TranscriptAnalysis(
            id=uuid4(),
            summary="Test",
            next_actions=["Action"],
            created_at=datetime.now(timezone.utc)
        )
        await repository.save(analysis)
        
        assert await repository.count() == 1