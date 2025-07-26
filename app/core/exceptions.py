from typing import Any, Dict, Optional

from fastapi import HTTPException


class LearnerGraphException(Exception):
    """Base exception class for the Learner Graph system."""

    pass


class RecommendationEngineException(LearnerGraphException):
    """Exception raised by the recommendation engine."""

    pass


class MasteryTrackingException(LearnerGraphException):
    """Exception raised during mastery tracking operations."""

    pass


class StreakEngineException(LearnerGraphException):
    """Exception raised by the streak engine."""

    pass


class ABTestException(LearnerGraphException):
    """Exception raised during A/B testing operations."""

    pass


class ValidationException(LearnerGraphException):
    """Exception raised during data validation."""

    pass


def create_http_exception(
    status_code: int, detail: str, headers: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create a standardized HTTP exception."""
    return HTTPException(status_code=status_code, detail=detail, headers=headers)


# Common HTTP exceptions
class NotFoundException(HTTPException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class BadRequestException(HTTPException):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)


class TooManyRequestsException(HTTPException):
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(status_code=429, detail=detail)
