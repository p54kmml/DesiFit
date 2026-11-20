import pytest
from fastapi.testclient import TestClient


def test_full_user_lifecycle_and_security(client: TestClient):
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200

    # 2. Register & Login
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "lifecycle_test@desifit.in",
        "username": "lifecycle_tester",
        "full_name": "LifeCycle Tester",
        "password": "StrongPassword123"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", json={
        "username": "lifecycle_tester",
        "password": "StrongPassword123"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Check fresh profile has NO hardcoded 70kg fallback
    prof_res = client.get("/api/v1/profile", headers=headers)
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert prof["current_weight_kg"] is None
    assert prof["height_cm"] is None
    assert prof["is_onboarded"] is False

    # 4. AI chat for unonboarded user: verify no leak of 70kg / 140g protein
    ai_res = client.post("/api/v1/ai/chat", json={"message": "Give me a nutrition overview"}, headers=headers)
    assert ai_res.status_code == 200
    ai_text = ai_res.json()["reply"]
    assert "70.0" not in ai_text and "70 kg" not in ai_text

    # 5. Onboard with custom biometrics (82.5 kg, 180 cm, 32 yrs)
    onboard_res = client.post("/api/v1/profile/onboard", json={
        "age": 32,
        "gender": "Male",
        "height_cm": 180.0,
        "current_weight_kg": 82.5,
        "target_weight_kg": 78.0,
        "fitness_experience": "Intermediate",
        "fitness_goal": "Fat Loss",
        "dietary_preference": "Non-Vegetarian",
        "activity_level": "Very Active"
    }, headers=headers)
    assert onboard_res.status_code == 200
    prof_updated = onboard_res.json()
    assert prof_updated["is_onboarded"] is True
    assert prof_updated["current_weight_kg"] == 82.5
    assert prof_updated["target_protein_g"] == round(82.5 * 2.0, 1)  # 165.0g for fat loss

    # 6. Verify 6-day workout generation
    workout_res = client.post("/api/v1/ai/chat", json={"message": "Make me a 6-day workout"}, headers=headers)
    assert workout_res.status_code == 200
    w_text = workout_res.json()["reply"]
    assert "6-Day" in w_text or "6 Active Training Days" in w_text
    assert "Day 1:" in w_text
    assert "Day 2:" in w_text
    assert "Day 3:" in w_text
    assert "Day 4:" in w_text
    assert "Day 5:" in w_text
    assert "Day 6:" in w_text
    assert "Target Muscles" in w_text
    assert "4-Day" not in w_text

    # 7. Verify 5-day workout generation
    workout5_res = client.post("/api/v1/ai/chat", json={"message": "Make me a 5-day split"}, headers=headers)
    assert workout5_res.status_code == 200
    w5_text = workout5_res.json()["reply"]
    assert "5-Day" in w5_text or "5 Active Training Days" in w5_text
    assert "Day 1:" in w5_text
    assert "Day 5:" in w5_text
    assert "Target Muscles" in w5_text

    # 8. Record body measurement
    meas_res = client.post("/api/v1/progress/measurements", json={
        "weight_kg": 82.0,
        "chest_cm": 105.0,
        "waist_cm": 84.0,
        "notes": "End of week 1 check-in"
    }, headers=headers)
    assert meas_res.status_code == 201
    assert meas_res.json()["weight_kg"] == 82.0

    # 9. Fetch dashboard stats
    dash_res = client.get("/api/v1/dashboard/stats", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["current_weight_kg"] == 82.0
    assert "daily_calorie_target" in dash_data
    assert len(dash_data["weekly_activity"]) == 7
