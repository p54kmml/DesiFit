from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Exercise, User
from backend.schemas import ExerciseCreate, ExerciseResponse
from backend.auth import get_current_user

router = APIRouter(prefix="/exercises", tags=["Exercise Library"])


@router.get("", response_model=List[ExerciseResponse])
def get_exercises(
    muscle_group: Optional[str] = Query(None, description="Filter by muscle group"),
    search: Optional[str] = Query(None, description="Search exercise by name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve exercises with optional filtering by muscle group and search query."""
    # Return: (1) built-in/shared exercises (is_custom=False)
    #       + (2) the current user's own custom exercises
    from sqlalchemy import or_
    query = db.query(Exercise).filter(
        or_(
            Exercise.is_custom == False,
            Exercise.created_by_user_id == current_user.id
        )
    )

    if muscle_group and muscle_group.lower() != "all":
        query = query.filter(Exercise.muscle_group.ilike(f"%{muscle_group}%"))

    if search:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))

    return query.order_by(Exercise.muscle_group, Exercise.name).all()


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
    exercise_in: ExerciseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new custom exercise."""
    # Block duplicate only within shared library or the same user's custom exercises
    from sqlalchemy import or_
    existing = db.query(Exercise).filter(
        Exercise.name.ilike(exercise_in.name),
        or_(
            Exercise.is_custom == False,
            Exercise.created_by_user_id == current_user.id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Exercise '{exercise_in.name}' already exists in your library."
        )

    exercise = Exercise(
        name=exercise_in.name,
        muscle_group=exercise_in.muscle_group,
        equipment=exercise_in.equipment,
        difficulty=exercise_in.difficulty,
        instructions=exercise_in.instructions,
        is_custom=True,
        created_by_user_id=current_user.id
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.get("/{exercise_id}", response_model=ExerciseResponse)
def get_exercise_by_id(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import or_
    exercise = db.query(Exercise).filter(
        Exercise.id == exercise_id,
        or_(
            Exercise.is_custom == False,
            Exercise.created_by_user_id == current_user.id
        )
    ).first()
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return exercise
