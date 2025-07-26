from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.recommendation import ABTestExperiment, Recommendation

from .base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for recommendation operations."""

    def __init__(self):
        super().__init__(Recommendation)

    def get_active_recommendations(
        self, db: Session, user_id: int, limit: int = 10
    ) -> List[Recommendation]:
        """Get active recommendations for a user."""
        now = datetime.utcnow()
        return (
            db.query(Recommendation)
            .filter(
                and_(
                    Recommendation.user_id == user_id,
                    Recommendation.status == "pending",
                    or_(
                        Recommendation.expires_at.is_(None),
                        Recommendation.expires_at > now,
                    ),
                )
            )
            .order_by(desc(Recommendation.priority_score))
            .limit(limit)
            .all()
        )

    def create_recommendation(
        self,
        db: Session,
        user_id: int,
        recommendation_type: str,
        priority_score: float,
        confidence_score: float,
        reasoning: str,
        algorithm_version: str,
        **kwargs,
    ) -> Recommendation:
        """Create a new recommendation."""
        recommendation_data = {
            "user_id": user_id,
            "recommendation_type": recommendation_type,
            "priority_score": priority_score,
            "confidence_score": confidence_score,
            "reasoning": reasoning,
            "algorithm_version": algorithm_version,
            **kwargs,
        }

        return self.create(db, obj_in=recommendation_data)

    def record_feedback(
        self,
        db: Session,
        recommendation_id: int,
        action: str,
        satisfaction_rating: Optional[int] = None,
    ) -> Recommendation:
        """Record user feedback on a recommendation."""
        recommendation = self.get_or_404(db, recommendation_id)
        recommendation.status = action
        recommendation.responded_at = datetime.utcnow()

        if satisfaction_rating is not None:
            recommendation.satisfaction_rating = satisfaction_rating

        db.commit()
        db.refresh(recommendation)
        return recommendation


class ABTestRepository(BaseRepository[ABTestExperiment]):
    """Repository for A/B test experiment operations."""

    def __init__(self):
        super().__init__(ABTestExperiment)

    def get_active_experiments(self, db: Session) -> List[ABTestExperiment]:
        """Get all active A/B test experiments."""
        now = datetime.utcnow()
        return (
            db.query(ABTestExperiment)
            .filter(
                and_(
                    ABTestExperiment.is_active == True,
                    ABTestExperiment.start_date <= now,
                    ABTestExperiment.end_date >= now,
                )
            )
            .all()
        )


# Create repository instances
recommendation_repository = RecommendationRepository()
ab_test_repository = ABTestRepository()
