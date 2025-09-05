import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.domain.models import TranscriptAnalysis, LLMAnalysisDTO
from app.domain.errors import (
    EmptyTranscriptError,
    TranscriptTooLargeError,
    AnalysisNotFoundError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMServiceError
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_analyze_use_case():
    mock = AsyncMock()
    mock.execute.return_value = TranscriptAnalysis(
        id=uuid4(),
        summary="Test summary from mock",
        next_actions=["Mock action 1", "Mock action 2"],
        created_at=datetime.now(timezone.utc)
    )
    return mock


@pytest.fixture
def mock_get_use_case():
    mock = AsyncMock()
    analysis_id = uuid4()
    mock.execute.return_value = TranscriptAnalysis(
        id=analysis_id,
        summary="Retrieved summary",
        next_actions=["Retrieved action"],
        created_at=datetime.now(timezone.utc)
    )
    return mock


@pytest.fixture
def mock_batch_use_case():
    from app.use_cases.analyze_batch import BatchAnalysisResult
    
    mock = AsyncMock()
    
    def create_mock_results(transcripts):
        results = []
        for transcript in transcripts:
            if transcript.strip():  # Success case
                analysis = TranscriptAnalysis(
                    id=uuid4(),
                    summary=f"Summary for: {transcript[:20]}...",
                    next_actions=[f"Action for {transcript[:10]}"],
                    created_at=datetime.now(timezone.utc)
                )
                results.append(BatchAnalysisResult(transcript=transcript, analysis=analysis))
            else:  # Error case
                results.append(BatchAnalysisResult(transcript=transcript, error="Empty transcript"))
        return results
    
    mock.execute.side_effect = create_mock_results
    return mock


class TestAnalyzeEndpoint:
    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_successful_analysis(self, mock_get_use_case, client, mock_analyze_use_case):
        mock_get_use_case.return_value = mock_analyze_use_case
        
        response = client.get("/api/v1/analyze?transcript=This is a test transcript")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["summary"] == "Test summary from mock"
        assert data["next_actions"] == ["Mock action 1", "Mock action 2"]
        assert "created_at" in data

    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_empty_transcript_error(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = EmptyTranscriptError()
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get("/api/v1/analyze?transcript=")
        
        assert response.status_code == 422
        assert "empty" in response.json()["detail"].lower()

    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_transcript_too_large_error(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = TranscriptTooLargeError(100001, 100000)
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get("/api/v1/analyze?transcript=large_transcript")
        
        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]

    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_rate_limit_error(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = LLMRateLimitError()
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get("/api/v1/analyze?transcript=test")
        
        assert response.status_code == 429

    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_timeout_error(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = LLMTimeoutError()
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get("/api/v1/analyze?transcript=test")
        
        assert response.status_code == 504

    @patch('app.infra.di.get_analyze_transcript_use_case')
    def test_service_error(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        mock_use_case.execute.side_effect = LLMServiceError("Service unavailable")
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get("/api/v1/analyze?transcript=test")
        
        assert response.status_code == 502


class TestGetAnalysisEndpoint:
    @patch('app.infra.di.get_get_analysis_use_case')
    def test_successful_retrieval(self, mock_get_use_case_dep, client, mock_get_use_case):
        mock_get_use_case_dep.return_value = mock_get_use_case
        analysis_id = str(uuid4())
        
        response = client.get(f"/api/v1/analyses/{analysis_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["summary"] == "Retrieved summary"
        assert data["next_actions"] == ["Retrieved action"]

    @patch('app.infra.di.get_get_analysis_use_case')
    def test_analysis_not_found(self, mock_get_use_case, client):
        mock_use_case = AsyncMock()
        analysis_id = str(uuid4())
        mock_use_case.execute.side_effect = AnalysisNotFoundError(analysis_id)
        mock_get_use_case.return_value = mock_use_case
        
        response = client.get(f"/api/v1/analyses/{analysis_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_invalid_uuid(self, client):
        response = client.get("/api/v1/analyses/invalid-uuid")
        
        assert response.status_code == 422


class TestBatchAnalysisEndpoint:
    @patch('app.infra.di.get_analyze_batch_use_case')
    def test_successful_batch_analysis(self, mock_get_use_case, client, mock_batch_use_case):
        mock_get_use_case.return_value = mock_batch_use_case
        
        request_data = {
            "transcripts": [
                "First transcript",
                "Second transcript"
            ]
        }
        
        response = client.post("/api/v1/analyses/batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert data["successful_count"] == 2
        assert len(data["results"]) == 2
        
        for result in data["results"]:
            assert result["success"] is True
            assert result["analysis"] is not None
            assert result["error"] is None

    @patch('app.infra.di.get_analyze_batch_use_case')
    def test_mixed_success_failure_batch(self, mock_get_use_case, client, mock_batch_use_case):
        mock_get_use_case.return_value = mock_batch_use_case
        
        request_data = {
            "transcripts": [
                "Valid transcript",
                "",  # Empty transcript
                "Another valid transcript"
            ]
        }
        
        response = client.post("/api/v1/analyses/batch", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
        assert data["successful_count"] == 2
        
        # Check individual results
        results = data["results"]
        assert results[0]["success"] is True
        assert results[1]["success"] is False
        assert results[1]["error"] == "Empty transcript"
        assert results[2]["success"] is True

    def test_empty_transcripts_list(self, client):
        request_data = {"transcripts": []}
        
        response = client.post("/api/v1/analyses/batch", json=request_data)
        
        assert response.status_code == 422

    def test_too_many_transcripts(self, client):
        request_data = {
            "transcripts": [f"Transcript {i}" for i in range(11)]  # Max is 10
        }
        
        response = client.post("/api/v1/analyses/batch", json=request_data)
        
        assert response.status_code == 422


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "transcript-analysis-api"


@pytest.mark.asyncio
async def test_async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200