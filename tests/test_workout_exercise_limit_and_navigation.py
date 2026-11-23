import pytest
from frontend.navigation import NAV_OPTIONS, PAGE_ALIASES


def test_navigation_options_and_aliases():
    """Verify that all navigation options and semantic page aliases resolve correctly."""
    assert "Dashboard" in NAV_OPTIONS
    assert "AI Fitness Assistant" in NAV_OPTIONS
    assert "Workout Planner" in NAV_OPTIONS
    assert "Exercise Library" in NAV_OPTIONS
    assert "Nutrition Tracker" in NAV_OPTIONS
    assert "Body Progress" in NAV_OPTIONS
    assert "User Profile" in NAV_OPTIONS

    # Check aliases
    expected_aliases = {
        "AI Coach": "AI Fitness Assistant",
        "Indian Diet Planner": "Nutrition Tracker",
        "Fitness Guides": "Exercise Library",
        "Profile & Tracking": "Body Progress",
        "Profile": "User Profile",
        "Tracking": "Body Progress"
    }
    for alias, target in expected_aliases.items():
        assert alias in PAGE_ALIASES
        assert PAGE_ALIASES[alias] == target
        assert target in NAV_OPTIONS


@pytest.mark.parametrize("exercise_count", [1, 3, 7, 10, 20, 50])
def test_create_and_persist_workout_plans_with_various_counts(client, auth_headers, exercise_count):
    """
    Verify plans containing different exercise counts (1, 3, 7, 10, 20, and 50 exercises).
    Ensures flexible support up to the maximum 50-exercise limit, and all selected
    exercises persist after saving and reopening.
    """
    # 1. Fetch available exercises from the library
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    assert ex_res.status_code == 200
    all_exercises = ex_res.json()
    assert len(all_exercises) >= exercise_count, f"Exercise library must contain at least {exercise_count} exercises"

    selected_exercises = all_exercises[:exercise_count]
    exercises_payload = [
        {
            "exercise_id": ex["id"],
            "sets": 3 + (i % 3),
            "reps": 8 + (i % 5),
            "rest_seconds": 60 + ((i % 4) * 15),
            "order_index": i + 1
        }
        for i, ex in enumerate(selected_exercises)
    ]

    plan_title = f"Plan with {exercise_count} Exercises"
    plan_payload = {
        "title": plan_title,
        "description": f"Custom flexible training plan containing exactly {exercise_count} distinct exercises.",
        "goal": "General Fitness",
        "difficulty": "Intermediate",
        "exercises": exercises_payload
    }

    # 2. Save plan (POST)
    create_res = client.post("/api/v1/workouts/plans", json=plan_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created_plan = create_res.json()
    assert created_plan["title"] == plan_title
    assert len(created_plan["exercises"]) == exercise_count

    plan_id = created_plan["id"]

    # 3. Reopen / Retrieve plan directly by ID (GET)
    get_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert get_res.status_code == 200
    retrieved_plan = get_res.json()
    assert retrieved_plan["id"] == plan_id
    assert len(retrieved_plan["exercises"]) == exercise_count

    # 4. Verify all exercise IDs and order indices persist accurately
    expected_ids = [ex["id"] for ex in selected_exercises]
    persisted_ids = [item["exercise_id"] for item in retrieved_plan["exercises"]]
    assert persisted_ids == expected_ids

    persisted_order = [item["order_index"] for item in retrieved_plan["exercises"]]
    assert persisted_order == list(range(1, exercise_count + 1))


@pytest.mark.parametrize("update_count", [1, 3, 7, 10, 20, 50])
def test_update_workout_plan_with_various_counts(client, auth_headers, update_count):
    """
    Verify updating an existing workout plan with 1, 3, 7, 10, 20, and 50 exercises.
    Ensures full replacement and persistence of flexible exercise counts up to 50.
    """
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    assert ex_res.status_code == 200
    all_exercises = ex_res.json()
    assert len(all_exercises) >= update_count

    # 1. Create a base plan with 2 exercises
    base_plan_payload = {
        "title": "Base Plan Before Update",
        "goal": "Fitness",
        "difficulty": "Beginner",
        "exercises": [
            {"exercise_id": all_exercises[0]["id"], "sets": 3, "reps": 10, "rest_seconds": 60, "order_index": 1},
            {"exercise_id": all_exercises[1]["id"], "sets": 3, "reps": 10, "rest_seconds": 60, "order_index": 2}
        ]
    }
    create_res = client.post("/api/v1/workouts/plans", json=base_plan_payload, headers=auth_headers)
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]

    # 2. Update plan to update_count exercises (1, 3, 7, 10, 20, or 50)
    target_exercises = all_exercises[:update_count]
    updated_payload = {
        "title": f"Updated Plan with {update_count} Exercises",
        "description": f"Updated plan featuring {update_count} exercises.",
        "goal": "Hypertrophy",
        "difficulty": "Intermediate",
        "exercises": [
            {
                "exercise_id": ex["id"],
                "sets": 4,
                "reps": 12,
                "rest_seconds": 75,
                "order_index": idx + 1
            }
            for idx, ex in enumerate(target_exercises)
        ]
    }
    update_res = client.put(f"/api/v1/workouts/plans/{plan_id}", json=updated_payload, headers=auth_headers)
    assert update_res.status_code == 200
    updated_plan = update_res.json()
    assert updated_plan["title"] == f"Updated Plan with {update_count} Exercises"
    assert len(updated_plan["exercises"]) == update_count

    # 3. Reopen / Retrieve plan directly and verify persistence
    get_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert get_res.status_code == 200
    reopened = get_res.json()
    assert reopened["id"] == plan_id
    assert len(reopened["exercises"]) == update_count
    persisted_ids = [item["exercise_id"] for item in reopened["exercises"]]
    assert persisted_ids == [ex["id"] for ex in target_exercises]


def test_update_workout_plan_resizing(client, auth_headers):
    """Test modifying/updating an existing workout plan across varying exercise counts (1 -> 50 -> 3)."""
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_exercises = ex_res.json()
    assert len(all_exercises) >= 50

    # Start with 1 exercise
    initial_plan = {
        "title": "Minimalist Single Exercise Plan",
        "goal": "Strength",
        "difficulty": "Beginner",
        "exercises": [
            {"exercise_id": all_exercises[0]["id"], "sets": 5, "reps": 5, "rest_seconds": 180, "order_index": 1}
        ]
    }
    create_res = client.post("/api/v1/workouts/plans", json=initial_plan, headers=auth_headers)
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]

    # Expand to 50 exercises
    expanded_payload = {
        "title": "Expanded Plan with 50 Exercises",
        "goal": "Hypertrophy",
        "difficulty": "Advanced",
        "exercises": [
            {"exercise_id": all_exercises[i]["id"], "sets": 3, "reps": 12, "rest_seconds": 60, "order_index": i + 1}
            for i in range(50)
        ]
    }
    update_res = client.put(f"/api/v1/workouts/plans/{plan_id}", json=expanded_payload, headers=auth_headers)
    assert update_res.status_code == 200
    updated_plan = update_res.json()
    assert updated_plan["title"] == "Expanded Plan with 50 Exercises"
    assert len(updated_plan["exercises"]) == 50

    # Reopen and verify persistence of all 50
    reopen_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert reopen_res.status_code == 200
    assert len(reopen_res.json()["exercises"]) == 50

    # Downsize to 3 exercises
    downsized_payload = {
        "title": "Downsized Plan with 3 Exercises",
        "goal": "Strength",
        "difficulty": "Intermediate",
        "exercises": [
            {"exercise_id": all_exercises[i]["id"], "sets": 4, "reps": 8, "rest_seconds": 90, "order_index": i + 1}
            for i in range(3)
        ]
    }
    downsize_res = client.put(f"/api/v1/workouts/plans/{plan_id}", json=downsized_payload, headers=auth_headers)
    assert downsize_res.status_code == 200
    downsized_plan = downsize_res.json()
    assert downsized_plan["title"] == "Downsized Plan with 3 Exercises"
    assert len(downsized_plan["exercises"]) == 3

    # Reopen and verify persistence of downsized list
    reopen_downsized = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert reopen_downsized.status_code == 200
    assert len(reopen_downsized.json()["exercises"]) == 3


@pytest.mark.parametrize("log_count", [1, 3, 7, 10, 20, 50])
def test_record_and_retrieve_workout_logs_with_flexible_counts(client, auth_headers, log_count):
    """Test logging and retrieving completed workouts with 1, 3, 7, 10, 20, and 50 exercises."""
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_exercises = ex_res.json()
    assert len(all_exercises) >= log_count
    selected = all_exercises[:log_count]

    logged_exercises = [
        {
            "exercise_id": ex["id"],
            "sets_completed": 3,
            "reps_completed": 10 + (i % 5),
            "weight_kg": 20.0 + (i * 2.5),
            "notes": f"Exercise {i+1} completed"
        }
        for i, ex in enumerate(selected)
    ]

    log_payload = {
        "title": f"Training Log with {log_count} Exercises",
        "notes": f"Session containing {log_count} completed exercise movements.",
        "duration_minutes": 30 + min(log_count * 2, 180),
        "completed": True,
        "logged_exercises": logged_exercises
    }

    post_res = client.post("/api/v1/workouts/logs", json=log_payload, headers=auth_headers)
    assert post_res.status_code == 201
    created_log = post_res.json()
    assert created_log["title"] == f"Training Log with {log_count} Exercises"
    assert len(created_log["logged_exercises"]) == log_count

    # Retrieve all logs and verify persistence
    get_res = client.get("/api/v1/workouts/logs", headers=auth_headers)
    assert get_res.status_code == 200
    matching = [l for l in get_res.json() if l["id"] == created_log["id"]][0]
    assert len(matching["logged_exercises"]) == log_count


def test_workout_plan_maximum_50_limit_rejection(client, auth_headers):
    """Verify that attempting to create a plan with 51 exercises is rejected with 422 or 400."""
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_exercises = ex_res.json()
    assert len(all_exercises) >= 50

    # 51 exercises payload
    ex_51 = [
        {"exercise_id": all_exercises[i % len(all_exercises)]["id"], "sets": 3, "reps": 10, "rest_seconds": 60, "order_index": i + 1}
        for i in range(51)
    ]

    payload = {
        "title": "Over-the-limit 51 Exercise Plan",
        "goal": "Endurance",
        "difficulty": "Advanced",
        "exercises": ex_51
    }

    create_res = client.post("/api/v1/workouts/plans", json=payload, headers=auth_headers)
    assert create_res.status_code in (400, 422), f"Expected 400 or 422 but got {create_res.status_code}"


def test_workout_plan_user_ownership_and_authorization(client, auth_headers):
    """Verify that users can only access, edit, and delete their own workout plans."""
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_exercises = ex_res.json()

    # User 1 creates a plan
    p_res = client.post("/api/v1/workouts/plans", json={
        "title": "User 1 Private Plan",
        "goal": "Strength",
        "difficulty": "Intermediate",
        "exercises": [{"exercise_id": all_exercises[0]["id"], "sets": 3, "reps": 10, "rest_seconds": 60, "order_index": 1}]
    }, headers=auth_headers)
    assert p_res.status_code == 201
    user1_plan_id = p_res.json()["id"]

    # Create User 2
    user2_reg = client.post("/api/v1/auth/register", json={
        "email": "user2_auth_test@example.com",
        "username": "user2_auth",
        "full_name": "User Two",
        "password": "Password123!"
    })
    assert user2_reg.status_code == 201
    user2_login = client.post("/api/v1/auth/login", json={
        "username": "user2_auth",
        "password": "Password123!"
    })
    assert user2_login.status_code == 200
    user2_headers = {"Authorization": f"Bearer {user2_login.json()['access_token']}"}

    # User 2 attempts to get User 1's plan
    u2_get = client.get(f"/api/v1/workouts/plans/{user1_plan_id}", headers=user2_headers)
    assert u2_get.status_code == 404

    # User 2 attempts to update User 1's plan
    u2_put = client.put(f"/api/v1/workouts/plans/{user1_plan_id}", json={"title": "Hacked Title"}, headers=user2_headers)
    assert u2_put.status_code == 404

    # User 2 attempts to delete User 1's plan
    u2_del = client.delete(f"/api/v1/workouts/plans/{user1_plan_id}", headers=user2_headers)
    assert u2_del.status_code == 404
