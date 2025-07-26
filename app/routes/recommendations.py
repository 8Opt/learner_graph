from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repository.recommendation_repository import recommendation_repository
from app.schemas.base import APIResponse
from app.schemas.recommendation import (
    ExplanationRequest,
    ExplanationResponse,
    NextBestQuestionRequest,
    RecommendationFeedback,
    RecommendationListResponse,
    RecommendationRequest,
)
from app.services.ab_testing_service import ab_testing_service
from app.services.recommendation_engine import recommendation_engine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/generate", response_model=RecommendationListResponse)
async def generate_recommendations(
    request: RecommendationRequest, db: Session = Depends(get_db)
):
    """Generate personalized recommendations for a user."""
    try:
        # A/B test: determine which algorithm to use
        algorithm_variant = ab_testing_service.get_algorithm_variant(
            db, request.user_id, "recommendation_algorithm_test"
        )

        # Generate recommendations
        recommendations = recommendation_engine.generate_recommendations(
            db=db,
            user_id=request.user_id,
            max_recommendations=request.max_recommendations,
            context={
                "session_context": request.session_context,
                "time_budget_minutes": request.time_budget_minutes,
                "algorithm_variant": algorithm_variant,
            },
        )

        # Convert to response format
        rec_responses = []
        for rec in recommendations:
            rec_responses.append(
                {
                    "id": rec.id,
                    "recommendation_type": rec.recommendation_type,
                    "priority_score": rec.priority_score,
                    "confidence_score": rec.confidence_score,
                    "target_questions": rec.target_questions,
                    "target_concepts": rec.target_concepts,
                    "recommended_difficulty": rec.recommended_difficulty,
                    "estimated_time_minutes": rec.estimated_time_minutes,
                    "reasoning": rec.reasoning,
                    "algorithm_version": rec.algorithm_version,
                    "expires_at": rec.expires_at,
                }
            )

        return RecommendationListResponse(
            recommendations=rec_responses,
            total_count=len(rec_responses),
            algorithm_version=recommendation_engine.algorithm_version,
            generated_at=datetime.utcnow(),
            user_context={"algorithm_variant": algorithm_variant},
            ab_test_info={"variant": algorithm_variant},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating recommendations: {str(e)}"
        )


@router.post("/feedback")
async def record_recommendation_feedback(
    feedback: RecommendationFeedback, db: Session = Depends(get_db)
):
    """Record user feedback on a recommendation."""
    try:
        updated_recommendation = recommendation_repository.record_feedback(
            db=db,
            recommendation_id=feedback.recommendation_id,
            action=feedback.action,
            satisfaction_rating=feedback.satisfaction_rating,
        )

        return APIResponse(
            success=True,
            message="Feedback recorded successfully",
            data={
                "recommendation_id": updated_recommendation.id,
                "status": updated_recommendation.status,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error recording feedback: {str(e)}"
        )


@router.get("/explanation/{recommendation_id}", response_model=ExplanationResponse)
async def get_recommendation_explanation(
    recommendation_id: int,
    user_id: int = Query(...),
    explanation_type: str = Query("detailed", regex=r"^(simple|detailed|technical)$"),
    db: Session = Depends(get_db),
):
    """Get explanation for why a recommendation was made."""
    try:
        recommendation = recommendation_repository.get_or_404(db, recommendation_id)

        if recommendation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Build explanation based on recommendation data
        explanation = {
            "recommendation_id": recommendation_id,
            "explanation_type": explanation_type,
            "main_reasons": [
                "Based on your current mastery levels",
                "Optimized for your learning style",
                "Aligned with your practice goals",
            ],
            "detailed_explanation": recommendation.reasoning,
            "feature_importance": recommendation.feature_weights or {},
            "user_factors": recommendation.user_preferences_applied or {},
            "confidence_factors": {
                "algorithm_confidence": recommendation.confidence_score,
                "data_quality": 0.85,
                "personalization_strength": recommendation.learning_style_match or 0.75,
            },
        }

        return ExplanationResponse(**explanation)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating explanation: {str(e)}"
        )


@router.get("/active/{user_id}")
async def get_active_recommendations(
    user_id: int, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)
):
    """Get active recommendations for a user."""
    try:
        recommendations = recommendation_repository.get_active_recommendations(
            db=db, user_id=user_id, limit=limit
        )

        return APIResponse(
            success=True,
            data=[
                {
                    "id": rec.id,
                    "type": rec.recommendation_type,
                    "priority_score": rec.priority_score,
                    "reasoning": rec.reasoning,
                    "estimated_time_minutes": rec.estimated_time_minutes,
                }
                for rec in recommendations
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching recommendations: {str(e)}"
        )


@router.post("/next-question", response_model=APIResponse)
async def get_next_best_question(
    request: NextBestQuestionRequest, db: Session = Depends(get_db)
):
    """Get next best question recommendations."""
    try:
        # This would integrate with the recommendation engine
        # For now, return a structured response
        return APIResponse(
            success=True,
            message="Next question recommendations generated",
            data={
                "user_id": request.user_id,
                "concept_id": request.concept_id,
                "recommended_difficulty": request.current_difficulty or 0.5,
                "estimated_success_rate": 0.75,
                "reasoning": "Based on your current progress and optimal challenge level",
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting next question: {str(e)}"
        )
