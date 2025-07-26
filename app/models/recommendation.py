from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class Recommendation(BaseModel):
    """Recommendation tracking for the recommendation engine."""

    __tablename__ = "recommendations"

    # Recommendation Content
    recommendation_type = Column(
        String(50), nullable=False
    )  # next_question, concept_review, streak_goal
    priority_score = Column(
        Float, nullable=False
    )  # 0.0 to 1.0, higher = more important
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0, how confident we are

    # Targeting
    target_questions = Column(JSON, default=list)  # List of question IDs
    target_concepts = Column(JSON, default=list)  # List of concept IDs
    recommended_difficulty = Column(Float, nullable=True)  # Suggested difficulty level
    estimated_time_minutes = Column(Integer, nullable=True)  # Estimated completion time

    # Reasoning and Explainability
    reasoning = Column(Text, nullable=False)  # Human-readable explanation
    algorithm_version = Column(
        String(50), nullable=False
    )  # Which algorithm generated this
    feature_weights = Column(
        JSON, default=dict
    )  # Feature importance for explainability

    # Context
    context_data = Column(JSON, default=dict)  # Additional context used in generation
    session_context = Column(
        String(100), nullable=True
    )  # morning, afternoon, weekend, etc.

    # Personalization Factors
    user_preferences_applied = Column(JSON, default=dict)  # Which preferences were used
    learning_style_match = Column(
        Float, nullable=True
    )  # How well this matches user's style

    # Status and Lifecycle
    status = Column(
        String(20), default="pending"
    )  # pending, shown, accepted, rejected, expired
    shown_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Performance Metrics
    click_through_rate = Column(Float, nullable=True)
    completion_rate = Column(Float, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating from user

    # A/B Testing
    ab_test_group = Column(String(50), nullable=True)
    ab_test_variant = Column(String(50), nullable=True)
    control_group = Column(Boolean, default=False)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="recommendations")

    learning_sessions = relationship("LearningSession", back_populates="recommendation")

    def __repr__(self):
        return f"<Recommendation(id={self.id}, user_id={self.user_id}, type={self.recommendation_type})>"


class ABTestExperiment(BaseModel):
    """A/B test experiment tracking."""

    __tablename__ = "ab_test_experiments"

    # Experiment Definition
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=False)

    # Experiment Configuration
    control_algorithm = Column(String(50), nullable=False)
    treatment_algorithm = Column(String(50), nullable=False)
    traffic_split = Column(Float, default=0.5)  # Percentage to treatment group

    # Timing
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)

    # Success Metrics
    primary_metric = Column(
        String(50), nullable=False
    )  # practice_minutes, retention_rate, etc.
    secondary_metrics = Column(JSON, default=list)
    target_improvement = Column(
        Float, nullable=False
    )  # Expected improvement percentage

    # Statistical Settings
    confidence_level = Column(Float, default=0.95)
    minimum_sample_size = Column(Integer, default=1000)
    minimum_effect_size = Column(Float, default=0.05)

    # Results
    control_group_size = Column(Integer, default=0)
    treatment_group_size = Column(Integer, default=0)
    statistical_significance = Column(Float, nullable=True)  # p-value
    effect_size = Column(Float, nullable=True)
    winner = Column(String(20), nullable=True)  # control, treatment, inconclusive

    # Metadata
    created_by = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)

    def __repr__(self):
        return f"<ABTestExperiment(name={self.name}, active={self.is_active})>"
