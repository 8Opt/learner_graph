from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .base import BaseSchema, TimestampSchema


class LearningSessionCreate(BaseSchema):
    """Schema for creating a learning session."""

    user_id: int
    question_id: int
    session_type: str = Field(..., regex="^(practice|assessment|review)$")
    duration_seconds: int = Field(..., ge=0)
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    completion_rate: float = Field(..., ge=0.0, le=1.0)
    is_correct: Optional[bool] = None
    hints_used: int = Field(0, ge=0)
    attempts_count: int = Field(1, ge=1)
    time_to_first_attempt_seconds: Optional[int] = Field(None, ge=0)
    context: Dict[str, Any] = Field(default_factory=dict)
    device_type: Optional[str] = None
    difficulty_perceived: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    user_feedback: Optional[str] = Field(None, max_length=1000)
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    recommendation_id: Optional[int] = None


class LearningSessionResponse(LearningSessionCreate, TimestampSchema):
    """Schema for learning session responses."""

    id: int
    knowledge_gained: float
    ab_test_variant: Optional[str]

    # Related data
    question: Optional[Dict[str, Any]] = None
    concept: Optional[Dict[str, Any]] = None


class MasteryLevelResponse(BaseSchema, TimestampSchema):
    """Schema for mastery level responses."""

    id: int
    user_id: int
    concept_id: int
    mastery_score: float
    confidence_score: float
    retention_score: float
    total_practice_time_minutes: int
    questions_attempted: int
    questions_correct: int
    last_practiced_at: Optional[datetime]
    improvement_rate: float
    time_to_mastery_estimate_minutes: Optional[int]
    optimal_difficulty: float
    challenge_level: str
    streak_days: int

    # Related data
    concept: Optional[Dict[str, Any]] = None


class ConceptProgressResponse(BaseSchema):
    """Detailed concept progress information."""

    concept_id: int
    concept_name: str
    mastery_level: float
    confidence_level: float
    time_spent_minutes: int
    questions_completed: int
    accuracy_rate: float
    last_practiced: Optional[datetime]
    estimated_time_to_mastery: Optional[int]
    prerequisite_readiness: float
    next_recommended_difficulty: float


class LearningPathResponse(BaseSchema):
    """Learning path recommendation."""

    user_id: int
    recommended_concepts: List[ConceptProgressResponse]
    current_focus: List[int]  # concept IDs
    prerequisites_needed: List[int]  # concept IDs
    next_milestones: List[Dict[str, Any]]
    estimated_completion_time: int  # minutes
    difficulty_progression: List[float]


class StreakResponse(BaseSchema, TimestampSchema):
    """Schema for streak responses."""

    id: int
    user_id: int
    streak_type: str
    current_count: int
    longest_count: int
    is_active: bool
    target_value: int
    unit: str
    frequency: str
    current_period_progress: int
    next_milestone: Optional[int]
    consistency_score: int

    # Status info
    days_until_break: Optional[int] = None
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    motivation_message: Optional[str] = None


class PracticeSessionSummary(BaseSchema):
    """Summary of a practice session."""

    session_date: datetime
    total_time_minutes: int
    questions_attempted: int
    questions_correct: int
    accuracy_rate: float
    concepts_practiced: List[str]
    average_difficulty: float
    mastery_gains: Dict[int, float]  # concept_id -> mastery gain
    streak_updates: List[Dict[str, Any]]


class WeeklyProgressReport(BaseSchema):
    """Weekly progress report."""

    user_id: int
    week_start_date: datetime
    total_practice_minutes: int
    total_questions: int
    accuracy_rate: float
    concepts_improved: List[str]
    streaks_maintained: List[str]
    streaks_broken: List[str]
    mastery_improvements: Dict[str, float]
    next_week_goals: List[str]
    achievement_highlights: List[str]


class AnalyticsEvent(BaseSchema):
    """Generic analytics event."""

    event_type: str
    user_id: int
    timestamp: datetime
    properties: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    ab_test_info: Optional[Dict[str, str]] = None
