from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class Streak(BaseModel):
    """User streak tracking for habit formation and gamification."""

    __tablename__ = "streaks"

    # Streak Type and Status
    streak_type = Column(
        String(50), nullable=False
    )  # daily_practice, weekly_goal, concept_mastery
    current_count = Column(Integer, default=0)
    longest_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Timing
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now())
    broken_at = Column(DateTime(timezone=True), nullable=True)

    # Goals and Thresholds
    target_value = Column(Integer, nullable=False)  # e.g., 15 minutes per day
    unit = Column(String(20), nullable=False)  # minutes, questions, concepts
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly

    # Progress Tracking
    current_period_progress = Column(Integer, default=0)
    total_accumulated = Column(Integer, default=0)

    # Streak Metadata
    difficulty_level = Column(
        String(20), default="normal"
    )  # easy, normal, hard, custom
    custom_rules = Column(JSON, default=dict)  # Custom streak rules and conditions

    # Gamification
    milestone_rewards = Column(JSON, default=list)  # Rewards earned at milestones
    next_milestone = Column(Integer, nullable=True)  # Next milestone target
    streak_multiplier = Column(Integer, default=1)  # Multiplier for rewards

    # Analytics
    average_daily_value = Column(Integer, default=0)  # Rolling average
    best_day_value = Column(Integer, default=0)  # Best single day performance
    consistency_score = Column(Integer, default=0)  # 0-100 consistency rating

    # Context
    created_reason = Column(String(100), nullable=True)  # Why this streak was created
    tags = Column(JSON, default=list)  # Tags for categorization

    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="streaks")

    def __repr__(self):
        return f"<Streak(user_id={self.user_id}, type={self.streak_type}, current={self.current_count})>"
