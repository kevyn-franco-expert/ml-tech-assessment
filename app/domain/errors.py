class DomainError(Exception):
    pass


class TranscriptTooLargeError(DomainError):
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(f"Transcript size {size} exceeds maximum allowed size {max_size}")


class EmptyTranscriptError(DomainError):
    def __init__(self):
        super().__init__("Transcript must not be empty")


class AnalysisNotFoundError(DomainError):
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        super().__init__(f"Analysis with id {analysis_id} not found")


class LLMServiceError(DomainError):
    def __init__(self, message: str):
        super().__init__(f"LLM service error: {message}")


class LLMTimeoutError(DomainError):
    def __init__(self):
        super().__init__("LLM service request timed out")


class LLMRateLimitError(DomainError):
    def __init__(self):
        super().__init__("LLM service rate limit exceeded")