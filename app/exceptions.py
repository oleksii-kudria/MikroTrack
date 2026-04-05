from __future__ import annotations


class MikroTrackError(Exception):
    def __init__(
        self,
        error_code: str,
        message: str,
        recommendation: str,
        original_exception: Exception | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.recommendation = recommendation
        self.original_exception = original_exception
        super().__init__(message)
