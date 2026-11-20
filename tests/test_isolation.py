import pytest
from fastapi.testclient import TestClient


def create_user(client: TestClient, username: str, email: str):
    reg = client.post("/api/v1/auth/register", json={
        "email": email,
        "username": username,
        "full_name": f"User {username}",
        "password": "Password123"
    })
    assert reg.status_code == 201
    login = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": "Password123"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_shared_builtin_libraries_accessible_to_all_users(client: TestClient):
    auth_a = create_user(client, "user_alpha_lib", "alpha_lib@example.com")
    auth_b = create_user(client, "user_beta_lib", "beta_lib@example.com")

    # Built-in exercises should be visible to both
    res_a = client.get("/api/v1/exercises", headers=auth_a)
    res_b = client.get("/api/v1/exercises", headers=auth_b)
    assert res_a.status_code == 200
    assert res_b.status_code == 200
    names_a = [e["name"] for e in res_a.json()]
    names_b = [e["name"] for e in res_b.json()]
    assert "Barbell Bench Press" in names_a
    assert "Barbell Bench Press" in names_b

    # Built-in food items should be visible to both
    foods_a = client.get("/api/v1/nutrition/foods", headers=auth_a)
    foods_b = client.get("/api/v1/nutrition/foods", headers=auth_b)
    assert foods_a.status_code == 200
    assert foods_b.status_code == 200
    food_names_a = [f["name"] for f in foods_a.json()]
    food_names_b = [f["name"] for f in foods_b.json()]
    assert any("Paneer" in f for f in food_names_a)
    assert any("Paneer" in f for f in food_names_b)


def test_custom_exercise_isolation_between_users(client: TestClient):
    auth_a = create_user(client, "user_alice", "alice@example.com")
    auth_b = create_user(client, "user_bob", "bob@example.com")

    # Alice creates a custom exercise
    custom_ex_payload = {
        "name": "Alice Secret Desi Mudgar Swing",
        "muscle_group": "Shoulders",
        "equipment": "Mudgar",
        "difficulty": "Intermediate",
        "instructions": "Traditional Akhada Indian club rotational swing."
    }
    create_res = client.post("/api/v1/exercises", json=custom_ex_payload, headers=auth_a)
    assert create_res.status_code == 201
    created_exercise = create_res.json()
    exercise_id = created_exercise["id"]
    assert created_exercise["is_custom"] is True

    # Alice should see her custom exercise in exercise list
    alice_list = client.get("/api/v1/exercises", headers=auth_a)
    alice_names = [e["name"] for e in alice_list.json()]
    assert "Alice Secret Desi Mudgar Swing" in alice_names

    # Bob must NOT see Alice's custom exercise in exercise list
    bob_list = client.get("/api/v1/exercises", headers=auth_b)
    bob_names = [e["name"] for e in bob_list.json()]
    assert "Alice Secret Desi Mudgar Swing" not in bob_names

    # Bob attempting to directly fetch Alice's custom exercise by ID must return 404
    bob_fetch = client.get(f"/api/v1/exercises/{exercise_id}", headers=auth_b)
    assert bob_fetch.status_code == 404


def test_custom_food_isolation_between_users(client: TestClient):
    auth_a = create_user(client, "user_carol", "carol@example.com")
    auth_b = create_user(client, "user_dave", "dave@example.com")

    # Carol creates a custom food item
    custom_food_payload = {
        "name": "Carol Secret High-Protein Halwa",
        "serving_size": "150g bowl",
        "calories": 280.0,
        "protein_g": 24.0,
        "carbs_g": 32.0,
        "fat_g": 6.0,
        "fiber_g": 4.0,
        "is_desi_special": True
    }
    create_res = client.post("/api/v1/nutrition/foods", json=custom_food_payload, headers=auth_a)
    assert create_res.status_code == 201
    food_id = create_res.json()["id"]

    # Carol should see her custom food item
    carol_foods = client.get("/api/v1/nutrition/foods", headers=auth_a)
    carol_names = [f["name"] for f in carol_foods.json()]
    assert "Carol Secret High-Protein Halwa" in carol_names

    # Dave must NOT see Carol's custom food item
    dave_foods = client.get("/api/v1/nutrition/foods", headers=auth_b)
    dave_names = [f["name"] for f in dave_foods.json()]
    assert "Carol Secret High-Protein Halwa" not in dave_names

    # Dave attempting to log Carol's private custom food item must return 404
    dave_log = client.post("/api/v1/nutrition/logs", json={
        "food_item_id": food_id,
        "meal_type": "Snack",
        "servings": 1.0
    }, headers=auth_b)
    assert dave_log.status_code == 404


def test_other_users_custom_exercises_cannot_be_attached_to_workouts(client: TestClient):
    auth_a = create_user(client, "workout_owner", "workout_owner@example.com")
    auth_b = create_user(client, "workout_guest", "workout_guest@example.com")

    created = client.post("/api/v1/exercises", json={
        "name": "Owner Private Cable Variant", "muscle_group": "Back",
        "equipment": "Cable", "difficulty": "Intermediate"
    }, headers=auth_a)
    assert created.status_code == 201
    private_exercise_id = created.json()["id"]

    plan = client.post("/api/v1/workouts/plans", json={
        "title": "Unauthorized plan",
        "exercises": [{"exercise_id": private_exercise_id, "sets": 3, "reps": 10}]
    }, headers=auth_b)
    assert plan.status_code == 404

    log = client.post("/api/v1/workouts/logs", json={
        "title": "Unauthorized log",
        "logged_exercises": [{"exercise_id": private_exercise_id, "sets_completed": 3, "reps_completed": 10}]
    }, headers=auth_b)
    assert log.status_code == 404
