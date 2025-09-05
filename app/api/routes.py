import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.schemas import TranscriptAnalysisResponse, BatchAnalysisRequest, BatchAnalysisResponse, BatchAnalysisItemResponse
from app.domain.errors import EmptyTranscriptError, TranscriptTooLargeError, AnalysisNotFoundError, LLMRateLimitError, LLMTimeoutError, LLMServiceError
from app.infra.di import get_analyze_transcript_use_case, get_get_analysis_use_case, get_analyze_batch_use_case
from app.use_cases.analyze_transcript import AnalyzeTranscriptUseCase
from app.use_cases.get_analysis import GetAnalysisUseCase
from app.use_cases.analyze_batch import AnalyzeBatchUseCase

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/analyze", response_model=TranscriptAnalysisResponse)
async def analyze_transcript(
    transcript: str = Query(..., min_length=1, description="The plain text transcript to analyze"),
    use_case: AnalyzeTranscriptUseCase = Depends(get_analyze_transcript_use_case)
):
    """
    Analyze a single transcript and return summary with next actions.
    
    - **transcript**: The plain text transcript to analyze
    
    Returns a TranscriptAnalysis with:
    - **id**: Unique identifier for the analysis
    - **summary**: Brief summary of the transcript
    - **next_actions**: List of recommended actions
    - **created_at**: Timestamp when analysis was created
    """
    try:
        analysis = await use_case.execute(transcript)
        return TranscriptAnalysisResponse(
            id=analysis.id,
            summary=analysis.summary,
            next_actions=analysis.next_actions,
            created_at=analysis.created_at
        )
    except EmptyTranscriptError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except TranscriptTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except LLMRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except LLMServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in analyze_transcript: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analyses/{analysis_id}", response_model=TranscriptAnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    use_case: GetAnalysisUseCase = Depends(get_get_analysis_use_case)
):
    """
    Retrieve a previously stored analysis by its ID.
    
    - **analysis_id**: The UUID of the analysis to retrieve
    
    Returns the stored TranscriptAnalysis or 404 if not found.
    """
    try:
        analysis = await use_case.execute(analysis_id)
        return TranscriptAnalysisResponse(
            id=analysis.id,
            summary=analysis.summary,
            next_actions=analysis.next_actions,
            created_at=analysis.created_at
        )
    except AnalysisNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in get_analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyses/batch", response_model=BatchAnalysisResponse)
async def analyze_batch(
    request: BatchAnalysisRequest,
    use_case: AnalyzeBatchUseCase = Depends(get_analyze_batch_use_case)
):
    """
    Analyze multiple transcripts concurrently.
    
    - **transcripts**: List of transcript texts to analyze
    
    Returns a BatchAnalysisResponse with:
    - **results**: List of individual analysis results
    - **total_count**: Total number of transcripts processed
    - **successful_count**: Number of successful analyses
    
    Each result contains either a successful analysis or an error message.
    """
    try:
        results = await use_case.execute(request.transcripts)
        
        response_results = []
        for result in results:
            if result.success:
                response_results.append(BatchAnalysisItemResponse(
                    transcript=result.transcript,
                    success=True,
                    analysis=TranscriptAnalysisResponse(
                        id=result.analysis.id,
                        summary=result.analysis.summary,
                        next_actions=result.analysis.next_actions,
                        created_at=result.analysis.created_at
                    )
                ))
            else:
                response_results.append(BatchAnalysisItemResponse(
                    transcript=result.transcript,
                    success=False,
                    error=result.error
                ))
        
        successful_count = sum(1 for r in results if r.success)
        
        return BatchAnalysisResponse(
            results=response_results,
            total_count=len(results),
            successful_count=successful_count
        )
    except Exception as e:
        logger.error(f"Unexpected error in analyze_batch: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")