from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserProfile, BodyMeasurement
from backend.schemas import UserProfileResponse, UserProfileUpdate, OnboardingRequest
from backend.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["User Profile"])


def calculate_recommended_macros(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity_level: str,
    goal: str
):
    """Calculates scientifically sound daily calorie and macro targets using Mifflin-St Jeor formula."""
    # Biological sex-based BMR calculation
    if gender.lower() == "female":
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0
    else: # Male / Default
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0

    activity_multipliers = {
        "Sedentary": 1.2,
        "Lightly Active": 1.375,
        "Moderately Active": 1.55,
        "Very Active": 1.725,
        "Extremely Active": 1.9
    }
    multiplier = activity_multipliers.get(activity_level, 1.4)
    tdee = bmr * multiplier

    # Adjust for specific goal
    goal_lower = goal.lower()
    if "fat loss" in goal_lower or "cut" in goal_lower or "loss" in goal_lower:
        calories = max(1300, int(tdee - 450))
        protein_g = round(weight_kg * 2.0, 1)
    elif "muscle" in goal_lower or "bulk" in goal_lower:
        calories = int(tdee + 300)
        protein_g = round(weight_kg * 2.0, 1)
    elif "strength" in goal_lower:
        calories = int(tdee + 200)
        protein_g = round(weight_kg * 1.8, 1)
    elif "endurance" in goal_lower:
        calories = int(tdee + 150)
        protein_g = round(weight_kg * 1.5, 1)
    else: # Maintenance
        calories = int(tdee)
        protein_g = round(weight_kg * 1.6, 1)

    # Dietary Fats: 25% of total calories (9 kcal/g)
    fat_cals = calories * 0.25
    fat_g = round(fat_cals / 9.0, 1)

    # Remaining calories to Carbs (4 kcal/g)
    protein_cals = protein_g * 4.0
    remaining_cals = max(0, calories - (fat_cals + protein_cals))
    carbs_g = round(remaining_cals / 4.0, 1)

    return calories, protein_g, carbs_g, fat_g


@router.get("", response_model=UserProfileResponse)
def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id, is_onboarded=False)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.post("/onboard", response_model=UserProfileResponse)
def complete_onboarding(
    onboarding_data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processes first-time user onboarding with real user-provided metrics and Mifflin-St Jeor calculation."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    # Calculate optimal nutritional targets if not manually overridden
    if not onboarding_data.target_calories or onboarding_data.target_calories <= 0:
        cals, pro, carbs, fat = calculate_recommended_macros(
            weight_kg=onboarding_data.current_weight_kg,
            height_cm=onboarding_data.height_cm,
            age=onboarding_data.age,
            gender=onboarding_data.gender,
            activity_level=onboarding_data.activity_level,
            goal=onboarding_data.fitness_goal
        )
    else:
        cals = onboarding_data.target_calories
        pro = onboarding_data.target_protein_g or round(onboarding_data.current_weight_kg * 1.8, 1)
        carbs = onboarding_data.target_carbs_g or round((cals * 0.45) / 4.0, 1)
        fat = onboarding_data.target_fat_g or round((cals * 0.25) / 9.0, 1)

    # Set user biometrics
    profile.is_onboarded = True
    profile.age = onboarding_data.age
    profile.gender = onboarding_data.gender
    profile.height_cm = onboarding_data.height_cm
    profile.current_weight_kg = onboarding_data.current_weight_kg
    profile.target_weight_kg = onboarding_data.target_weight_kg
    profile.fitness_experience = onboarding_data.fitness_experience
    profile.fitness_goal = onboarding_data.fitness_goal
    profile.dietary_preference = onboarding_data.dietary_preference
    profile.activity_level = onboarding_data.activity_level
    profile.target_calories = cals
    profile.target_protein_g = pro
    profile.target_carbs_g = carbs
    profile.target_fat_g = fat
    profile.workout_frequency_days = onboarding_data.workout_frequency_days
    profile.preferred_split = onboarding_data.preferred_split
    profile.custom_split_details = onboarding_data.custom_split_details

    # Add initial body measurement record to start their journey
    existing_meas = db.query(BodyMeasurement).filter(BodyMeasurement.user_id == current_user.id).first()
    if not existing_meas:
        init_meas = BodyMeasurement(
            user_id=current_user.id,
            weight_kg=onboarding_data.current_weight_kg,
            notes="Initial profile onboarding weight",
            date=date.today()
        )
        db.add(init_meas)

    db.commit()
    db.refresh(profile)
    return profile


@router.put("", response_model=UserProfileResponse)
def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id, is_onboarded=False)
        db.add(profile)

    update_dict = profile_data.model_dump(exclude_unset=True)

    # Only auto-recalculate macros if the profile has sufficient biometric data to do so meaningfully
    if "target_calories" not in update_dict or update_dict["target_calories"] is None:
        # Gather the best available weight/height/age/gender (new value > current saved > skip)
        eff_weight = update_dict.get("current_weight_kg") or profile.current_weight_kg
        eff_height = update_dict.get("height_cm") or profile.height_cm
        eff_age = update_dict.get("age") or profile.age
        eff_gender = update_dict.get("gender") or profile.gender
        eff_activity = update_dict.get("activity_level") or profile.activity_level
        eff_goal = update_dict.get("fitness_goal") or profile.fitness_goal

        if all([eff_weight, eff_height, eff_age, eff_gender, eff_activity, eff_goal]):
            # All required fields present — safe to calculate personalized macros
            rec_cal, rec_pro, rec_carbs, rec_fat = calculate_recommended_macros(
                weight_kg=eff_weight,
                height_cm=eff_height,
                age=eff_age,
                gender=eff_gender,
                activity_level=eff_activity,
                goal=eff_goal
            )
            update_dict["target_calories"] = rec_cal
            update_dict["target_protein_g"] = rec_pro
            update_dict["target_carbs_g"] = rec_carbs
            update_dict["target_fat_g"] = rec_fat
        else:
            # Insufficient biometric data — do not substitute hardcoded personal fallback values
            update_dict.pop("target_calories", None)
            update_dict.pop("target_protein_g", None)
            update_dict.pop("target_carbs_g", None)
            update_dict.pop("target_fat_g", None)

    for key, value in update_dict.items():
        setattr(profile, key, value)

    # Ensure profile remains marked onboarded if it was updated with metrics
    if profile.current_weight_kg and profile.height_cm:
        profile.is_onboarded = True

    db.commit()
    db.refresh(profile)
    return profile
