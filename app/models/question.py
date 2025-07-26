from sqlalchemy import Column, Integer, String, Float, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class Question(BaseModel):
    """Practice question/exercise model."""
    __tablename__ = "questions"
    
    # Basic Info
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)  # Question content/prompt
    question_type = Column(String(50), nullable=False)  # multiple_choice, coding, essay, etc.
    
    # Difficulty and Scoring
    difficulty_level = Column(Float, nullable=False)  # 0.0 = easy, 1.0 = very hard
    max_points = Column(Integer, default=100)
    time_limit_seconds = Column(Integer, nullable=True)
    
    # Content Structure
    options = Column(JSON, nullable=True)  # For multiple choice questions
    correct_answer = Column(JSON, nullable=True)  # Correct answer(s)
    explanation = Column(Text, nullable=True)  # Explanation of the correct answer
    hints = Column(JSON, default=list)  # List of hints
    
    # Metadata
    tags = Column(JSON, default=list)  # Tags for categorization
    learning_objectives = Column(JSON, default=list)  # What this question teaches/tests
    
    # Analytics
    total_attempts = Column(Integer, default=0)
    correct_attempts = Column(Integer, default=0)
    average_time_seconds = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    concept = relationship("Concept", back_populates="questions")
    
    learning_sessions = relationship("LearningSession", back_populates="question") 