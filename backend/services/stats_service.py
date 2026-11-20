from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session

from backend.models import (
    User,
    WorkoutLog,
    NutritionLog,
    BodyMeasurement
)
from backend.schemas import DashboardStatsResponse, WeeklyActivityItem, WorkoutLogResponse, BodyMeasurementResponse


def get_dashboard_statistics(user: User, db: Session) -> DashboardStatsResponse:
    profile = user.profile
    today = date.today()

    # Weight resolution: latest body measurement or profile
    latest_measurement = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user.id)
        .order_by(BodyMeasurement.date.desc(), BodyMeasurement.id.desc())
        .first()
    )
    current_weight = (
        latest_measurement.weight_kg
        if latest_measurement
        else (profile.current_weight_kg if (profile and profile.current_weight_kg) else 0.0)
    )
    target_weight = profile.target_weight_kg if (profile and profile.target_weight_kg) else 0.0

    # Nutrition targets
    daily_cal_target = profile.target_calories if (profile and profile.target_calories) else 2000
    daily_pro_target = profile.target_protein_g if (profile and profile.target_protein_g) else 120.0

    # Today's nutrition consumption
    today_nutritions = (
        db.query(NutritionLog)
        .filter(NutritionLog.user_id == user.id, NutritionLog.date == today)
        .all()
    )
    today_calories = sum(n.total_calories for n in today_nutritions)
    today_protein = sum(n.total_protein_g for n in today_nutritions)

    # Workouts completed
    total_workouts = db.query(WorkoutLog).filter(WorkoutLog.user_id == user.id, WorkoutLog.completed == True).count()

    # Past 7 days activity
    seven_days_ago = today - timedelta(days=6)
    week_logs = (
        db.query(WorkoutLog)
        .filter(
            WorkoutLog.user_id == user.id,
            WorkoutLog.date >= seven_days_ago,
            WorkoutLog.date <= today,
            WorkoutLog.completed == True
        )
        .all()
    )
    this_week_workouts_count = len(week_logs)

    # Build weekly day-by-day activity breakdown
    weekly_activity: List[WeeklyActivityItem] = []
    for i in range(7):
        current_day = seven_days_ago + timedelta(days=i)
        day_logs = [log for log in week_logs if log.date == current_day]
        workouts_count = len(day_logs)
        total_duration = sum(log.duration_minutes for log in day_logs)
        weekly_activity.append(
            WeeklyActivityItem(
                day=current_day.strftime("%a"),
                date=current_day.strftime("%Y-%m-%d"),
                workouts_completed=workouts_count,
                total_duration_minutes=total_duration
            )
        )

    # Recent workouts (last 5)
    recent_workout_records = (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user.id)
        .order_by(WorkoutLog.date.desc(), WorkoutLog.id.desc())
        .limit(5)
        .all()
    )
    recent_workouts = [WorkoutLogResponse.model_validate(w) for w in recent_workout_records]

    # Recent measurements (last 7)
    recent_meas_records = (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user.id)
        .order_by(BodyMeasurement.date.desc(), BodyMeasurement.id.desc())
        .limit(7)
        .all()
    )
    recent_measurements = [BodyMeasurementResponse.model_validate(m) for m in recent_meas_records]

    is_onboarded = profile.is_onboarded if profile else False

    return DashboardStatsResponse(
        full_name=user.full_name,
        is_onboarded=is_onboarded,
        fitness_goal=profile.fitness_goal if (profile and profile.fitness_goal) else "Fitness",
        current_weight_kg=round(current_weight, 1),
        target_weight_kg=round(target_weight, 1),
        daily_calorie_target=daily_cal_target,
        daily_protein_target=round(daily_pro_target, 1),
        today_calories_consumed=round(today_calories, 1),
        today_protein_consumed=round(today_protein, 1),
        total_workouts_completed=total_workouts,
        this_week_workouts_count=this_week_workouts_count,
        weekly_activity=weekly_activity,
        recent_workouts=recent_workouts,
        recent_measurements=recent_measurements
    )
