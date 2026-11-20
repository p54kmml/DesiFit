from datetime import datetime as py_datetime, date as py_date
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ==========================================
# AUTH & USER SCHEMAS
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    is_onboarded: bool = False


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    created_at: py_datetime

    model_config = ConfigDict(from_attributes=True)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    email_sent: bool = False
    dev_reset_link: Optional[str] = None
    dev_token: Optional[str] = None
    dev_note: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


class VerifyResetTokenResponse(BaseModel):
    valid: bool
    message: Optional[str] = None


# ==========================================
# USER PROFILE SCHEMAS
# ==========================================

class UserProfileBase(BaseModel):
    is_onboarded: bool = False
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    fitness_experience: Optional[str] = None
    fitness_goal: Optional[str] = None
    dietary_preference: Optional[str] = None
    activity_level: Optional[str] = None
    target_calories: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    workout_frequency_days: Optional[int] = None
    preferred_split: Optional[str] = None
    custom_split_details: Optional[str] = None


class UserProfileUpdate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    fitness_experience: Optional[str] = None
    fitness_goal: Optional[str] = None
    dietary_preference: Optional[str] = None
    activity_level: Optional[str] = None
    target_calories: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    workout_frequency_days: Optional[int] = None
    preferred_split: Optional[str] = None
    custom_split_details: Optional[str] = None


class OnboardingRequest(BaseModel):
    age: int = Field(..., ge=12, le=120)
    gender: str = Field(..., description="Sex/Gender: Male, Female")
    height_cm: float = Field(..., ge=80.0, le=260.0)
    current_weight_kg: float = Field(..., ge=25.0, le=350.0)
    target_weight_kg: float = Field(..., ge=25.0, le=350.0)
    fitness_experience: str = Field(..., description="Beginner, Intermediate, Advanced")
    fitness_goal: str = Field(..., description="Muscle Gain, Fat Loss, Maintenance, Endurance, Strength")
    dietary_preference: str = Field(..., description="Vegetarian, Non-Vegetarian, Vegan, Eggetarian, Jain")
    activity_level: str = Field(..., description="Sedentary, Lightly Active, Moderately Active, Very Active, Extremely Active")
    target_calories: Optional[int] = None
    target_protein_g: Optional[float] = None
    target_carbs_g: Optional[float] = None
    target_fat_g: Optional[float] = None
    workout_frequency_days: Optional[int] = Field(None, ge=1, le=7)
    preferred_split: Optional[str] = None
    custom_split_details: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    id: int
    user_id: int
    updated_at: py_datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# EXERCISE SCHEMAS
# ==========================================

class ExerciseBase(BaseModel):
    name: str
    muscle_group: str
    equipment: Optional[str] = "Gym Equipment"
    difficulty: Optional[str] = "Intermediate"
    instructions: Optional[str] = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseResponse(ExerciseBase):
    id: int
    is_custom: bool
    created_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# WORKOUT PLAN SCHEMAS
# ==========================================

class WorkoutPlanExerciseCreate(BaseModel):
    exercise_id: int
    sets: int = 3
    reps: int = 12
    rest_seconds: int = 60
    order_index: int = 0


class WorkoutPlanExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    sets: int
    reps: int
    rest_seconds: int
    order_index: int
    exercise: ExerciseResponse

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanCreate(BaseModel):
    title: str
    description: Optional[str] = None
    goal: Optional[str] = None
    difficulty: Optional[str] = None
    exercises: List[WorkoutPlanExerciseCreate] = []


class WorkoutPlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    goal: Optional[str]
    difficulty: Optional[str]
    created_at: py_datetime
    exercises: List[WorkoutPlanExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# WORKOUT LOG SCHEMAS
# ==========================================

class WorkoutLogExerciseCreate(BaseModel):
    exercise_id: int
    sets_completed: int = 3
    reps_completed: int = 10
    weight_kg: float = 0.0
    notes: Optional[str] = None


class WorkoutLogExerciseResponse(BaseModel):
    id: int
    exercise_id: int
    sets_completed: int
    reps_completed: int
    weight_kg: float
    notes: Optional[str]
    exercise: ExerciseResponse

    model_config = ConfigDict(from_attributes=True)


class WorkoutLogCreate(BaseModel):
    workout_plan_id: Optional[int] = None
    title: str
    notes: Optional[str] = None
    duration_minutes: int = 45
    date: Optional[py_date] = None
    completed: bool = True
    logged_exercises: List[WorkoutLogExerciseCreate] = []


class WorkoutLogResponse(BaseModel):
    id: int
    user_id: int
    workout_plan_id: Optional[int]
    title: str
    notes: Optional[str]
    duration_minutes: int
    date: py_date
    completed: bool
    created_at: py_datetime
    logged_exercises: List[WorkoutLogExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# FOOD & NUTRITION SCHEMAS
# ==========================================

class FoodItemBase(BaseModel):
    name: str
    serving_size: str = "100g"
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: Optional[float] = 0.0
    is_desi_special: Optional[bool] = False


class FoodItemCreate(FoodItemBase):
    pass


class FoodItemResponse(FoodItemBase):
    id: int
    is_custom: bool
    created_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class NutritionLogCreate(BaseModel):
    food_item_id: int
    meal_type: str # Breakfast, Lunch, Dinner, Snacks
    servings: float = 1.0
    date: Optional[py_date] = None


class NutritionLogResponse(BaseModel):
    id: int
    user_id: int
    food_item_id: int
    meal_type: str
    servings: float
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    date: py_date
    created_at: py_datetime
    food_item: FoodItemResponse

    model_config = ConfigDict(from_attributes=True)


class DailyNutritionSummary(BaseModel):
    date: py_date
    calories_consumed: float
    protein_consumed_g: float
    carbs_consumed_g: float
    fat_consumed_g: float
    target_calories: int
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    logs: List[NutritionLogResponse] = []


# ==========================================
# BODY PROGRESS SCHEMAS
# ==========================================

class BodyMeasurementCreate(BaseModel):
    weight_kg: float
    chest_cm: Optional[float] = None
    waist_cm: Optional[float] = None
    arm_cm: Optional[float] = None
    thigh_cm: Optional[float] = None
    notes: Optional[str] = None
    date: Optional[py_date] = None


class BodyMeasurementResponse(BaseModel):
    id: int
    user_id: int
    weight_kg: float
    chest_cm: Optional[float]
    waist_cm: Optional[float]
    arm_cm: Optional[float]
    thigh_cm: Optional[float]
    notes: Optional[str]
    date: py_date
    created_at: py_datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# AI CHAT SCHEMAS
# ==========================================

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    workout_frequency_days: Optional[int] = None
    preferred_split: Optional[str] = None


class AIConversationMessage(BaseModel):
    id: int
    role: str
    content: str
    is_fallback: bool
    created_at: py_datetime

    model_config = ConfigDict(from_attributes=True)


class AIChatResponse(BaseModel):
    reply: str
    is_fallback: bool
    api_connected: bool
    system_notes: Optional[str] = None


# ==========================================
# DASHBOARD STATS SCHEMAS
# ==========================================

class WeeklyActivityItem(BaseModel):
    day: str
    date: str
    workouts_completed: int
    total_duration_minutes: int


class DashboardStatsResponse(BaseModel):
    full_name: str
    is_onboarded: bool = False
    fitness_goal: str
    current_weight_kg: float
    target_weight_kg: float
    daily_calorie_target: int
    daily_protein_target: float
    today_calories_consumed: float
    today_protein_consumed: float
    total_workouts_completed: int
    this_week_workouts_count: int
    weekly_activity: List[WeeklyActivityItem]
    recent_workouts: List[WorkoutLogResponse]
    recent_measurements: List[BodyMeasurementResponse]
