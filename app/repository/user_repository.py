from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.learning_session import LearningSession
from app.models.mastery import MasteryLevel
from app.models.streak import Streak
from app.models.user import User

from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self):
        super().__init__(User)

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username."""
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    def get_with_stats(self, db: Session, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user with computed statistics."""
        user = self.get(db, user_id)
        if not user:
            return None

        # Calculate statistics
        stats = self._calculate_user_stats(db, user_id)

        return {**user.to_dict(), **stats}

    def get_learning_profile(
        self, db: Session, user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get detailed learning profile for a user."""
        user = self.get(db, user_id)
        if not user:
            return None

        # Get recent learning sessions for analysis
        recent_sessions = (
            db.query(LearningSession)
            .filter(
                and_(
                    LearningSession.user_id == user_id,
                    LearningSession.created_at
                    >= datetime.utcnow() - timedelta(days=30),
                )
            )
            .order_by(desc(LearningSession.created_at))
            .limit(100)
            .all()
        )

        # Analyze learning patterns
        profile = self._analyze_learning_patterns(recent_sessions)
        profile["user_id"] = user_id

        return profile

    def get_users_by_ab_group(self, db: Session, ab_test_group: str) -> List[User]:
        """Get all users in a specific A/B test group."""
        return db.query(User).filter(User.ab_test_group == ab_test_group).all()

    def assign_ab_group(
        self,
        db: Session,
        user_id: int,
        ab_test_group: str,
        experiment_cohort: str = None,
    ) -> User:
        """Assign user to A/B test group."""
        user = self.get_or_404(db, user_id)
        user.ab_test_group = ab_test_group
        if experiment_cohort:
            user.experiment_cohort = experiment_cohort

        db.commit()
        db.refresh(user)
        return user

    def update_practice_stats(
        self, db: Session, user_id: int, session_duration_minutes: int
    ) -> User:
        """Update user's practice statistics after a learning session."""
        user = self.get_or_404(db, user_id)

        user.total_practice_minutes += session_duration_minutes
        user.last_practice_at = datetime.utcnow()

        # Update streak if applicable
        self._update_daily_streak(db, user)

        db.commit()
        db.refresh(user)
        return user

    def get_active_learners(self, db: Session, days: int = 7) -> List[User]:
        """Get users who have been active in the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            db.query(User)
            .filter(
                and_(User.last_practice_at >= cutoff_date, User.is_deleted == False)
            )
            .all()
        )

    def get_users_needing_recommendations(self, db: Session) -> List[User]:
        """Get users who might need new recommendations."""
        # Users who haven't practiced in 1-3 days (re-engagement)
        start_date = datetime.utcnow() - timedelta(days=3)
        end_date = datetime.utcnow() - timedelta(days=1)

        return (
            db.query(User)
            .filter(
                and_(
                    User.last_practice_at.between(start_date, end_date),
                    User.is_deleted == False,
                )
            )
            .all()
        )

    def _calculate_user_stats(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Calculate comprehensive user statistics."""
        # Get learning session stats
        session_stats = (
            db.query(
                func.count(LearningSession.id).label("total_questions"),
                func.sum(
                    func.case([(LearningSession.is_correct == True, 1)], else_=0)
                ).label("correct_questions"),
                func.avg(LearningSession.score).label("avg_score"),
            )
            .filter(LearningSession.user_id == user_id)
            .first()
        )

        # Get mastery stats
        mastery_stats = (
            db.query(
                func.count(MasteryLevel.id).label("concepts_tracked"),
                func.sum(
                    func.case([(MasteryLevel.mastery_score >= 0.7, 1)], else_=0)
                ).label("concepts_mastered"),
                func.avg(MasteryLevel.mastery_score).label("avg_mastery"),
            )
            .filter(MasteryLevel.user_id == user_id)
            .first()
        )

        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_practice = (
            db.query(
                func.sum(LearningSession.duration_seconds).label(
                    "recent_practice_seconds"
                )
            )
            .filter(
                and_(
                    LearningSession.user_id == user_id,
                    LearningSession.created_at >= week_ago,
                )
            )
            .first()
        )

        return {
            "total_questions_attempted": session_stats.total_questions or 0,
            "total_questions_correct": session_stats.correct_questions or 0,
            "accuracy_rate": (session_stats.correct_questions or 0)
            / max(session_stats.total_questions or 1, 1),
            "average_score": float(session_stats.avg_score or 0),
            "concepts_tracked": mastery_stats.concepts_tracked or 0,
            "concepts_mastered": mastery_stats.concepts_mastered or 0,
            "average_mastery_score": float(mastery_stats.avg_mastery or 0),
            "weekly_practice_minutes": (recent_practice.recent_practice_seconds or 0)
            // 60,
            "practice_consistency_score": self._calculate_consistency_score(
                db, user_id
            ),
        }

    def _analyze_learning_patterns(
        self, sessions: List[LearningSession]
    ) -> Dict[str, Any]:
        """Analyze learning patterns from recent sessions."""
        if not sessions:
            return {
                "learning_style": "unknown",
                "optimal_session_length": 30,
                "best_practice_times": [],
                "difficulty_preference": 0.5,
                "learning_velocity": 0.0,
            }

        # Analyze session durations
        durations = [s.duration_seconds // 60 for s in sessions]  # Convert to minutes
        optimal_length = sum(durations) // len(durations) if durations else 30

        # Analyze practice times
        practice_hours = [s.created_at.hour for s in sessions]
        time_preferences = self._categorize_practice_times(practice_hours)

        # Analyze difficulty preferences
        difficulties = [s.question.difficulty_level for s in sessions if s.question]
        avg_difficulty = sum(difficulties) / len(difficulties) if difficulties else 0.5

        # Calculate learning velocity (concepts per week)
        unique_concepts = len(
            set(s.question.concept_id for s in sessions if s.question)
        )
        weeks = max(1, len(sessions) / 7)  # Rough estimate
        velocity = unique_concepts / weeks

        return {
            "learning_style": self._determine_learning_style(sessions),
            "optimal_session_length": min(
                max(optimal_length, 10), 120
            ),  # Clamp between 10-120 minutes
            "best_practice_times": time_preferences,
            "difficulty_preference": avg_difficulty,
            "learning_velocity": velocity,
        }

    def _update_daily_streak(self, db: Session, user: User) -> None:
        """Update user's daily practice streak."""
        today = datetime.utcnow().date()

        if user.last_practice_at:
            last_practice_date = user.last_practice_at.date()

            if last_practice_date == today:
                # Already practiced today, no change needed
                return
            elif last_practice_date == today - timedelta(days=1):
                # Practiced yesterday, continue streak
                user.current_streak_days += 1
            else:
                # Gap in practice, reset streak
                user.current_streak_days = 1
        else:
            # First practice session
            user.current_streak_days = 1

        # Update longest streak if necessary
        if user.current_streak_days > user.longest_streak_days:
            user.longest_streak_days = user.current_streak_days

    def _calculate_consistency_score(self, db: Session, user_id: int) -> int:
        """Calculate practice consistency score (0-100)."""
        # Get last 30 days of practice
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        daily_practice = (
            db.query(
                func.date(LearningSession.created_at).label("practice_date"),
                func.count(LearningSession.id).label("session_count"),
            )
            .filter(
                and_(
                    LearningSession.user_id == user_id,
                    LearningSession.created_at >= thirty_days_ago,
                )
            )
            .group_by(func.date(LearningSession.created_at))
            .all()
        )

        if not daily_practice:
            return 0

        # Calculate consistency based on days practiced vs total days
        days_practiced = len(daily_practice)
        consistency_score = min(100, int((days_practiced / 30) * 100))

        return consistency_score

    def _categorize_practice_times(self, hours: List[int]) -> List[str]:
        """Categorize practice times into periods."""
        if not hours:
            return []

        morning = sum(1 for h in hours if 6 <= h < 12)
        afternoon = sum(1 for h in hours if 12 <= h < 18)
        evening = sum(1 for h in hours if 18 <= h < 22)
        night = sum(1 for h in hours if h >= 22 or h < 6)

        times = [
            ("morning", morning),
            ("afternoon", afternoon),
            ("evening", evening),
            ("night", night),
        ]

        # Return top 2 practice times
        times.sort(key=lambda x: x[1], reverse=True)
        return [time[0] for time in times[:2] if time[1] > 0]

    def _determine_learning_style(self, sessions: List[LearningSession]) -> str:
        """Determine learning style based on session patterns."""
        if not sessions:
            return "balanced"

        # Analyze session characteristics
        short_sessions = sum(
            1 for s in sessions if s.duration_seconds < 900
        )  # < 15 min
        long_sessions = sum(
            1 for s in sessions if s.duration_seconds > 2700
        )  # > 45 min

        hint_usage = sum(s.hints_used for s in sessions) / len(sessions)
        attempt_rate = sum(s.attempts_count for s in sessions) / len(sessions)

        # Simple heuristic-based classification
        if short_sessions > len(sessions) * 0.7:
            return "bite_sized"
        elif long_sessions > len(sessions) * 0.3:
            return "deep_focus"
        elif hint_usage > 2:
            return "guided"
        elif attempt_rate > 2:
            return "experimental"
        else:
            return "balanced"


# Create repository instance
user_repository = UserRepository()
