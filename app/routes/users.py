from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repository.user_repository import user_repository
from app.schemas.base import APIResponse, PaginationParams
from app.schemas.user import (
    UserCreate,
    UserLearningProfile,
    UserProgress,
    UserResponse,
    UserStats,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    try:
        # Check if username or email already exists
        if user_repository.get_by_username(db, user_data.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        if user_repository.get_by_email(db, user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create user
        user = user_repository.create(db, obj_in=user_data.dict())
        return UserResponse.from_orm(user)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = user_repository.get_or_404(db, user_id)
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)
):
    """Update user information."""
    try:
        user = user_repository.get_or_404(db, user_id)
        updated_user = user_repository.update(
            db, db_obj=user, obj_in=user_update.dict(exclude_unset=True)
        )
        return UserResponse.from_orm(updated_user)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    """Get comprehensive user statistics."""
    try:
        user_with_stats = user_repository.get_with_stats(db, user_id)
        if not user_with_stats:
            raise HTTPException(status_code=404, detail="User not found")

        return UserStats(**user_with_stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user stats: {str(e)}"
        )


@router.get("/{user_id}/progress", response_model=UserProgress)
async def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    """Get user learning progress summary."""
    try:
        # This would integrate with mastery tracking
        # For now, return a structured response
        return UserProgress(
            user_id=user_id,
            overall_progress=0.65,
            concepts_by_mastery={
                "mastered": 12,
                "proficient": 8,
                "learning": 5,
                "not_started": 3,
            },
            recent_improvements=[
                {"concept": "Algebra", "improvement": 0.15, "date": "2024-01-15"},
                {"concept": "Geometry", "improvement": 0.08, "date": "2024-01-14"},
            ],
            suggested_focus_areas=["Calculus", "Statistics"],
            estimated_time_to_next_milestone=120,  # minutes
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching user progress: {str(e)}"
        )


@router.get("/{user_id}/learning-profile", response_model=UserLearningProfile)
async def get_learning_profile(user_id: int, db: Session = Depends(get_db)):
    """Get detailed learning profile for a user."""
    try:
        profile = user_repository.get_learning_profile(db, user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        return UserLearningProfile(**profile)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching learning profile: {str(e)}"
        )


@router.post("/{user_id}/practice-session")
async def record_practice_session(
    user_id: int,
    duration_minutes: int = Query(..., ge=1, le=300),
    db: Session = Depends(get_db),
):
    """Record a practice session and update user stats."""
    try:
        updated_user = user_repository.update_practice_stats(
            db, user_id, duration_minutes
        )

        return APIResponse(
            success=True,
            message="Practice session recorded successfully",
            data={
                "user_id": user_id,
                "total_practice_minutes": updated_user.total_practice_minutes,
                "current_streak_days": updated_user.current_streak_days,
                "session_duration": duration_minutes,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error recording practice session: {str(e)}"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(), db: Session = Depends(get_db)
):
    """List users with pagination."""
    try:
        users = user_repository.get_multi(
            db, skip=pagination.offset, limit=pagination.size
        )
        return [UserResponse.from_orm(user) for user in users]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")


@router.get("/active/recent")
async def get_active_learners(
    days: int = Query(7, ge=1, le=30), db: Session = Depends(get_db)
):
    """Get users who have been active recently."""
    try:
        active_users = user_repository.get_active_learners(db, days=days)

        return APIResponse(
            success=True,
            data=[
                {
                    "user_id": user.id,
                    "username": user.username,
                    "last_practice_at": user.last_practice_at,
                    "current_streak_days": user.current_streak_days,
                    "total_practice_minutes": user.total_practice_minutes,
                }
                for user in active_users
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching active learners: {str(e)}"
        )
