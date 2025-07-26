from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import BaseSchema, TimestampSchema


class RecommendationRequest(BaseSchema):
    """Request schema for getting recommendations."""

    user_id: int
    session_context: Optional[str] = Field(
        None, description="Context like 'morning', 'review', etc."
    )
    max_recommendations: int = Field(10, ge=1, le=50)
    recommendation_types: Optional[List[str]] = Field(
        None, description="Filter by recommendation types"
    )
    difficulty_range: Optional[tuple[float, float]] = Field(
        None, description="Difficulty range (min, max)"
    )
    time_budget_minutes: Optional[int] = Field(None, ge=1, le=180)
    include_explanations: bool = Field(
        True, description="Include reasoning explanations"
    )


class RecommendationResponse(BaseSchema):
    """Individual recommendation response."""

    id: int
    recommendation_type: str
    priority_score: float
    confidence_score: float
    target_questions: List[int]
    target_concepts: List[int]
    recommended_difficulty: Optional[float]
    estimated_time_minutes: Optional[int]
    reasoning: str
    algorithm_version: str
    expires_at: Optional[datetime]

    # Question/Concept details (populated by service)
    questions: Optional[List[Dict[str, Any]]] = None
    concepts: Optional[List[Dict[str, Any]]] = None


class RecommendationListResponse(BaseSchema):
    """Response with list of recommendations."""

    recommendations: List[RecommendationResponse]
    total_count: int
    algorithm_version: str
    generated_at: datetime
    user_context: Dict[str, Any]
    ab_test_info: Optional[Dict[str, Any]] = None


class RecommendationFeedback(BaseSchema):
    """Feedback on a recommendation."""

    recommendation_id: int
    user_id: int
    action: str = Field(..., regex="^(accepted|rejected|ignored|completed)$")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = Field(None, max_length=1000)
    completion_time_seconds: Optional[int] = None


class ExplanationRequest(BaseSchema):
    """Request for recommendation explanation."""

    recommendation_id: int
    user_id: int
    explanation_type: str = Field("detailed", regex="^(simple|detailed|technical)$")


class ExplanationResponse(BaseSchema):
    """Explanation of why a recommendation was made."""

    recommendation_id: int
    explanation_type: str
    main_reasons: List[str]
    detailed_explanation: str
    feature_importance: Dict[str, float]
    user_factors: Dict[str, Any]
    concept_relationships: Optional[Dict[str, Any]] = None
    confidence_factors: Dict[str, float]


class NextBestQuestionRequest(BaseSchema):
    """Request for next best question recommendations."""

    user_id: int
    concept_id: Optional[int] = None
    current_difficulty: Optional[float] = None
    time_budget_minutes: Optional[int] = 30
    exclude_recent: bool = True
    recent_threshold_hours: int = 24


class NextBestQuestionResponse(BaseSchema):
    """Response with next best question recommendations."""

    questions: List[Dict[str, Any]]
    reasoning: str
    difficulty_explanation: str
    estimated_success_rate: float
    learning_impact_score: float


class StreakGoalRecommendation(BaseSchema):
    """Streak goal recommendation."""

    streak_type: str
    target_value: int
    unit: str
    frequency: str
    difficulty_level: str
    estimated_success_rate: float
    motivation_message: str
    milestone_rewards: List[str]


class RecommendationPerformanceMetrics(BaseSchema):
    """Performance metrics for recommendations."""

    recommendation_id: int
    click_through_rate: Optional[float]
    completion_rate: Optional[float]
    average_satisfaction: Optional[float]
    time_to_action_seconds: Optional[int]
    learning_outcome_impact: Optional[float]
