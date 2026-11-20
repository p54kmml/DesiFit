import pytest
from backend.models import User, UserProfile
from backend.services.workout_generator import (
    extract_requested_training_days,
    count_training_days,
    build_personalized_workout_plan,
    validate_and_enforce_workout_days
)


@pytest.fixture
def test_user():
    user = User(id=99, username="rohit_fit", full_name="Rohit Kumar")
    profile = UserProfile(
        user_id=99,
        fitness_goal="Muscle Gain",
        fitness_experience="Intermediate",
        current_weight_kg=74.0
    )
    user.profile = profile
    return user


def test_extract_requested_training_days():
    assert extract_requested_training_days("Make me a 6-day workout") == 6
    assert extract_requested_training_days("Can you give me a 6 day split?") == 6
    assert extract_requested_training_days("I want to train 5 days a week") == 5
    assert extract_requested_training_days("Give me a 4-day workout") == 4
    assert extract_requested_training_days("I need a 7 day routine") == 7
    assert extract_requested_training_days("3 days workout plan") == 3
    assert extract_requested_training_days("Design a six-day workout split for muscle gain") == 6
    assert extract_requested_training_days("What is the best protein diet?") is None


def test_generate_6_day_workout_plan(test_user):
    plan = build_personalized_workout_plan(6, test_user, test_user.profile)
    
    # 1. Must contain Rohit Kumar
    assert "Rohit Kumar" in plan
    
    # 2. Must contain exactly 6 active training days
    active_days = count_training_days(plan)
    assert active_days == 6, f"Expected 6 active training days, got {active_days}"
    
    # 3. Must verify days 1 through 6 are present
    for d in range(1, 7):
        assert f"Day {d}:" in plan
        
    # 4. Must verify required workout components
    assert "Target Muscles" in plan
    assert "Rest:" in plan
    assert "sets ×" in plan
    
    # 5. Must include recovery day
    assert "Rest & Active Recovery" in plan
    assert "6 Active Training Days" in plan


def test_generate_5_day_workout_plan(test_user):
    plan = build_personalized_workout_plan(5, test_user, test_user.profile)
    active_days = count_training_days(plan)
    assert active_days == 5, f"Expected 5 active training days, got {active_days}"
    for d in range(1, 6):
        assert f"Day {d}:" in plan
    assert "5 Active Training Days" in plan


def test_generate_4_day_workout_plan(test_user):
    plan = build_personalized_workout_plan(4, test_user, test_user.profile)
    active_days = count_training_days(plan)
    assert active_days == 4, f"Expected 4 active training days, got {active_days}"
    for d in range(1, 5):
        assert f"Day {d}:" in plan
    assert "4 Active Training Days" in plan


def test_generate_7_day_workout_plan_includes_recovery_clarification(test_user):
    plan = build_personalized_workout_plan(7, test_user, test_user.profile)
    # Must clarify training days vs recovery
    assert "Recovery Clarification" in plan or "Active Recovery" in plan
    assert "Day 7:" in plan


def test_validator_enforces_requested_days(test_user):
    # Simulated flawed model output that generated a 4-day split when 6 days were requested
    flawed_output = """
    Here is your 4-day split:
    ### Day 1: Chest
    Bench press 3x8
    ### Day 2: Back
    Rows 3x8
    ### Day 3: Legs
    Squats 3x8
    ### Day 4: Shoulders
    Press 3x8
    """
    
    # User asked for 6 days
    validated = validate_and_enforce_workout_days(flawed_output, 6, test_user, test_user.profile)
    
    # Validator must have corrected the plan to exactly 6 days
    active_days = count_training_days(validated)
    assert active_days == 6
    assert "Day 6:" in validated
