class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class OllamaError(AppException):
    """Base exception for Ollama-related errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama fails."""
    pass


class OllamaTimeoutError(OllamaError):
    """Raised when Ollama request times out."""
    pass


class DatabaseError(AppException):
    """Raised when database operations fail."""
    pass


class ValidationError(AppException):
    """Raised when validation fails."""
    pass


class InsufficientEvidenceError(AppException):
    """Raised when RAG retrieval has insufficient evidence."""
    pass
