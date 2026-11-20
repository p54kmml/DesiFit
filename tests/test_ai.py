def test_ai_status(client):
    res = client.get("/api/v1/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "api_connected" in data
    assert "model" in data


def test_ai_chat_fallback(client, auth_headers):
    # Tests that when OpenAI API key is not present or invalid, rule-based fallback replies intelligently
    res = client.post("/api/v1/ai/chat", json={
        "message": "What is the best protein diet for muscle building?"
    }, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "is_fallback" in data

    # Verify history is saved
    hist_res = client.get("/api/v1/ai/history", headers=auth_headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 2  # user message and assistant reply


def test_ai_chat_6_day_workout_generation(client, auth_headers):
    # Tests the fix for user request: "Make me a 6-day workout"
    res = client.post("/api/v1/ai/chat", json={
        "message": "Make me a 6-day workout"
    }, headers=auth_headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    # Must contain exactly 6 active days and not be mislabeled as a 4-day split
    assert "6-Day Workout Routine" in reply or "6 Active Training Days" in reply
    assert "Day 1:" in reply
    assert "Day 2:" in reply
    assert "Day 3:" in reply
    assert "Day 4:" in reply
    assert "Day 5:" in reply
    assert "Day 6:" in reply
    assert "Target Muscles" in reply
    assert "Rest:" in reply
    assert "sets ×" in reply
    assert "4-Day Push/Pull/Legs" not in reply


def test_ai_chat_5_day_workout_generation(client, auth_headers):
    res = client.post("/api/v1/ai/chat", json={
        "message": "Give me a 5-day workout split"
    }, headers=auth_headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    
    assert "5-Day Workout Routine" in reply or "5 Active Training Days" in reply
    assert "Day 5:" in reply
    assert "Target Muscles" in reply


def test_saved_workout_frequency_does_not_turn_protein_question_into_workout(client, auth_headers):
    profile_update = client.put("/api/v1/profile", json={
        "age": 25, "gender": "Male", "height_cm": 175, "current_weight_kg": 70,
        "fitness_goal": "Muscle Gain", "dietary_preference": "Vegetarian",
        "activity_level": "Very Active", "workout_frequency_days": 6,
        "preferred_split": "Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)",
        "custom_split_details": "1. Chest + Triceps\n2. Back + Biceps\n3. Legs\n4. Chest + Shoulders\n5. Arms (Biceps + Triceps)\n6. Back + Shoulders\n7. Rest"
    }, headers=auth_headers)
    assert profile_update.status_code == 200

    res = client.post("/api/v1/ai/chat", json={
        "message": "How can I increase my daily protein intake?"
    }, headers=auth_headers)
    assert res.status_code == 200
    reply = res.json()["reply"]
    assert "Recommended Protein Sources" in reply
    assert "Day 1:" not in reply
