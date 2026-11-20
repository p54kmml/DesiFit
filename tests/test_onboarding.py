def test_new_user_registration_is_not_onboarded(client):
    reg = client.post("/api/v1/auth/register", json={
        "email": "freshuser@desifit.in",
        "username": "freshuser",
        "full_name": "Fresh User",
        "password": "Password123"
    })
    assert reg.status_code == 201

    login = client.post("/api/v1/auth/login", json={
        "username": "freshuser",
        "password": "Password123"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["is_onboarded"] is False

    # Check profile
    prof_res = client.get("/api/v1/profile", headers={"Authorization": f"Bearer {token}"})
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert prof["is_onboarded"] is False
    # Verify no personal 70kg is hardcoded as default
    assert prof["current_weight_kg"] is None


def test_complete_onboarding_and_macro_calculation(client):
    # Register fresh user for this test
    client.post("/api/v1/auth/register", json={
        "email": "onboardtest@desifit.in",
        "username": "onboard_test_user",
        "full_name": "Onboard User",
        "password": "Password123"
    })
    login = client.post("/api/v1/auth/login", json={
        "username": "onboard_test_user",
        "password": "Password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit onboarding with specific biometrics
    onboard_payload = {
        "age": 28,
        "gender": "Female",
        "height_cm": 162.0,
        "current_weight_kg": 58.0,
        "target_weight_kg": 54.0,
        "fitness_experience": "Beginner",
        "fitness_goal": "Fat Loss",
        "dietary_preference": "Vegetarian",
        "activity_level": "Moderately Active"
    }
    onboard_res = client.post("/api/v1/profile/onboard", json=onboard_payload, headers=headers)
    assert onboard_res.status_code == 200
    data = onboard_res.json()
    assert data["is_onboarded"] is True
    assert data["current_weight_kg"] == 58.0
    assert data["target_weight_kg"] == 54.0
    assert data["gender"] == "Female"
    # Verify scientifically calculated macros for 58kg female fat loss
    assert data["target_protein_g"] == round(58.0 * 2.0, 1)  # 116g
    assert data["target_calories"] > 1300

    # Verify initial body measurement was automatically recorded
    meas_res = client.get("/api/v1/progress/measurements", headers=headers)
    assert meas_res.status_code == 200
    measurements = meas_res.json()
    assert len(measurements) >= 1
    assert measurements[0]["weight_kg"] == 58.0


def test_multi_user_data_isolation(client):
    # 1. Register User Alpha
    client.post("/api/v1/auth/register", json={
        "email": "alpha@desifit.in",
        "username": "user_alpha",
        "full_name": "Alpha Athlete",
        "password": "AlphaPassword123"
    })
    tok_a = client.post("/api/v1/auth/login", json={"username": "user_alpha", "password": "AlphaPassword123"}).json()["access_token"]
    h_a = {"Authorization": f"Bearer {tok_a}"}

    # Onboard User Alpha (85kg Muscle Gain)
    client.post("/api/v1/profile/onboard", json={
        "age": 26, "gender": "Male", "height_cm": 182.0, "current_weight_kg": 85.0, "target_weight_kg": 90.0,
        "fitness_experience": "Advanced", "fitness_goal": "Muscle Gain", "dietary_preference": "Non-Vegetarian",
        "activity_level": "Very Active"
    }, headers=h_a)

    # 2. Register User Beta
    client.post("/api/v1/auth/register", json={
        "email": "beta@desifit.in",
        "username": "user_beta",
        "full_name": "Beta Athlete",
        "password": "BetaPassword123"
    })
    tok_b = client.post("/api/v1/auth/login", json={"username": "user_beta", "password": "BetaPassword123"}).json()["access_token"]
    h_b = {"Authorization": f"Bearer {tok_b}"}

    # Onboard User Beta (52kg Fat Loss)
    client.post("/api/v1/profile/onboard", json={
        "age": 32, "gender": "Female", "height_cm": 158.0, "current_weight_kg": 52.0, "target_weight_kg": 49.0,
        "fitness_experience": "Beginner", "fitness_goal": "Fat Loss", "dietary_preference": "Vegetarian",
        "activity_level": "Lightly Active"
    }, headers=h_b)

    # 3. User Alpha logs a workout
    ex_id = client.get("/api/v1/exercises", headers=h_a).json()[0]["id"]
    w_alpha = client.post("/api/v1/workouts/logs", json={
        "title": "Alpha Heavy Chest Workout",
        "duration_minutes": 60,
        "logged_exercises": [{"exercise_id": ex_id, "sets_completed": 4, "reps_completed": 8, "weight_kg": 90.0}]
    }, headers=h_a).json()

    # 4. User Beta logs a different workout
    w_beta = client.post("/api/v1/workouts/logs", json={
        "title": "Beta Light Cardio & Core",
        "duration_minutes": 30,
        "logged_exercises": [{"exercise_id": ex_id, "sets_completed": 2, "reps_completed": 15, "weight_kg": 10.0}]
    }, headers=h_b).json()

    # Verify User Alpha sees only Alpha's workout
    alpha_workouts = client.get("/api/v1/workouts/logs", headers=h_a).json()
    assert len(alpha_workouts) == 1
    assert alpha_workouts[0]["title"] == "Alpha Heavy Chest Workout"

    # Verify User Beta sees only Beta's workout
    beta_workouts = client.get("/api/v1/workouts/logs", headers=h_b).json()
    assert len(beta_workouts) == 1
    assert beta_workouts[0]["title"] == "Beta Light Cardio & Core"

    # User Alpha attempts to delete User Beta's workout -> must return 404
    del_res = client.delete(f"/api/v1/workouts/logs/{w_beta['id']}", headers=h_a)
    assert del_res.status_code == 404

    # 5. Nutrition isolation: User Alpha logs food, User Beta has empty nutrition logs
    food_id = client.get("/api/v1/nutrition/foods", headers=h_a).json()[0]["id"]
    client.post("/api/v1/nutrition/logs", json={
        "food_item_id": food_id, "meal_type": "Lunch", "servings": 2.0
    }, headers=h_a)

    alpha_nutr = client.get("/api/v1/nutrition/summary", headers=h_a).json()
    beta_nutr = client.get("/api/v1/nutrition/summary", headers=h_b).json()

    assert alpha_nutr["calories_consumed"] > 0
    assert beta_nutr["calories_consumed"] == 0

    # 6. AI Conversation history isolation
    client.post("/api/v1/ai/chat", json={"message": "Alpha secret query"}, headers=h_a)
    client.post("/api/v1/ai/chat", json={"message": "Beta distinct inquiry"}, headers=h_b)

    alpha_ai_hist = client.get("/api/v1/ai/history", headers=h_a).json()
    beta_ai_hist = client.get("/api/v1/ai/history", headers=h_b).json()

    assert any("Alpha secret query" in m["content"] for m in alpha_ai_hist)
    assert not any("Beta distinct inquiry" in m["content"] for m in alpha_ai_hist)
    assert any("Beta distinct inquiry" in m["content"] for m in beta_ai_hist)
    assert not any("Alpha secret query" in m["content"] for m in beta_ai_hist)
