from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class MasteryLevel(BaseModel):
    """User's mastery level for specific concepts over time."""
    __tablename__ = "mastery_levels"
    
    # Mastery Metrics
    mastery_score = Column(Float, nullable=False)  # 0.0 to 1.0
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    retention_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Learning Progress
    total_practice_time_minutes = Column(Integer, default=0)
    questions_attempted = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    
    # Temporal Learning Gaps
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    decay_rate = Column(Float, default=0.01)  # How fast knowledge decays
    forgetting_curve_params = Column(JSON, default=dict)  # Parameters for forgetting curve
    
    # Learning Velocity
    improvement_rate = Column(Float, default=0.0)  # Rate of improvement
    time_to_mastery_estimate_minutes = Column(Integer, nullable=True)
    
    # Difficulty Adaptation
    optimal_difficulty = Column(Float, default=0.5)  # Optimal difficulty for this user/concept
    challenge_level = Column(String(20), default="appropriate")  # too_easy, appropriate, too_hard
    
    # Learning Path Context
    prerequisite_mastery_average = Column(Float, default=0.0)  # Average mastery of prerequisites
    dependent_concepts_unlocked = Column(Integer, default=0)  # How many concepts this unlocks
    
    # Analytics
    streak_days = Column(Integer, default=0)
    last_streak_update = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="mastery_levels")
    
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False, index=True)
    concept = relationship("Concept", back_populates="mastery_levels")
    
    def __repr__(self):
        return f"<MasteryLevel(user_id={self.user_id}, concept_id={self.concept_id}, score={self.mastery_score})>" 