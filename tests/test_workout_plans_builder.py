import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest

from frontend.views.workouts_view import (
    add_plan_exercise,
    remove_plan_exercise,
    add_log_exercise,
    remove_log_exercise
)


# ==============================================================================
# 1. ACTUAL STATE-MANAGEMENT CALLBACKS TESTS (REQUIREMENT 6)
# ==============================================================================

def test_actual_state_management_callback_functions():
    """
    Directly exercises add_plan_exercise() and remove_plan_exercise(row_id)
    callback functions to verify state mutations without manual simulation.
    """
    import streamlit as st

    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    orig_state = getattr(st, "session_state", None)
    try:
        mock_state = MockSessionState()
        st.session_state = mock_state

        # Initial state before callbacks
        mock_state["plan_exercise_count"] = 3
        mock_state["plan_exercise_row_ids"] = [1, 2, 3]
        mock_state["plan_next_row_id"] = 4
        mock_state["p_ex_1"] = "Bench Press (Chest)"
        mock_state["p_s_1"] = 4
        mock_state["p_r_1"] = 8
        mock_state["p_rst_1"] = 120

        mock_state["p_ex_2"] = "Overhead Press (Shoulders)"
        mock_state["p_s_2"] = 3
        mock_state["p_r_2"] = 10
        mock_state["p_rst_2"] = 90

        mock_state["p_ex_3"] = "Barbell Squat (Legs)"
        mock_state["p_s_3"] = 5
        mock_state["p_r_3"] = 5
        mock_state["p_rst_3"] = 180

        # 1. Execute actual callback function: add_plan_exercise()
        add_plan_exercise()

        # Verify callback mutated session state properly
        assert len(mock_state["plan_exercise_row_ids"]) == 4
        assert mock_state["plan_exercise_count"] == 4
        assert 4 in mock_state["plan_exercise_row_ids"]
        assert mock_state["plan_next_row_id"] == 5
        assert mock_state["p_s_4"] == 3
        assert mock_state["p_r_4"] == 12
        assert mock_state["p_rst_4"] == 60

        # Existing values in rows 1, 2, 3 are completely preserved
        assert mock_state["p_ex_1"] == "Bench Press (Chest)"
        assert mock_state["p_s_1"] == 4
        assert mock_state["p_ex_2"] == "Overhead Press (Shoulders)"
        assert mock_state["p_ex_3"] == "Barbell Squat (Legs)"

        # 2. Execute callback again for multiple additions
        add_plan_exercise()
        assert len(mock_state["plan_exercise_row_ids"]) == 5
        assert mock_state["plan_exercise_count"] == 5
        assert 5 in mock_state["plan_exercise_row_ids"]

        # 3. Execute actual callback function: remove_plan_exercise(row_id=2)
        remove_plan_exercise(2)

        # Verify row 2 was removed
        assert 2 not in mock_state["plan_exercise_row_ids"]
        assert len(mock_state["plan_exercise_row_ids"]) == 4
        assert mock_state["plan_exercise_count"] == 4
        assert "p_ex_2" not in mock_state
        assert "p_s_2" not in mock_state

        # Verify rows 1, 3, 4, 5 and their values are 100% preserved
        assert mock_state["p_ex_1"] == "Bench Press (Chest)"
        assert mock_state["p_ex_3"] == "Barbell Squat (Legs)"
        assert 4 in mock_state["plan_exercise_row_ids"]
        assert 5 in mock_state["plan_exercise_row_ids"]

    finally:
        st.session_state = orig_state


def test_actual_workout_log_callback_functions():
    """
    Directly exercises add_log_exercise() and remove_log_exercise(row_id)
    callback functions to verify state mutations and value preservation for logging workouts.
    """
    import streamlit as st

    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    orig_state = getattr(st, "session_state", None)
    try:
        mock_state = MockSessionState()
        st.session_state = mock_state

        # Initial state before callbacks
        mock_state["log_exercise_count"] = 3
        mock_state["log_exercise_row_ids"] = [1, 2, 3]
        mock_state["log_next_row_id"] = 4
        mock_state["log_ex_1"] = "Incline Dumbbell Press (Chest)"
        mock_state["log_s_1"] = 4
        mock_state["log_r_1"] = 12
        mock_state["log_w_1"] = 32.5

        mock_state["log_ex_2"] = "Lateral Raise (Shoulders)"
        mock_state["log_s_2"] = 3
        mock_state["log_r_2"] = 15
        mock_state["log_w_2"] = 14.0

        mock_state["log_ex_3"] = "Tricep Pushdown (Arms)"
        mock_state["log_s_3"] = 4
        mock_state["log_r_3"] = 12
        mock_state["log_w_3"] = 27.5

        # 1. Execute actual callback function: add_log_exercise()
        add_log_exercise()

        # Verify callback mutated session state properly
        assert len(mock_state["log_exercise_row_ids"]) == 4
        assert mock_state["log_exercise_count"] == 4
        assert 4 in mock_state["log_exercise_row_ids"]
        assert mock_state["log_next_row_id"] == 5
        assert mock_state["log_s_4"] == 3
        assert mock_state["log_r_4"] == 10
        assert mock_state["log_w_4"] == 20.0

        # Existing values in rows 1, 2, 3 are completely preserved
        assert mock_state["log_ex_1"] == "Incline Dumbbell Press (Chest)"
        assert mock_state["log_s_1"] == 4
        assert mock_state["log_w_1"] == 32.5
        assert mock_state["log_ex_2"] == "Lateral Raise (Shoulders)"
        assert mock_state["log_ex_3"] == "Tricep Pushdown (Arms)"

        # 2. Execute callback again for multiple additions
        add_log_exercise()
        assert len(mock_state["log_exercise_row_ids"]) == 5
        assert 5 in mock_state["log_exercise_row_ids"]

        # 3. Execute actual callback function: remove_log_exercise(row_id=2)
        remove_log_exercise(2)

        # Verify row 2 was removed
        assert 2 not in mock_state["log_exercise_row_ids"]
        assert len(mock_state["log_exercise_row_ids"]) == 4
        assert "log_ex_2" not in mock_state
        assert "log_s_2" not in mock_state
        assert "log_w_2" not in mock_state

        # Verify rows 1, 3, 4, 5 and their values are 100% preserved
        assert mock_state["log_ex_1"] == "Incline Dumbbell Press (Chest)"
        assert mock_state["log_s_1"] == 4
        assert mock_state["log_w_1"] == 32.5
        assert mock_state["log_ex_3"] == "Tricep Pushdown (Arms)"
        assert 4 in mock_state["log_exercise_row_ids"]
        assert 5 in mock_state["log_exercise_row_ids"]

    finally:
        st.session_state = orig_state


# ==============================================================================
# 2. ACTUAL STREAMLIT UI INTEGRATION TESTS (APPTEST)
# ==============================================================================

def test_actual_streamlit_ui_add_and_remove_exercise_interactions():
    """
    Renders the actual Streamlit app and exercises the real UI buttons:
    1. Verifies '+ Add Exercise' button is visibly rendered in Create New Plan form.
    2. Clicks '+ Add Exercise' using at.button.click().run().
    3. Clicks multiple times to add multiple rows.
    4. Verifies each row renders:
       - Exercise dropdown selector
       - Sets number input
       - Reps number input
       - Rest seconds number input
       - Remove button
    5. Clicks '🗑️ Remove' on an intermediate row and verifies other rows/values are preserved.
    6. Verifies 'Create Workout Plan' submit button exists.
    """
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "test_auth_token"
    at.session_state["user"] = {"username": "ui_tester", "full_name": "UI Tester"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Workout Planner"
    at.session_state["nav_radio"] = "Workout Planner"
    at.session_state["workout_active_tab"] = "📋 Workout Planner"
    at.run()

    assert len(at.exception) == 0, f"App execution failed: {at.exception}"

    # 1. Verify '+ Add Exercise' button is visibly rendered below the exercise fields
    add_btn_matches = [b for b in at.button if b.key == "btn_add_plan_slot"]
    assert len(add_btn_matches) == 1, "Expected '+ Add Exercise' button with key 'btn_add_plan_slot' to be rendered"
    assert "Add Exercise" in add_btn_matches[0].label

    # Initial row count
    initial_rows = len(at.session_state["plan_exercise_row_ids"])
    assert initial_rows >= 1

    # 2. Click '+ Add Exercise' button
    add_btn_matches[0].click().run()
    assert len(at.exception) == 0
    after_first_add = len(at.session_state["plan_exercise_row_ids"])
    assert after_first_add == initial_rows + 1

    # 3. Multiple clicks: Click '+ Add Exercise' a second time
    add_btn_again = [b for b in at.button if b.key == "btn_add_plan_slot"][0]
    add_btn_again.click().run()
    assert len(at.exception) == 0
    after_second_add = len(at.session_state["plan_exercise_row_ids"])
    assert after_second_add == initial_rows + 2

    # 4. Verify each row contains dropdown, sets, reps, rest seconds, and remove button
    current_row_ids = at.session_state["plan_exercise_row_ids"]
    for r_id in current_row_ids:
        # Exercise dropdown
        ex_select = [s for s in at.selectbox if s.key == f"p_ex_{r_id}"]
        assert len(ex_select) == 1, f"Missing selectbox for row {r_id}"

        # Sets, Reps, Rest inputs
        s_input = [n for n in at.number_input if n.key == f"p_s_{r_id}"]
        r_input = [n for n in at.number_input if n.key == f"p_r_{r_id}"]
        rst_input = [n for n in at.number_input if n.key == f"p_rst_{r_id}"]
        assert len(s_input) == 1, f"Missing sets input for row {r_id}"
        assert len(r_input) == 1, f"Missing reps input for row {r_id}"
        assert len(rst_input) == 1, f"Missing rest input for row {r_id}"

        # Remove button
        del_btn = [b for b in at.button if b.key == f"btn_del_row_{r_id}"]
        assert len(del_btn) == 1, f"Missing remove button for row {r_id}"

    # 5. Set custom value on row 1, click remove on row 2, verify row 1 value preserved
    first_row_id = current_row_ids[0]
    target_remove_id = current_row_ids[1]
    at.session_state[f"p_s_{first_row_id}"] = 7

    target_del_btn = [b for b in at.button if b.key == f"btn_del_row_{target_remove_id}"][0]
    target_del_btn.click().run()
    assert len(at.exception) == 0

    assert target_remove_id not in at.session_state["plan_exercise_row_ids"]
    assert at.session_state[f"p_s_{first_row_id}"] == 7, "Row 1 sets value was not preserved after removing row 2"

    # 6. Verify Create Workout Plan button is rendered
    save_btns = [b for b in at.button if b.key == "btn_save_workout_plan"]
    assert len(save_btns) == 1
    assert "Workout Plan" in save_btns[0].label


def test_actual_streamlit_ui_record_completed_workout_interactions():
    """
    Renders the actual Streamlit app on the 'Record Completed Workout' tab and verifies:
    1. '+ Add Exercise' button is visibly rendered below exercise rows.
    2. Clicking '+ Add Exercise' dynamically appends rows.
    3. Custom values entered into row 1 (sets, reps, weight) remain intact when row 2 is deleted.
    4. Individual delete button removes that row cleanly.
    5. 'Save Completed Workout ✅' button is visibly rendered.
    """
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "test_auth_token"
    at.session_state["user"] = {"username": "ui_tester", "full_name": "UI Tester"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Workout Planner"
    at.session_state["nav_radio"] = "Workout Planner"
    at.session_state["workout_active_tab"] = "📝 Record Completed Workout"
    at.run()

    assert len(at.exception) == 0, f"App execution failed: {at.exception}"

    # 1. Verify '+ Add Exercise' button is visibly rendered below exercise fields in Log Workout
    add_btn_matches = [b for b in at.button if b.key == "btn_add_log_slot"]
    assert len(add_btn_matches) == 1, "Expected '+ Add Exercise' button with key 'btn_add_log_slot' to be rendered"
    assert "Add Exercise" in add_btn_matches[0].label

    # Initial row count
    initial_rows = len(at.session_state["log_exercise_row_ids"])
    assert initial_rows >= 1

    # 2. Click '+ Add Exercise' button
    add_btn_matches[0].click().run()
    assert len(at.exception) == 0
    after_first_add = len(at.session_state["log_exercise_row_ids"])
    assert after_first_add == initial_rows + 1

    # Click '+ Add Exercise' a second time
    add_btn_again = [b for b in at.button if b.key == "btn_add_log_slot"][0]
    add_btn_again.click().run()
    assert len(at.exception) == 0
    after_second_add = len(at.session_state["log_exercise_row_ids"])
    assert after_second_add == initial_rows + 2

    # 3. Verify each row contains dropdown, sets, reps, weight input, and remove button
    current_row_ids = at.session_state["log_exercise_row_ids"]
    for r_id in current_row_ids:
        ex_select = [s for s in at.selectbox if s.key == f"log_ex_{r_id}"]
        assert len(ex_select) == 1, f"Missing selectbox for log row {r_id}"

        s_input = [n for n in at.number_input if n.key == f"log_s_{r_id}"]
        r_input = [n for n in at.number_input if n.key == f"log_r_{r_id}"]
        w_input = [n for n in at.number_input if n.key == f"log_w_{r_id}"]
        assert len(s_input) == 1, f"Missing sets input for log row {r_id}"
        assert len(r_input) == 1, f"Missing reps input for log row {r_id}"
        assert len(w_input) == 1, f"Missing weight input for log row {r_id}"

        del_btn = [b for b in at.button if b.key == f"btn_del_log_{r_id}"]
        assert len(del_btn) == 1, f"Missing remove button for log row {r_id}"

    # 4. Set custom values on row 1, click remove on row 2, verify row 1 values preserved
    first_row_id = current_row_ids[0]
    target_remove_id = current_row_ids[1]
    at.session_state[f"log_s_{first_row_id}"] = 5
    at.session_state[f"log_r_{first_row_id}"] = 15
    at.session_state[f"log_w_{first_row_id}"] = 45.0

    target_del_btn = [b for b in at.button if b.key == f"btn_del_log_{target_remove_id}"][0]
    target_del_btn.click().run()
    assert len(at.exception) == 0

    assert target_remove_id not in at.session_state["log_exercise_row_ids"]
    assert at.session_state[f"log_s_{first_row_id}"] == 5, "Row 1 sets value was not preserved"
    assert at.session_state[f"log_r_{first_row_id}"] == 15, "Row 1 reps value was not preserved"
    assert at.session_state[f"log_w_{first_row_id}"] == 45.0, "Row 1 weight value was not preserved"

    # 5. Verify Save Completed Workout button is rendered
    save_btns = [b for b in at.button if b.key == "btn_save_workout_log"]
    assert len(save_btns) == 1
    assert "Save Completed Workout" in save_btns[0].label


# ==============================================================================
# 3. API LEVEL: 1, 3, 5, AND 10 EXERCISE PLANS PERSISTENCE & RETRIEVAL
# ==============================================================================

@pytest.mark.parametrize("num_exercises", [1, 3, 5, 10])
def test_create_and_save_plan_with_variable_exercise_counts(client, auth_headers, num_exercises):
    """
    Verify creating and successfully saving workout plans with exactly
    1, 3, 5, and 10 exercises via POST /api/v1/workouts/plans.
    Confirms all exercises persist and can be reopened.
    """
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    assert ex_res.status_code == 200
    all_ex = ex_res.json()
    assert len(all_ex) >= num_exercises, f"Need at least {num_exercises} exercises in library"

    selected_exercises = all_ex[:num_exercises]
    plan_items = [
        {
            "exercise_id": ex["id"],
            "sets": 3 + (i % 2),
            "reps": 10 + (i % 5),
            "rest_seconds": 60 + (i * 10),
            "order_index": i + 1
        }
        for i, ex in enumerate(selected_exercises)
    ]

    payload = {
        "title": f"Plan with {num_exercises} Exercises",
        "description": f"Testing flexible plan creation with {num_exercises} distinct movements.",
        "goal": "Muscle Gain",
        "difficulty": "Intermediate",
        "exercises": plan_items
    }

    # Save plan
    post_res = client.post("/api/v1/workouts/plans", json=payload, headers=auth_headers)
    assert post_res.status_code == 201
    created = post_res.json()
    assert created["title"] == f"Plan with {num_exercises} Exercises"
    assert len(created["exercises"]) == num_exercises

    plan_id = created["id"]

    # Reopen plan
    get_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == plan_id
    assert len(retrieved["exercises"]) == num_exercises

    expected_ids = [ex["id"] for ex in selected_exercises]
    persisted_ids = [item["exercise_id"] for item in retrieved["exercises"]]
    assert persisted_ids == expected_ids


# ==============================================================================
# 4. REMOVING AN EXERCISE AND SAVING REMAINING EXERCISES VIA API
# ==============================================================================

def test_remove_exercise_and_save_remaining_plan(client, auth_headers):
    """
    Simulate user configuring 5 exercises, removing the 3rd exercise row,
    and saving the remaining 4 exercises.
    Verify that the saved plan contains exactly the 4 remaining exercises with re-indexed order.
    """
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_ex = ex_res.json()
    assert len(all_ex) >= 5

    initial_5 = all_ex[:5]
    # Remove the 3rd exercise (index 2)
    remaining_4 = [initial_5[0], initial_5[1], initial_5[3], initial_5[4]]

    payload_items = [
        {
            "exercise_id": ex["id"],
            "sets": 4,
            "reps": 12,
            "rest_seconds": 90,
            "order_index": i + 1
        }
        for i, ex in enumerate(remaining_4)
    ]

    payload = {
        "title": "5 Minus 1 Exercise Plan",
        "description": "5 exercises were added, 3rd row removed, saving 4 exercises.",
        "goal": "Strength",
        "difficulty": "Advanced",
        "exercises": payload_items
    }

    post_res = client.post("/api/v1/workouts/plans", json=payload, headers=auth_headers)
    assert post_res.status_code == 201
    created = post_res.json()
    assert len(created["exercises"]) == 4

    # Verify exercise 3 from initial_5 is NOT present
    removed_id = initial_5[2]["id"]
    saved_ids = [item["exercise_id"] for item in created["exercises"]]
    assert removed_id not in saved_ids
    assert saved_ids == [ex["id"] for ex in remaining_4]


# ==============================================================================
# 5. BACKEND LIMITS & ERROR HANDLING
# ==============================================================================

def test_over_50_exercises_limit_rejection(client, auth_headers):
    """Verify that attempting to create a plan with 51 exercises is rejected by the backend."""
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    all_ex = ex_res.json()
    assert len(all_ex) >= 1

    # Repeat exercise to generate 51 items
    ex_51 = [
        {
            "exercise_id": all_ex[0]["id"],
            "sets": 3,
            "reps": 10,
            "rest_seconds": 60,
            "order_index": i + 1
        }
        for i in range(51)
    ]

    payload = {
        "title": "Over Limit 51 Plan",
        "goal": "General Fitness",
        "difficulty": "Beginner",
        "exercises": ex_51
    }
    res = client.post("/api/v1/workouts/plans", json=payload, headers=auth_headers)
    assert res.status_code in (400, 422)
    assert "50" in res.text


def test_inaccessible_exercise_id_returns_404(client, auth_headers):
    """Verify that submitting an unlisted / non-existent exercise ID returns 404."""
    payload = {
        "title": "Ghost Exercise Plan",
        "goal": "General Fitness",
        "difficulty": "Beginner",
        "exercises": [
            {"exercise_id": 999999, "sets": 3, "reps": 10, "rest_seconds": 60, "order_index": 1}
        ]
    }
    res = client.post("/api/v1/workouts/plans", json=payload, headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
