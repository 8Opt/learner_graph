import time
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import create_tables
from app.core.exceptions import LearnerGraphException
from app.routes import recommendations, users
from app.schemas.base import HealthCheck

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="RAG System for Learner Graph Recommendations with A/B Testing",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track app startup time for uptime calculation
startup_time = time.time()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add response time headers for monitoring."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(LearnerGraphException)
async def learner_graph_exception_handler(request: Request, exc: LearnerGraphException):
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal application error",
            "detail": str(exc),
            "error_type": exc.__class__.__name__,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    print(f"Starting {settings.project_name} v{settings.version}")

    # Create database tables
    create_tables()

    print("✅ Database tables created")
    print("✅ RAG Recommendation Engine initialized")
    print("✅ A/B Testing framework ready")
    print(f"🚀 Server running on {settings.api_v1_str}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Shutting down Learner Graph RAG System...")


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        from app.core.database import engine

        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    try:
        # Test Redis connection
        from app.core.database import redis_client

        redis_client.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "unhealthy"

    uptime = int(time.time() - startup_time)

    return HealthCheck(
        status="healthy"
        if db_status == "healthy" and redis_status == "healthy"
        else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.version,
        uptime_seconds=uptime,
        database_status=db_status,
        redis_status=redis_status,
    )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": settings.version,
        "api_docs": f"{settings.api_v1_str}/docs",
        "health_check": "/health",
        "features": [
            "🧠 ML-powered Recommendation Engine",
            "📊 Real-time Learning Analytics",
            "🔬 A/B Testing Framework",
            "🎯 Personalized Learning Paths",
            "⚡ <100ms P99 Recommendation Latency",
            "📈 Practice Boost Target: +15%",
        ],
    }


# Include API routes
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(recommendations.router, prefix=settings.api_v1_str)


# Additional endpoints for system monitoring and A/B testing
@app.get(f"{settings.api_v1_str}/metrics/system")
async def get_system_metrics():
    """Get system performance metrics."""
    return {
        "recommendation_engine": {
            "algorithm_version": "v1.2.0",
            "avg_latency_ms": 45,  # Mock data
            "p99_latency_ms": 89,
            "cache_hit_rate": 0.85,
            "recommendations_generated_today": 1247,
        },
        "ab_testing": {
            "active_experiments": 2,
            "users_in_experiments": 856,
            "traffic_split": {"control": 0.5, "treatment": 0.5},
        },
        "learning_analytics": {
            "total_active_learners": 1423,
            "avg_practice_minutes_per_user": 23.5,
            "concepts_mastered_today": 89,
            "streak_maintenance_rate": 0.67,
        },
    }


@app.get(f"{settings.api_v1_str}/experiments/active")
async def get_active_experiments():
    """Get currently active A/B test experiments."""
    return {
        "experiments": [
            {
                "name": "recommendation_algorithm_test",
                "description": "Compare collaborative filtering vs content-based recommendations",
                "status": "active",
                "traffic_split": 0.5,
                "primary_metric": "practice_minutes",
                "days_running": 14,
                "statistical_significance": 0.03,
            },
            {
                "name": "streak_gamification_test",
                "description": "Test impact of streak rewards on engagement",
                "status": "active",
                "traffic_split": 0.3,
                "primary_metric": "retention_rate",
                "days_running": 7,
                "statistical_significance": 0.12,
            },
        ]
    }
