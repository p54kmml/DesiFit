from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.database import get_db
from backend.models import (
    User,
    WorkoutPlan,
    WorkoutPlanExercise,
    WorkoutLog,
    WorkoutLogExercise,
    Exercise
)
from backend.schemas import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    WorkoutPlanResponse,
    WorkoutLogCreate,
    WorkoutLogResponse
)
from backend.auth import get_current_user

router = APIRouter(prefix="/workouts", tags=["Workouts"])


# ==========================================
# WORKOUT PLANS
# ==========================================

@router.get("/plans", response_model=List[WorkoutPlanResponse])
def get_user_workout_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plans = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.user_id == current_user.id)
        .order_by(WorkoutPlan.created_at.desc())
        .all()
    )
    return plans


@router.post("/plans", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def create_workout_plan(
    plan_in: WorkoutPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if plan_in.exercises:
        if len(plan_in.exercises) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A workout plan can contain a maximum of 50 exercises."
            )
        requested_exercise_ids = {item.exercise_id for item in plan_in.exercises}
        accessible_exercises = db.query(Exercise.id).filter(
            Exercise.id.in_(requested_exercise_ids),
            or_(Exercise.is_custom == False, Exercise.created_by_user_id == current_user.id)
        ).all()
        accessible_ids = {row[0] for row in accessible_exercises}
        if accessible_ids != requested_exercise_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more exercises were not found")

    plan = WorkoutPlan(
        user_id=current_user.id,
        title=plan_in.title,
        description=plan_in.description,
        goal=plan_in.goal,
        difficulty=plan_in.difficulty
    )
    db.add(plan)
    db.flush()

    for item in plan_in.exercises:
        # Exercise ownership was validated above; never attach another user's custom exercise.
        plan_exercise = WorkoutPlanExercise(
            workout_plan_id=plan.id,
            exercise_id=item.exercise_id,
            sets=item.sets,
            reps=item.reps,
            rest_seconds=item.rest_seconds,
            order_index=item.order_index
        )
        db.add(plan_exercise)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=WorkoutPlanResponse)
def get_workout_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout plan not found")
    return plan


@router.put("/plans/{plan_id}", response_model=WorkoutPlanResponse)
def update_workout_plan(
    plan_id: int,
    plan_in: WorkoutPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout plan not found")

    if plan_in.title is not None:
        plan.title = plan_in.title
    if plan_in.description is not None:
        plan.description = plan_in.description
    if plan_in.goal is not None:
        plan.goal = plan_in.goal
    if plan_in.difficulty is not None:
        plan.difficulty = plan_in.difficulty

    if plan_in.exercises is not None:
        if len(plan_in.exercises) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A workout plan can contain a maximum of 50 exercises."
            )
        requested_exercise_ids = {item.exercise_id for item in plan_in.exercises}
        if requested_exercise_ids:
            accessible_exercises = db.query(Exercise.id).filter(
                Exercise.id.in_(requested_exercise_ids),
                or_(Exercise.is_custom == False, Exercise.created_by_user_id == current_user.id)
            ).all()
            accessible_ids = {row[0] for row in accessible_exercises}
            if accessible_ids != requested_exercise_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more exercises were not found")

        # Clear existing plan exercises and insert new ones
        db.query(WorkoutPlanExercise).filter(WorkoutPlanExercise.workout_plan_id == plan.id).delete()
        for item in plan_in.exercises:
            plan_exercise = WorkoutPlanExercise(
                workout_plan_id=plan.id,
                exercise_id=item.exercise_id,
                sets=item.sets,
                reps=item.reps,
                rest_seconds=item.rest_seconds,
                order_index=item.order_index
            )
            db.add(plan_exercise)

    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.id == plan_id, WorkoutPlan.user_id == current_user.id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout plan not found")
    db.delete(plan)
    db.commit()
    return None


# ==========================================
# WORKOUT LOGS
# ==========================================

@router.get("/logs", response_model=List[WorkoutLogResponse])
def get_workout_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == current_user.id)
        .order_by(WorkoutLog.date.desc(), WorkoutLog.id.desc())
        .all()
    )
    return logs


@router.post("/logs", response_model=WorkoutLogResponse, status_code=status.HTTP_201_CREATED)
def record_workout_log(
    log_in: WorkoutLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if log_in.workout_plan_id is not None:
        owned_plan = db.query(WorkoutPlan.id).filter(
            WorkoutPlan.id == log_in.workout_plan_id,
            WorkoutPlan.user_id == current_user.id
        ).first()
        if not owned_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout plan not found")

    if log_in.logged_exercises:
        if len(log_in.logged_exercises) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A workout log can contain a maximum of 50 exercises."
            )
        requested_exercise_ids = {item.exercise_id for item in log_in.logged_exercises}
        accessible_exercises = db.query(Exercise.id).filter(
            Exercise.id.in_(requested_exercise_ids),
            or_(Exercise.is_custom == False, Exercise.created_by_user_id == current_user.id)
        ).all()
        accessible_ids = {row[0] for row in accessible_exercises}
        if accessible_ids != requested_exercise_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more exercises were not found")

    log = WorkoutLog(
        user_id=current_user.id,
        workout_plan_id=log_in.workout_plan_id,
        title=log_in.title,
        notes=log_in.notes,
        duration_minutes=log_in.duration_minutes,
        date=log_in.date or date.today(),
        completed=log_in.completed
    )
    db.add(log)
    db.flush()

    for ex_item in log_in.logged_exercises:
        # Exercise ownership was validated above.
        log_exercise = WorkoutLogExercise(
            workout_log_id=log.id,
            exercise_id=ex_item.exercise_id,
            sets_completed=ex_item.sets_completed,
            reps_completed=ex_item.reps_completed,
            weight_kg=ex_item.weight_kg,
            notes=ex_item.notes
        )
        db.add(log_exercise)

    db.commit()
    db.refresh(log)
    return log


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.id == log_id, WorkoutLog.user_id == current_user.id)
        .first()
    )
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout log not found")
    db.delete(log)
    db.commit()
    return None
