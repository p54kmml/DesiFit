import pytest
from fastapi.testclient import TestClient
from backend.services.workout_generator import (
    build_personalized_workout_plan,
    count_training_days,
    extract_requested_training_days
)
from backend.models import User, UserProfile


def test_exact_6_day_split_generation():
    """Verifies that the requested 6-day split is generated with exact muscle groups and only Day 7 as Rest."""
    user = User(id=101, username="test_split_user", full_name="Aarav Patel")
    profile = UserProfile(
        user_id=101,
        fitness_goal="Muscle Gain",
        fitness_experience="Intermediate",
        workout_frequency_days=6,
        preferred_split="Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)",
        custom_split_details=(
            "1. Chest + Triceps\n"
            "2. Back + Biceps\n"
            "3. Legs\n"
            "4. Chest + Shoulders\n"
            "5. Arms (Biceps + Triceps)\n"
            "6. Back + Shoulders\n"
            "7. Rest"
        )
    )
    user.profile = profile

    plan = build_personalized_workout_plan(6, user, profile)

    # 1. Exact 6-day split is generated
    assert "Day 1: Chest + Triceps" in plan
    assert "Day 2: Back + Biceps" in plan
    assert "Day 3: Legs" in plan
    assert "Day 4: Chest + Shoulders" in plan
    assert "Day 5: Arms (Biceps + Triceps)" in plan
    assert "Day 6: Back + Shoulders" in plan
    assert "Day 7: Dedicated Rest" in plan or "Day 7: Rest" in plan

    # 2. Only Day 7 is the rest day
    active_days = count_training_days(plan)
    assert active_days == 6, f"Expected 6 active training days, got {active_days}"
    assert "Only Day 7 is the rest day" in plan or "Only Day 7" in plan

    # Days 1 through 6 must not be rest days
    for d in range(1, 7):
        # Must have active exercises
        assert f"Day {d}:" in plan
        assert "sets ×" in plan

    # 3. Muscle groups are assigned correctly
    # Day 1: Chest + Triceps
    assert "Bench Press" in plan
    assert "Triceps" in plan

    # Day 2: Back + Biceps
    assert "Bent-Over Row" in plan or "Deadlift" in plan
    assert "Bicep Curl" in plan

    # Day 3: Legs
    assert "Squats" in plan
    assert "Deadlift" in plan or "Leg Press" in plan or "Calf" in plan

    # Day 4: Chest + Shoulders
    assert "Military Press" in plan or "Lateral Raises" in plan

    # Day 5: Arms (Biceps + Triceps)
    assert "Hammer Curls" in plan or "Bicep" in plan
    assert "Skull Crushers" in plan or "Pushdown" in plan

    # Day 6: Back + Shoulders
    assert "Military Press" in plan or "Lateral Raises" in plan or "Face Pulls" in plan


def test_4_day_request_still_works_when_explicitly_requested():
    """Verifies that an explicit 4-day request still produces exactly 4 training days."""
    user = User(id=102, username="test_4day_user", full_name="Vikram Singh")
    profile = UserProfile(
        user_id=102,
        fitness_goal="Strength",
        fitness_experience="Intermediate",
        workout_frequency_days=6  # User usually trains 6 days, but asks for 4
    )
    user.profile = profile

    # Explicitly requesting 4 days
    plan = build_personalized_workout_plan(4, user, profile)
    active_days = count_training_days(plan)
    assert active_days == 4
    assert "Day 1:" in plan
    assert "Day 2:" in plan
    assert "Day 3:" in plan
    assert "Day 4:" in plan
    assert "Day 5:" not in plan or "Rest" in plan


def test_user_preferences_persistence_in_sqlite(client: TestClient):
    """Verifies user workout preferences persist in SQLite and survive across sessions."""
    # 1. Register a fresh user
    reg = client.post("/api/v1/auth/register", json={
        "email": "split_persist@desifit.in",
        "username": "split_persist_user",
        "full_name": "Split Tester",
        "password": "Password123"
    })
    assert reg.status_code == 201

    login = client.post("/api/v1/auth/login", json={
        "username": "split_persist_user",
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Save user workout preferences
    update_payload = {
        "age": 27,
        "gender": "Male",
        "height_cm": 178.0,
        "current_weight_kg": 76.0,
        "target_weight_kg": 72.0,
        "fitness_experience": "Intermediate",
        "fitness_goal": "Muscle Gain",
        "dietary_preference": "Non-Vegetarian",
        "activity_level": "Very Active",
        "workout_frequency_days": 6,
        "preferred_split": "Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)",
        "custom_split_details": (
            "1. Chest + Triceps\n"
            "2. Back + Biceps\n"
            "3. Legs\n"
            "4. Chest + Shoulders\n"
            "5. Arms (Biceps + Triceps)\n"
            "6. Back + Shoulders\n"
            "7. Rest"
        )
    }
    update_res = client.put("/api/v1/profile", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    prof = update_res.json()
    assert prof["workout_frequency_days"] == 6
    assert "Chest+Tri" in prof["preferred_split"]

    # 3. Simulate new application session / restart by fetching from fresh request
    fetch_res = client.get("/api/v1/profile", headers=headers)
    assert fetch_res.status_code == 200
    persisted = fetch_res.json()
    assert persisted["workout_frequency_days"] == 6
    assert "Chest+Tri" in persisted["preferred_split"]
    assert "Chest + Triceps" in persisted["custom_split_details"]

    # 4. Now verify AI assistant generates the 6-day split without repeating "6 days" in query
    chat_res = client.post("/api/v1/ai/chat", json={
        "message": "Give me my personalized workout split"
    }, headers=headers)
    assert chat_res.status_code == 200
    reply = chat_res.json()["reply"]

    # Must generate the 6-day split according to saved preferences
    assert "Day 1: Chest + Triceps" in reply
    assert "Day 2: Back + Biceps" in reply
    assert "Day 3: Legs" in reply
    assert "Day 4: Chest + Shoulders" in reply
    assert "Day 5: Arms" in reply
    assert "Day 6: Back + Shoulders" in reply
    assert "Day 7" in reply
    assert "Only Day 7 is the rest day" in reply or "Day 7: Dedicated Rest" in reply
    # Must NOT generate the 4-day Upper/Lower split!
    assert "Upper / Lower" not in reply or "4-Day" not in reply


def test_custom_arms_day_does_not_duplicate_biceps_or_triceps():
    """A combined arms day should contain one balanced block, not duplicate blocks."""
    from backend.services.workout_generator import generate_day_exercises

    day = generate_day_exercises("Arms (Biceps + Triceps)", "6-10 reps", "10-12 reps", "90-120s", "60-75s")
    exercises = day["exercises"]
    assert exercises.count("Standing Barbell Bicep Curl") == 1
    assert exercises.count("Incline Dumbbell Hammer Curls") == 1
    assert exercises.count("Preacher EZ-Bar Curls") == 1
    assert exercises.count("Skull Crushers") == 1
    assert exercises.count("Triceps Cable Rope Pushdown") == 1


def test_profile_training_frequency_does_not_override_nutrition_question():
    """Saved workout frequency must not turn nutrition questions into workout plans."""
    from backend.services.ai_service import generate_rule_based_response

    user = User(id=103, username="nutrition_test", full_name="Nutrition Tester")
    profile = UserProfile(
        user_id=103, fitness_goal="Muscle Gain", dietary_preference="Vegetarian",
        workout_frequency_days=6, current_weight_kg=70, target_calories=2400, target_protein_g=130
    )
    user.profile = profile
    reply = generate_rule_based_response("How can I increase my daily protein?", user, profile)
    assert "Recommended Protein Sources" in reply
    assert "Day 1:" not in reply
