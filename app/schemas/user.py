from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from .base import BaseSchema, TimestampSchema


class UserBase(BaseSchema):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    skill_level: str = Field("beginner", regex="^(beginner|intermediate|advanced)$")
    learning_goals: List[str] = Field(default_factory=list)
    preferred_difficulty: float = Field(0.5, ge=0.0, le=1.0)


class UserCreate(UserBase):
    """Schema for creating a new user."""

    pass


class UserUpdate(BaseSchema):
    """Schema for updating user information."""

    full_name: Optional[str] = Field(None, max_length=255)
    skill_level: Optional[str] = Field(None, regex="^(beginner|intermediate|advanced)$")
    learning_goals: Optional[List[str]] = None
    preferred_difficulty: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommendation_preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase, TimestampSchema):
    """Schema for user responses."""

    id: int
    total_practice_minutes: int
    current_streak_days: int
    longest_streak_days: int
    last_practice_at: Optional[datetime]
    ab_test_group: Optional[str]
    experiment_cohort: Optional[str]
    recommendation_preferences: Dict[str, Any]
    is_deleted: bool


class UserStats(BaseSchema):
    """User statistics and progress."""

    user_id: int
    total_practice_minutes: int
    total_questions_attempted: int
    total_questions_correct: int
    accuracy_rate: float
    current_streak_days: int
    longest_streak_days: int
    concepts_mastered: int
    concepts_in_progress: int
    average_mastery_score: float
    weekly_practice_minutes: int
    monthly_practice_minutes: int
    practice_consistency_score: int  # 0-100


class UserProgress(BaseSchema):
    """User learning progress summary."""

    user_id: int
    overall_progress: float  # 0.0 to 1.0
    concepts_by_mastery: Dict[str, int]  # mastery_level -> count
    recent_improvements: List[Dict[str, Any]]
    suggested_focus_areas: List[str]
    estimated_time_to_next_milestone: Optional[int]  # minutes


class UserLearningProfile(BaseSchema):
    """Detailed user learning profile."""

    user_id: int
    learning_style: str
    optimal_session_length: int  # minutes
    best_practice_times: List[str]  # e.g., ["morning", "evening"]
    difficulty_preference: float
    concept_preferences: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]
    learning_velocity: float  # concepts per week
