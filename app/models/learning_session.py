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

from .base import BaseModel


class LearningSession(BaseModel):
    """Learning session/practice log model."""

    __tablename__ = "learning_sessions"

    # Session Info
    session_type = Column(String(50), nullable=False)  # practice, assessment, review
    duration_seconds = Column(Integer, nullable=False)

    # Performance Metrics
    score = Column(Float, nullable=True)  # 0.0 to 1.0
    completion_rate = Column(Float, nullable=False)  # 0.0 to 1.0
    is_correct = Column(Boolean, nullable=True)  # For single question sessions

    # Engagement Metrics
    hints_used = Column(Integer, default=0)
    attempts_count = Column(Integer, default=1)
    time_to_first_attempt_seconds = Column(Integer, nullable=True)

    # Context and Metadata
    context = Column(JSON, default=dict)  # Additional context data
    device_type = Column(String(50), nullable=True)  # web, mobile, tablet
    user_agent = Column(String(500), nullable=True)

    # Learning Data
    knowledge_gained = Column(Float, default=0.0)  # Estimated knowledge gain
    difficulty_perceived = Column(Float, nullable=True)  # User's perceived difficulty
    confidence_level = Column(Float, nullable=True)  # User's confidence in answer

    # Feedback
    user_feedback = Column(Text, nullable=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 rating

    # A/B Testing Context
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=True)
    ab_test_variant = Column(String(50), nullable=True)

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="learning_sessions")

    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    question = relationship("Question", back_populates="learning_sessions")

    recommendation = relationship("Recommendation", back_populates="learning_sessions")
