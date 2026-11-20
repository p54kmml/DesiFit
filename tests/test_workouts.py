def test_get_exercise_library(client, auth_headers):
    res = client.get("/api/v1/exercises", headers=auth_headers)
    assert res.status_code == 200
    exercises = res.json()
    assert len(exercises) > 0
    # verify muscle groups are present
    muscle_groups = {ex["muscle_group"] for ex in exercises}
    assert "Chest" in muscle_groups
    assert "Back" in muscle_groups
    assert "Legs" in muscle_groups


def test_filter_exercises_by_muscle_group(client, auth_headers):
    res = client.get("/api/v1/exercises?muscle_group=Chest", headers=auth_headers)
    assert res.status_code == 200
    exercises = res.json()
    assert all("Chest" in ex["muscle_group"] for ex in exercises)


def test_create_and_fetch_workout_plan(client, auth_headers):
    # Fetch an exercise
    ex_res = client.get("/api/v1/exercises?muscle_group=Chest", headers=auth_headers)
    ex_id = ex_res.json()[0]["id"]

    plan_payload = {
        "title": "Chest & Tricep Hypertrophy",
        "description": "Mass builder chest focus",
        "goal": "Muscle Gain",
        "difficulty": "Intermediate",
        "exercises": [
            {
                "exercise_id": ex_id,
                "sets": 4,
                "reps": 10,
                "rest_seconds": 90,
                "order_index": 1
            }
        ]
    }
    create_res = client.post("/api/v1/workouts/plans", json=plan_payload, headers=auth_headers)
    assert create_res.status_code == 201
    plan_data = create_res.json()
    assert plan_data["title"] == "Chest & Tricep Hypertrophy"
    assert len(plan_data["exercises"]) == 1

    # Fetch plans list
    list_res = client.get("/api/v1/workouts/plans", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(p["id"] == plan_data["id"] for p in list_res.json())


def test_record_workout_log(client, auth_headers):
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    ex_id = ex_res.json()[0]["id"]

    log_payload = {
        "title": "Morning Push Session",
        "notes": "Felt strong on bench press today",
        "duration_minutes": 50,
        "completed": True,
        "logged_exercises": [
            {
                "exercise_id": ex_id,
                "sets_completed": 3,
                "reps_completed": 12,
                "weight_kg": 60.0,
                "notes": "Solid pump"
            }
        ]
    }
    res = client.post("/api/v1/workouts/logs", json=log_payload, headers=auth_headers)
    assert res.status_code == 201
    log = res.json()
    assert log["title"] == "Morning Push Session"
    assert len(log["logged_exercises"]) == 1
    assert log["logged_exercises"][0]["weight_kg"] == 60.0
