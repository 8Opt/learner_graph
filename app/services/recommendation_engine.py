import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import RecommendationEngineException
from app.models.concept import Concept
from app.models.learning_session import LearningSession
from app.models.mastery import MasteryLevel
from app.models.question import Question
from app.models.user import User
from app.repository.recommendation_repository import recommendation_repository
from app.repository.user_repository import user_repository


class RecommendationEngine:
    """Core recommendation engine using collaborative filtering and content-based approaches."""

    def __init__(self):
        self.algorithm_version = "v1.2.0"

    def generate_recommendations(
        self,
        db: Session,
        user_id: int,
        max_recommendations: int = 10,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate personalized recommendations for a user."""
        try:
            # Get user profile and learning history
            user = user_repository.get(db, user_id)
            if not user:
                raise RecommendationEngineException(f"User {user_id} not found")

            user_profile = self._build_user_profile(db, user)

            # Generate different types of recommendations
            recommendations = []

            # Next best questions (40% of recommendations)
            next_questions = self._recommend_next_questions(
                db, user_profile, max_recommendations // 2
            )
            recommendations.extend(next_questions)

            # Concept review (30% of recommendations)
            review_concepts = self._recommend_concept_review(
                db, user_profile, max_recommendations // 3
            )
            recommendations.extend(review_concepts)

            # Streak goals (30% of recommendations)
            streak_goals = self._recommend_streak_goals(
                db, user_profile, max_recommendations // 3
            )
            recommendations.extend(streak_goals)

            # Sort by priority and limit
            recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
            recommendations = recommendations[:max_recommendations]

            # Store recommendations in database
            stored_recommendations = []
            for rec in recommendations:
                stored_rec = recommendation_repository.create_recommendation(
                    db=db,
                    user_id=user_id,
                    recommendation_type=rec["type"],
                    priority_score=rec["priority_score"],
                    confidence_score=rec["confidence_score"],
                    reasoning=rec["reasoning"],
                    algorithm_version=self.algorithm_version,
                    target_questions=rec.get("target_questions", []),
                    target_concepts=rec.get("target_concepts", []),
                    recommended_difficulty=rec.get("difficulty"),
                    estimated_time_minutes=rec.get("estimated_time"),
                )
                stored_recommendations.append(stored_rec)

            return stored_recommendations

        except Exception as e:
            raise RecommendationEngineException(
                f"Error generating recommendations: {str(e)}"
            )

    def _build_user_profile(self, db: Session, user: User) -> Dict[str, Any]:
        """Build comprehensive user profile for recommendations."""
        # Get user's mastery levels
        mastery_levels = (
            db.query(MasteryLevel).filter(MasteryLevel.user_id == user.id).all()
        )

        # Get recent learning sessions
        recent_sessions = (
            db.query(LearningSession)
            .filter(
                and_(
                    LearningSession.user_id == user.id,
                    LearningSession.created_at
                    >= datetime.utcnow() - timedelta(days=30),
                )
            )
            .all()
        )

        # Calculate current mastery state
        mastery_map = {ml.concept_id: ml.mastery_score for ml in mastery_levels}

        # Analyze learning patterns
        session_patterns = self._analyze_session_patterns(recent_sessions)

        return {
            "user_id": user.id,
            "skill_level": user.skill_level,
            "preferred_difficulty": user.preferred_difficulty,
            "total_practice_minutes": user.total_practice_minutes,
            "current_streak": user.current_streak_days,
            "mastery_levels": mastery_map,
            "session_patterns": session_patterns,
            "learning_goals": user.learning_goals,
            "ab_test_group": user.ab_test_group,
        }

    def _recommend_next_questions(
        self, db: Session, user_profile: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        """Recommend next best questions using difficulty adaptation."""
        recommendations = []

        # Get concepts where user needs practice
        weak_concepts = [
            concept_id
            for concept_id, mastery in user_profile["mastery_levels"].items()
            if mastery < settings.min_mastery_threshold
        ]

        if not weak_concepts:
            # If all concepts are mastered, focus on maintenance
            weak_concepts = list(user_profile["mastery_levels"].keys())

        for concept_id in weak_concepts[:count]:
            # Find optimal difficulty for this user/concept
            optimal_difficulty = self._calculate_optimal_difficulty(
                user_profile, concept_id
            )

            # Get suitable questions
            questions = (
                db.query(Question)
                .filter(
                    and_(
                        Question.concept_id == concept_id,
                        Question.difficulty_level.between(
                            optimal_difficulty - 0.1, optimal_difficulty + 0.1
                        ),
                        Question.is_active == True,
                    )
                )
                .limit(3)
                .all()
            )

            if questions:
                priority_score = self._calculate_priority_score(
                    user_profile, concept_id, "next_question"
                )

                recommendations.append(
                    {
                        "type": "next_question",
                        "priority_score": priority_score,
                        "confidence_score": 0.85,
                        "target_questions": [q.id for q in questions],
                        "target_concepts": [concept_id],
                        "difficulty": optimal_difficulty,
                        "estimated_time": sum(
                            q.time_limit_seconds
                            for q in questions
                            if q.time_limit_seconds
                        )
                        // 60
                        or 20,
                        "reasoning": f"Based on your current mastery level, these questions will help strengthen your understanding of this concept.",
                    }
                )

        return recommendations

    def _recommend_concept_review(
        self, db: Session, user_profile: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        """Recommend concepts for review based on forgetting curve."""
        recommendations = []

        # Find concepts that might need review (temporal learning gaps)
        mastery_levels = (
            db.query(MasteryLevel)
            .filter(
                and_(
                    MasteryLevel.user_id == user_profile["user_id"],
                    MasteryLevel.last_practiced_at
                    < datetime.utcnow() - timedelta(days=7),
                )
            )
            .order_by(MasteryLevel.last_practiced_at.asc())
            .limit(count)
            .all()
        )

        for mastery in mastery_levels:
            # Calculate decay score
            days_since_practice = (datetime.utcnow() - mastery.last_practiced_at).days
            decay_score = min(1.0, days_since_practice * mastery.decay_rate)

            priority_score = self._calculate_priority_score(
                user_profile, mastery.concept_id, "concept_review"
            )

            recommendations.append(
                {
                    "type": "concept_review",
                    "priority_score": priority_score * decay_score,
                    "confidence_score": 0.75,
                    "target_concepts": [mastery.concept_id],
                    "target_questions": [],
                    "difficulty": mastery.optimal_difficulty,
                    "estimated_time": 15,
                    "reasoning": f"It's been {days_since_practice} days since you practiced this concept. A quick review will help maintain your mastery.",
                }
            )

        return recommendations

    def _recommend_streak_goals(
        self, db: Session, user_profile: Dict[str, Any], count: int
    ) -> List[Dict[str, Any]]:
        """Recommend personalized streak goals."""
        recommendations = []

        current_streak = user_profile["current_streak"]
        avg_practice = user_profile["session_patterns"].get("avg_daily_minutes", 15)

        # Suggest incremental streak improvements
        if current_streak < 7:
            target_streak = 7
            difficulty = "achievable"
        elif current_streak < 30:
            target_streak = 30
            difficulty = "moderate"
        else:
            target_streak = current_streak + 7
            difficulty = "challenging"

        recommendations.append(
            {
                "type": "streak_goal",
                "priority_score": 0.7,
                "confidence_score": 0.8,
                "target_questions": [],
                "target_concepts": [],
                "difficulty": None,
                "estimated_time": max(15, int(avg_practice * 1.2)),
                "reasoning": f"Build consistency with a {target_streak}-day practice streak. Based on your current pattern, this is {difficulty} but achievable.",
                "streak_target": target_streak,
                "daily_minutes": max(15, int(avg_practice * 1.2)),
            }
        )

        return recommendations

    def _calculate_optimal_difficulty(
        self, user_profile: Dict[str, Any], concept_id: int
    ) -> float:
        """Calculate optimal difficulty for a user-concept pair using zone of proximal development."""
        base_difficulty = user_profile["preferred_difficulty"]

        if concept_id in user_profile["mastery_levels"]:
            mastery = user_profile["mastery_levels"][concept_id]
            # Adjust based on mastery: higher mastery = can handle more difficulty
            difficulty_adjustment = (mastery - 0.5) * 0.3
            optimal_difficulty = base_difficulty + difficulty_adjustment
        else:
            # New concept, start easier
            optimal_difficulty = base_difficulty - 0.1

        # Clamp between 0.1 and 0.9
        return max(0.1, min(0.9, optimal_difficulty))

    def _calculate_priority_score(
        self, user_profile: Dict[str, Any], concept_id: int, recommendation_type: str
    ) -> float:
        """Calculate priority score for a recommendation."""
        base_score = 0.5

        # Factor in mastery level (lower mastery = higher priority for practice)
        if concept_id in user_profile["mastery_levels"]:
            mastery = user_profile["mastery_levels"][concept_id]
            mastery_factor = 1.0 - mastery  # Inverse relationship
            base_score += mastery_factor * 0.3

        # Factor in learning goals
        if concept_id in user_profile.get("learning_goals", []):
            base_score += 0.2

        # Type-specific adjustments
        if recommendation_type == "next_question":
            base_score += 0.1  # Questions are high priority
        elif recommendation_type == "streak_goal":
            base_score += (
                0.05 * user_profile["current_streak"]
            )  # Reward streak building

        return min(1.0, base_score)

    def _analyze_session_patterns(
        self, sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze user's learning session patterns."""
        if not sessions:
            return {
                "avg_daily_minutes": 15,
                "preferred_session_length": 20,
                "peak_performance_hour": 14,
                "consistency_score": 0,
            }

        # Calculate averages
        total_minutes = sum(s.duration_seconds for s in sessions) // 60
        avg_daily = total_minutes / max(
            30, len(set(s.created_at.date() for s in sessions))
        )

        durations = [s.duration_seconds // 60 for s in sessions]
        avg_session_length = sum(durations) / len(durations) if durations else 20

        # Find peak performance hour
        hours = [s.created_at.hour for s in sessions]
        if hours:
            hour_counts = {}
            for h in hours:
                hour_counts[h] = hour_counts.get(h, 0) + 1
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
        else:
            peak_hour = 14

        return {
            "avg_daily_minutes": avg_daily,
            "preferred_session_length": avg_session_length,
            "peak_performance_hour": peak_hour,
            "consistency_score": min(100, len(sessions) * 2),
        }


# Create service instance
recommendation_engine = RecommendationEngine()
