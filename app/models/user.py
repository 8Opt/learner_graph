from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from .base import BaseModel, SoftDeleteMixin


class User(BaseModel, SoftDeleteMixin):
    """User/Learner model."""

    __tablename__ = "users"

    # Basic Info
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)

    # Learning Profile
    skill_level = Column(
        String(20), default="beginner"
    )  # beginner, intermediate, advanced
    learning_goals = Column(JSON, default=list)  # List of learning objectives
    preferred_difficulty = Column(Float, default=0.5)  # 0.0 = easy, 1.0 = hard

    # Engagement Metrics
    total_practice_minutes = Column(Integer, default=0)
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_practice_at = Column(DateTime(timezone=True), nullable=True)

    # A/B Testing
    ab_test_group = Column(String(50), nullable=True)  # Control group identifier
    experiment_cohort = Column(String(50), nullable=True)  # Experiment cohort

    # Personalization
    recommendation_preferences = Column(
        JSON, default=dict
    )  # User preferences for recommendations

    # Relationships
    learning_sessions = relationship("LearningSession", back_populates="user")
    mastery_levels = relationship("MasteryLevel", back_populates="user")
    streaks = relationship("Streak", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
