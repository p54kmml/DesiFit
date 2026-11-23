from datetime import datetime, date, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    Date,
    ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    workout_plans = relationship("WorkoutPlan", back_populates="user", cascade="all, delete-orphan")
    workout_logs = relationship("WorkoutLog", back_populates="user", cascade="all, delete-orphan")
    nutrition_logs = relationship("NutritionLog", back_populates="user", cascade="all, delete-orphan")
    body_measurements = relationship("BodyMeasurement", back_populates="user", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("AccountVerificationToken", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_onboarded = Column(Boolean, default=False, nullable=False)
    
    # Biometrics (No hardcoded personal defaults for other users)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    height_cm = Column(Float, nullable=True)
    current_weight_kg = Column(Float, nullable=True)
    target_weight_kg = Column(Float, nullable=True)
    fitness_experience = Column(String(50), nullable=True)
    fitness_goal = Column(String(100), nullable=True)
    dietary_preference = Column(String(100), nullable=True)
    activity_level = Column(String(100), nullable=True)
    
    # Nutrition targets
    target_calories = Column(Integer, nullable=True)
    target_protein_g = Column(Float, nullable=True)
    target_carbs_g = Column(Float, nullable=True)
    target_fat_g = Column(Float, nullable=True)

    # Workout & Training Preferences
    workout_frequency_days = Column(Integer, nullable=True)
    preferred_split = Column(String(150), nullable=True)
    custom_split_details = Column(Text, nullable=True)
    
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="profile")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    muscle_group = Column(String(100), index=True, nullable=False) # Chest, Back, Shoulders, Biceps, Triceps, Legs, Abs
    equipment = Column(String(100), nullable=True, default="Gym Equipment")
    difficulty = Column(String(50), nullable=True, default="Intermediate")
    instructions = Column(Text, nullable=True)
    is_custom = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    plan_associations = relationship("WorkoutPlanExercise", back_populates="exercise", cascade="all, delete-orphan")
    log_associations = relationship("WorkoutLogExercise", back_populates="exercise")


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="workout_plans")
    exercises = relationship("WorkoutPlanExercise", back_populates="workout_plan", cascade="all, delete-orphan")
    logs = relationship("WorkoutLog", back_populates="plan")


class WorkoutPlanExercise(Base):
    __tablename__ = "workout_plan_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets = Column(Integer, default=3)
    reps = Column(Integer, default=12)
    rest_seconds = Column(Integer, default=60)
    order_index = Column(Integer, default=0)

    workout_plan = relationship("WorkoutPlan", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="plan_associations")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workout_plan_id = Column(Integer, ForeignKey("workout_plans.id"), nullable=True)
    title = Column(String(200), nullable=False)
    notes = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=45)
    date = Column(Date, default=date.today, nullable=False)
    completed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="workout_logs")
    plan = relationship("WorkoutPlan", back_populates="logs")
    logged_exercises = relationship("WorkoutLogExercise", back_populates="workout_log", cascade="all, delete-orphan")


class WorkoutLogExercise(Base):
    __tablename__ = "workout_log_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_log_id = Column(Integer, ForeignKey("workout_logs.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets_completed = Column(Integer, default=3)
    reps_completed = Column(Integer, default=10)
    weight_kg = Column(Float, default=0.0)
    notes = Column(String(255), nullable=True)

    workout_log = relationship("WorkoutLog", back_populates="logged_exercises")
    exercise = relationship("Exercise", back_populates="log_associations")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), index=True, nullable=False)
    serving_size = Column(String(100), default="100g")
    calories = Column(Float, nullable=False)
    protein_g = Column(Float, nullable=False)
    carbs_g = Column(Float, nullable=False)
    fat_g = Column(Float, nullable=False)
    fiber_g = Column(Float, default=0.0)
    is_desi_special = Column(Boolean, default=False)
    is_custom = Column(Boolean, default=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    nutrition_logs = relationship("NutritionLog", back_populates="food_item")


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    meal_type = Column(String(50), nullable=False) # Breakfast, Lunch, Dinner, Snacks
    servings = Column(Float, default=1.0)
    total_calories = Column(Float, nullable=False)
    total_protein_g = Column(Float, nullable=False)
    total_carbs_g = Column(Float, nullable=False)
    total_fat_g = Column(Float, nullable=False)
    date = Column(Date, default=date.today, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="nutrition_logs")
    food_item = relationship("FoodItem", back_populates="nutrition_logs")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    chest_cm = Column(Float, nullable=True)
    waist_cm = Column(Float, nullable=True)
    arm_cm = Column(Float, nullable=True)
    thigh_cm = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    date = Column(Date, default=date.today, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="body_measurements")


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False) # user or assistant
    content = Column(Text, nullable=False)
    is_fallback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="ai_conversations")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")


class AccountVerificationToken(Base):
    __tablename__ = "account_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    user = relationship("User", back_populates="verification_tokens")
