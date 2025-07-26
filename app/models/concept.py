from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from .base import BaseModel

# Many-to-many relationship table for concept prerequisites
concept_prerequisites = Table(
    "concept_prerequisites",
    BaseModel.metadata,
    Column("concept_id", Integer, ForeignKey("concepts.id"), primary_key=True),
    Column("prerequisite_id", Integer, ForeignKey("concepts.id"), primary_key=True),
)


class Concept(BaseModel):
    """Learning concept/topic model."""

    __tablename__ = "concepts"

    # Basic Info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    subject_area = Column(String(100), nullable=False, index=True)

    # Hierarchy and Organization
    level = Column(Integer, default=1)  # 1=basic, 2=intermediate, 3=advanced
    difficulty_score = Column(Float, default=0.5)  # 0.0 = easy, 1.0 = very hard
    estimated_time_minutes = Column(Integer, default=30)  # Time to master this concept

    # Content and Metadata
    learning_objectives = Column(JSON, default=list)  # List of learning objectives
    tags = Column(JSON, default=list)  # Tags for categorization

    # Graph Relationships
    prerequisites = relationship(
        "Concept",
        secondary=concept_prerequisites,
        primaryjoin=id == concept_prerequisites.c.concept_id,
        secondaryjoin=id == concept_prerequisites.c.prerequisite_id,
        back_populates="dependent_concepts",
        overlaps="dependent_concepts",
    )

    dependent_concepts = relationship(
        "Concept",
        secondary=concept_prerequisites,
        primaryjoin=id == concept_prerequisites.c.prerequisite_id,
        secondaryjoin=id == concept_prerequisites.c.concept_id,
        back_populates="prerequisites",
        overlaps="prerequisites",
    )

    # Other Relationships
    questions = relationship("Question", back_populates="concept")
    mastery_levels = relationship("MasteryLevel", back_populates="concept")
