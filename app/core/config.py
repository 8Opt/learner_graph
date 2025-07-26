from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./learner_graph.db"

    # API Settings
    api_v1_str: str = "/api/v1"
    project_name: str = "Learner Graph RAG System"
    version: str = "1.0.0"

    # Redis for caching and real-time data
    redis_url: str = "redis://localhost:6379"

    # Recommendation Engine Settings
    recommendation_cache_ttl: int = 300  # 5 minutes
    max_recommendations: int = 10
    min_mastery_threshold: float = 0.7

    # Streak Engine Settings
    streak_decay_hours: int = 48  # Hours before streak breaks
    min_practice_minutes_per_day: int = 15

    # A/B Testing
    ab_test_enabled: bool = True
    default_ab_split: float = 0.5  # 50/50 split

    # Performance Targets
    recommendation_latency_p99_ms: int = 100
    target_practice_boost_percent: float = 15.0

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
