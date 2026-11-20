from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import DashboardStatsResponse
from backend.auth import get_current_user
from backend.services.stats_service import get_dashboard_statistics

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all computed statistics, weekly trends, and recent records for the logged-in user."""
    return get_dashboard_statistics(current_user, db)
