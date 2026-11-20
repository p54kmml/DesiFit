from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, FoodItem, NutritionLog
from backend.schemas import (
    FoodItemCreate,
    FoodItemResponse,
    NutritionLogCreate,
    NutritionLogResponse,
    DailyNutritionSummary
)
from backend.auth import get_current_user

router = APIRouter(prefix="/nutrition", tags=["Nutrition Tracker"])


# ==========================================
# FOOD ITEMS
# ==========================================

@router.get("/foods", response_model=List[FoodItemResponse])
def get_food_items(
    search: Optional[str] = Query(None, description="Search food items"),
    desi_only: Optional[bool] = Query(False, description="Filter only Desi specials"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import or_
    query = db.query(FoodItem).filter(
        or_(
            FoodItem.is_custom == False,
            FoodItem.created_by_user_id == current_user.id
        )
    )
    if desi_only:
        query = query.filter(FoodItem.is_desi_special == True)
    if search:
        query = query.filter(FoodItem.name.ilike(f"%{search}%"))
    return query.order_by(FoodItem.name).all()


@router.post("/foods", response_model=FoodItemResponse, status_code=status.HTTP_201_CREATED)
def create_food_item(
    food_in: FoodItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Block duplicate only within shared library or the same user's custom items
    from sqlalchemy import or_
    existing = db.query(FoodItem).filter(
        FoodItem.name.ilike(food_in.name),
        or_(
            FoodItem.is_custom == False,
            FoodItem.created_by_user_id == current_user.id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Food item '{food_in.name}' already exists in your library."
        )

    food = FoodItem(
        name=food_in.name,
        serving_size=food_in.serving_size,
        calories=food_in.calories,
        protein_g=food_in.protein_g,
        carbs_g=food_in.carbs_g,
        fat_g=food_in.fat_g,
        fiber_g=food_in.fiber_g or 0.0,
        is_desi_special=food_in.is_desi_special or False,
        is_custom=True,
        created_by_user_id=current_user.id
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food


# ==========================================
# NUTRITION LOGS
# ==========================================

@router.get("/logs", response_model=List[NutritionLogResponse])
def get_nutrition_logs(
    log_date: Optional[date] = Query(None, description="Date to retrieve logs for"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_date = log_date or date.today()
    logs = (
        db.query(NutritionLog)
        .filter(NutritionLog.user_id == current_user.id, NutritionLog.date == target_date)
        .order_by(NutritionLog.created_at.asc())
        .all()
    )
    return logs


@router.post("/logs", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED)
def log_meal(
    log_in: NutritionLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_
    food = db.query(FoodItem).filter(
        FoodItem.id == log_in.food_item_id,
        or_(
            FoodItem.is_custom == False,
            FoodItem.created_by_user_id == current_user.id
        )
    ).first()
    if not food:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")

    servings = max(0.1, log_in.servings)
    total_cals = round(food.calories * servings, 1)
    total_pro = round(food.protein_g * servings, 1)
    total_carbs = round(food.carbs_g * servings, 1)
    total_fat = round(food.fat_g * servings, 1)

    log = NutritionLog(
        user_id=current_user.id,
        food_item_id=food.id,
        meal_type=log_in.meal_type,
        servings=servings,
        total_calories=total_cals,
        total_protein_g=total_pro,
        total_carbs_g=total_carbs,
        total_fat_g=total_fat,
        date=log_in.date or date.today()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nutrition_log(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    log = (
        db.query(NutritionLog)
        .filter(NutritionLog.id == log_id, NutritionLog.user_id == current_user.id)
        .first()
    )
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nutrition log not found")
    db.delete(log)
    db.commit()
    return None


@router.get("/summary", response_model=DailyNutritionSummary)
def get_daily_nutrition_summary(
    log_date: Optional[date] = Query(None, description="Date for summary"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_date = log_date or date.today()
    profile = current_user.profile

    logs = (
        db.query(NutritionLog)
        .filter(NutritionLog.user_id == current_user.id, NutritionLog.date == target_date)
        .all()
    )

    cals = sum(l.total_calories for l in logs)
    pro = sum(l.total_protein_g for l in logs)
    carbs = sum(l.total_carbs_g for l in logs)
    fat = sum(l.total_fat_g for l in logs)

    target_cal = profile.target_calories if (profile and profile.target_calories) else 2200
    target_pro = profile.target_protein_g if (profile and profile.target_protein_g) else 140.0
    target_carbs = profile.target_carbs_g if (profile and profile.target_carbs_g) else 240.0
    target_fat = profile.target_fat_g if (profile and profile.target_fat_g) else 65.0

    return DailyNutritionSummary(
        date=target_date,
        calories_consumed=round(cals, 1),
        protein_consumed_g=round(pro, 1),
        carbs_consumed_g=round(carbs, 1),
        fat_consumed_g=round(fat, 1),
        target_calories=target_cal,
        target_protein_g=target_pro,
        target_carbs_g=target_carbs,
        target_fat_g=target_fat,
        logs=[NutritionLogResponse.model_validate(l) for l in logs]
    )
