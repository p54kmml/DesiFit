from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, AIConversation
from backend.schemas import AIChatRequest, AIChatResponse, AIConversationMessage
from backend.auth import get_current_user
from backend.services.ai_service import process_chat_message, is_openai_configured

router = APIRouter(prefix="/ai", tags=["AI Fitness Assistant"])


@router.post("/chat", response_model=AIChatResponse)
def chat_with_desifit_ai(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = process_chat_message(
        user_message=req.message,
        user=current_user,
        db=db,
        requested_days_override=req.workout_frequency_days,
        preferred_split_override=req.preferred_split
    )
    return AIChatResponse(
        reply=result["reply"],
        is_fallback=result["is_fallback"],
        api_connected=result["api_connected"],
        system_notes=result.get("system_notes")
    )


@router.get("/history", response_model=List[AIConversationMessage])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chats = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.created_at.asc())
        .all()
    )
    return chats


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(AIConversation).filter(AIConversation.user_id == current_user.id).delete()
    db.commit()
    return None


@router.get("/status")
def get_ai_status():
    configured = is_openai_configured()
    return {
        "api_connected": configured,
        "model": "gpt-4o-mini" if configured else "rule-based-fallback",
        "description": "OpenAI Live Assistant" if configured else "DesiFit Rule-Based Expert Assistant (Offline/Fallback Mode)"
    }
