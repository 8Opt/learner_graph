import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ABTestException
from app.models.recommendation import ABTestExperiment
from app.models.user import User
from app.repository.recommendation_repository import ab_test_repository
from app.repository.user_repository import user_repository


class ABTestingService:
    """Service for managing A/B testing experiments."""

    def __init__(self):
        self.enabled = settings.ab_test_enabled

    def assign_user_to_group(
        self, db: Session, user_id: int, experiment_name: str
    ) -> str:
        """Assign user to A/B test group using consistent hashing."""
        if not self.enabled:
            return "control"

        experiment = ab_test_repository.get_experiment_by_name(db, experiment_name)
        if not experiment or not experiment.is_active:
            return "control"

        # Use consistent hashing for stable group assignment
        hash_input = f"{user_id}_{experiment_name}_{experiment.start_date}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        assignment_ratio = (hash_value % 100) / 100.0

        group = (
            "treatment" if assignment_ratio < experiment.traffic_split else "control"
        )

        # Update user's A/B test group
        user_repository.assign_ab_group(db, user_id, group, experiment_name)

        return group

    def get_algorithm_variant(
        self, db: Session, user_id: int, experiment_name: str
    ) -> str:
        """Get the algorithm variant for the user's A/B test group."""
        group = self.assign_user_to_group(db, user_id, experiment_name)

        experiment = ab_test_repository.get_experiment_by_name(db, experiment_name)
        if not experiment:
            return "baseline"

        return (
            experiment.treatment_algorithm
            if group == "treatment"
            else experiment.control_algorithm
        )

    def create_experiment(
        self,
        db: Session,
        name: str,
        description: str,
        hypothesis: str,
        control_algorithm: str,
        treatment_algorithm: str,
        primary_metric: str,
        target_improvement: float,
        duration_days: int = 30,
        traffic_split: float = 0.5,
    ) -> ABTestExperiment:
        """Create a new A/B test experiment."""
        experiment_data = {
            "name": name,
            "description": description,
            "hypothesis": hypothesis,
            "control_algorithm": control_algorithm,
            "treatment_algorithm": treatment_algorithm,
            "traffic_split": traffic_split,
            "start_date": datetime.utcnow(),
            "end_date": datetime.utcnow() + datetime.timedelta(days=duration_days),
            "primary_metric": primary_metric,
            "target_improvement": target_improvement,
            "is_active": True,
        }

        return ab_test_repository.create(db, obj_in=experiment_data)

    def calculate_experiment_results(
        self, db: Session, experiment_name: str
    ) -> Dict[str, Any]:
        """Calculate statistical results for an A/B test experiment."""
        experiment = ab_test_repository.get_experiment_by_name(db, experiment_name)
        if not experiment:
            raise ABTestException(f"Experiment {experiment_name} not found")

        # Get users in each group
        control_users = user_repository.get_users_by_ab_group(db, "control")
        treatment_users = user_repository.get_users_by_ab_group(db, "treatment")

        # Calculate metrics for each group
        control_metrics = self._calculate_group_metrics(
            db, control_users, experiment.primary_metric
        )
        treatment_metrics = self._calculate_group_metrics(
            db, treatment_users, experiment.primary_metric
        )

        # Perform statistical test (simplified)
        effect_size = self._calculate_effect_size(control_metrics, treatment_metrics)
        significance = self._calculate_significance(control_metrics, treatment_metrics)

        # Update experiment with results
        ab_test_repository.update_experiment_metrics(
            db,
            experiment.id,
            len(control_users),
            len(treatment_users),
            significance,
            effect_size,
        )

        return {
            "experiment_name": experiment_name,
            "control_group_size": len(control_users),
            "treatment_group_size": len(treatment_users),
            "control_metric_value": control_metrics["mean"],
            "treatment_metric_value": treatment_metrics["mean"],
            "effect_size": effect_size,
            "statistical_significance": significance,
            "is_significant": significance < 0.05,
            "winner": self._determine_winner(
                control_metrics, treatment_metrics, effect_size, significance
            ),
        }

    def _calculate_group_metrics(
        self, db: Session, users: List[User], metric_name: str
    ) -> Dict[str, float]:
        """Calculate metrics for a group of users."""
        if not users:
            return {"mean": 0.0, "std": 0.0, "count": 0}

        if metric_name == "practice_minutes":
            values = [user.total_practice_minutes for user in users]
        elif metric_name == "retention_rate":
            # Simplified: users who practiced in last 7 days
            week_ago = datetime.utcnow() - datetime.timedelta(days=7)
            active_users = sum(
                1
                for user in users
                if user.last_practice_at and user.last_practice_at >= week_ago
            )
            return {"mean": active_users / len(users), "std": 0.0, "count": len(users)}
        else:
            values = [0.0] * len(users)  # Default

        import statistics

        return {
            "mean": statistics.mean(values) if values else 0.0,
            "std": statistics.stdev(values) if len(values) > 1 else 0.0,
            "count": len(values),
        }

    def _calculate_effect_size(
        self, control_metrics: Dict[str, float], treatment_metrics: Dict[str, float]
    ) -> float:
        """Calculate Cohen's d effect size."""
        if control_metrics["count"] == 0 or treatment_metrics["count"] == 0:
            return 0.0

        pooled_std = (
            (control_metrics["std"] ** 2 + treatment_metrics["std"] ** 2) / 2
        ) ** 0.5
        if pooled_std == 0:
            return 0.0

        return (treatment_metrics["mean"] - control_metrics["mean"]) / pooled_std

    def _calculate_significance(
        self, control_metrics: Dict[str, float], treatment_metrics: Dict[str, float]
    ) -> float:
        """Calculate p-value using simplified t-test approximation."""
        # Simplified calculation - in production, use proper statistical libraries
        if control_metrics["count"] < 30 or treatment_metrics["count"] < 30:
            return 1.0  # Not enough data

        # Mock calculation - replace with proper t-test
        effect_size = abs(
            self._calculate_effect_size(control_metrics, treatment_metrics)
        )

        # Simple heuristic: larger effect sizes are more likely to be significant
        if effect_size > 0.5:
            return 0.01
        elif effect_size > 0.3:
            return 0.05
        elif effect_size > 0.1:
            return 0.15
        else:
            return 0.5

    def _determine_winner(
        self,
        control_metrics: Dict[str, float],
        treatment_metrics: Dict[str, float],
        effect_size: float,
        significance: float,
    ) -> str:
        """Determine the winning variant."""
        if significance >= 0.05:
            return "inconclusive"

        if treatment_metrics["mean"] > control_metrics["mean"]:
            return "treatment"
        else:
            return "control"


# Create service instance
ab_testing_service = ABTestingService()
