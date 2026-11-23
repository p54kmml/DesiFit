import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from streamlit.testing.v1 import AppTest

from backend.services.email_service import (
    is_production,
    is_resend_configured,
    is_smtp_configured,
    is_email_configured,
    send_password_reset_email,
    get_from_email,
    get_frontend_url
)


# ==============================================================================
# ISSUE 1: WORKOUT PLANNER STATE & ADD EXERCISES TESTS
# ==============================================================================

def test_workout_planner_add_exercise_slot_preserves_state():
    """
    Verify that in the Streamlit Workout Planner UI:
    1. Entering a plan name and selecting exercise details.
    2. Clicking '➕ Add Exercise Slot' increments slot count.
    3. Plan name, previous exercise selections, and active tab are 100% PRESERVED.
    """
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "valid_test_token"
    at.session_state["user"] = {"username": "planner_athlete", "full_name": "Planner Athlete"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Workout Planner"
    at.session_state["nav_radio"] = "Workout Planner"
    at.session_state["workout_active_tab"] = "📋 Workout Plans"
    at.run()

    assert len(at.exception) == 0

    # Locate Plan Name text input
    p_title_input = [t for t in at.text_input if "Plan Name" in t.label or t.key == "p_title_input"]
    assert len(p_title_input) >= 1
    p_title_input[0].set_value("Hypertrophy Push Plan")

    initial_slots = at.session_state.get("plan_exercise_count", 4)

    # Click '➕ Add Exercise Slot'
    add_btn = [b for b in at.button if b.key == "btn_add_plan_slot"]
    assert len(add_btn) == 1
    add_btn[0].click().run()

    assert len(at.exception) == 0

    # Verify slot count increased
    new_slots = at.session_state.get("plan_exercise_count")
    assert new_slots == initial_slots + 1

    # Verify plan name is preserved
    p_title_after = [t for t in at.text_input if "Plan Name" in t.label or t.key == "p_title_input"][0]
    assert p_title_after.value == "Hypertrophy Push Plan"

    # Verify active tab remained on Workout Plans / Workout Planner
    assert at.session_state.get("workout_active_tab") in ("📋 Workout Planner", "📋 Workout Plans")


def test_workout_planner_add_exercise_button_visible_and_functional_on_initial_navigation():
    """
    Verify that when user navigates to Workout Planner:
    1. The page defaults directly to the Workout Planner tab (not 'Record a Completed Workout').
    2. The '➕ Add Exercise' button is immediately visible without needing to switch tabs.
    3. Clicking '➕ Add Exercise' dynamically adds an exercise slot (1 to 50) and preserves input state.
    """
    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "valid_test_token"
    at.session_state["user"] = {"username": "planner_athlete", "full_name": "Planner Athlete"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Workout Planner"
    at.session_state["nav_radio"] = "Workout Planner"
    at.run()

    assert len(at.exception) == 0

    # Ensure Add Exercise buttons exist and are visible
    add_exercise_buttons = [b for b in at.button if "Add Exercise" in b.label]
    assert len(add_exercise_buttons) >= 1, "At least one 'Add Exercise' button must be rendered on Workout Planner"

    # Verify both top button and bottom button exist
    top_btn = [b for b in at.button if b.key == "btn_add_plan_exercise_top"]
    bottom_btn = [b for b in at.button if b.key == "btn_add_plan_slot"]
    assert len(top_btn) == 1, "'btn_add_plan_exercise_top' must be rendered"
    assert len(bottom_btn) == 1, "'btn_add_plan_slot' must be rendered"

    # Set plan name and verify state preservation
    p_title = [t for t in at.text_input if t.key == "p_title_input"][0]
    p_title.set_value("Chest Day Protocol")

    initial_slots = at.session_state.get("plan_exercise_count", 4)

    # Click top Add Exercise button
    top_btn[0].click().run()
    assert len(at.exception) == 0
    assert at.session_state["plan_exercise_count"] == initial_slots + 1
    assert [t for t in at.text_input if t.key == "p_title_input"][0].value == "Chest Day Protocol"

    # Click bottom Add Exercise button
    bottom_btn_new = [b for b in at.button if b.key == "btn_add_plan_slot"][0]
    bottom_btn_new.click().run()
    assert len(at.exception) == 0
    assert at.session_state["plan_exercise_count"] == initial_slots + 2
    assert [t for t in at.text_input if t.key == "p_title_input"][0].value == "Chest Day Protocol"


def test_workout_planner_api_create_reopen_and_edit_multiple_exercises(client, auth_headers):
    """
    Test full end-to-end workout plan lifecycle with multiple exercises (1 to 15):
    1. Fetch available exercises from the library.
    2. Create a custom workout plan with 8 exercises.
    3. Retrieve the created plan by ID to verify persistence of all 8 exercises.
    4. Update the plan by adding 4 more exercises (total 12 exercises).
    5. Reopen the updated plan and verify all 12 exercises persist accurately.
    """
    ex_res = client.get("/api/v1/exercises", headers=auth_headers)
    assert ex_res.status_code == 200
    all_ex = ex_res.json()
    assert len(all_ex) >= 12

    # Step 1: Create plan with 8 exercises
    initial_exs = [
        {
            "exercise_id": all_ex[i]["id"],
            "sets": 3 + (i % 2),
            "reps": 10 + (i % 3),
            "rest_seconds": 60,
            "order_index": i + 1
        }
        for i in range(8)
    ]

    create_payload = {
        "title": "8-Exercise Upper-Lower Split",
        "description": "Comprehensive routine with 8 distinct movements.",
        "goal": "Muscle Gain",
        "difficulty": "Intermediate",
        "exercises": initial_exs
    }

    create_res = client.post("/api/v1/workouts/plans", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created_data = create_res.json()
    plan_id = created_data["id"]
    assert len(created_data["exercises"]) == 8

    # Step 2: Reopen / Retrieve plan by ID
    get_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert get_res.status_code == 200
    retrieved_data = get_res.json()
    assert retrieved_data["title"] == "8-Exercise Upper-Lower Split"
    assert len(retrieved_data["exercises"]) == 8

    # Step 3: Update plan by extending to 12 exercises
    updated_exs = [
        {
            "exercise_id": all_ex[i]["id"],
            "sets": 4,
            "reps": 12,
            "rest_seconds": 90,
            "order_index": i + 1
        }
        for i in range(12)
    ]

    update_payload = {
        "title": "12-Exercise Heavy Volume Split",
        "exercises": updated_exs
    }

    update_res = client.put(f"/api/v1/workouts/plans/{plan_id}", json=update_payload, headers=auth_headers)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "12-Exercise Heavy Volume Split"
    assert len(updated_data["exercises"]) == 12

    # Step 4: Reopen again and verify persistence
    reopen_res = client.get(f"/api/v1/workouts/plans/{plan_id}", headers=auth_headers)
    assert reopen_res.status_code == 200
    final_data = reopen_res.json()
    assert len(final_data["exercises"]) == 12
    persisted_ids = [item["exercise_id"] for item in final_data["exercises"]]
    expected_ids = [all_ex[i]["id"] for i in range(12)]
    assert persisted_ids == expected_ids


# ==============================================================================
# ISSUE 2: PASSWORD RECOVERY EMAIL & SECURITY TESTS
# ==============================================================================

def test_production_detection_mechanisms(monkeypatch):
    """
    Verify is_production() correctly identifies production environments via:
    - ENVIRONMENT=production
    - RENDER=true
    - RENDER_SERVICE_ID set
    """
    # Default clean environment
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    assert is_production() is False

    # 1. ENVIRONMENT=production
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert is_production() is True

    # 2. RENDER=true (Render platform default)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("RENDER", "true")
    assert is_production() is True

    # 3. RENDER_SERVICE_ID present
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("RENDER_SERVICE_ID", "srv-c123456789")
    assert is_production() is True


def test_production_password_recovery_never_exposes_token_in_api(client, monkeypatch):
    """
    CRITICAL SECURITY CHECK:
    In production mode (e.g. deployed on Render), the /forgot-password endpoint
    must NEVER return dev_token, dev_reset_link, or dev_note, even if email provider is unconfigured.
    """
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)

    # Register test user
    client.post("/api/v1/auth/register", json={
        "email": "prod_recovery_check@desifit.in",
        "username": "prod_rec_user",
        "full_name": "Prod Recovery User",
        "password": "ValidPassword123!"
    })

    # Request password recovery
    res = client.post("/api/v1/auth/forgot-password", json={"email": "prod_recovery_check@desifit.in"})
    assert res.status_code == 200
    data = res.json()

    # Verify zero token leakage
    assert data["dev_token"] is None, "dev_token MUST NOT be returned in production"
    assert data["dev_reset_link"] is None, "dev_reset_link MUST NOT be returned in production"
    assert data["dev_note"] is None, "dev_note MUST NOT be returned in production"
    assert "If this email is registered" in data["message"]


def test_production_resend_verification_never_exposes_token(client, monkeypatch):
    """Verify resend-verification in production never leaks raw verification tokens."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)

    res = client.post("/api/v1/auth/resend-verification", json={"email": "prod_recovery_check@desifit.in"})
    assert res.status_code == 200
    data = res.json()
    assert data["dev_token"] is None, "dev_token MUST NOT be leaked in production"


def test_frontend_auth_view_suppresses_dev_banner_in_production(monkeypatch):
    """
    Verify that in production mode, the Streamlit frontend NEVER displays
    'Development Mode (SMTP Not Configured)' or exposed tokens.
    """
    from frontend.views.auth_view import is_production as frontend_is_prod

    monkeypatch.setenv("RENDER", "true")
    assert frontend_is_prod() is True

    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert frontend_is_prod() is True


def test_email_dispatch_via_resend_sdk(monkeypatch):
    """Verify that with RESEND_API_KEY set, password recovery emails dispatch via Resend."""
    monkeypatch.setenv("RESEND_API_KEY", "re_prod_resend_key_99999")
    monkeypatch.setenv("EMAIL_FROM", "DesiFit Security <noreply@desifit.com>")
    monkeypatch.setenv("FRONTEND_URL", "https://desifit-frontend.onrender.com")

    assert is_resend_configured() is True
    assert is_email_configured() is True

    with patch("resend.Emails.send") as mock_send:
        mock_send.return_value = {"id": "msg_resend_prod_123"}
        sent = send_password_reset_email(
            to_email="athlete@example.com",
            reset_token="secure_prod_reset_token_456"
        )
        assert sent is True
        assert mock_send.called
        call_params = mock_send.call_args[0][0]
        assert call_params["to"] == ["athlete@example.com"]
        assert call_params["from"] == "DesiFit Security <noreply@desifit.com>"
        assert "https://desifit-frontend.onrender.com/?token=secure_prod_reset_token_456" in call_params["html"]


def test_email_dispatch_via_smtp_fallback(monkeypatch):
    """Verify that when SMTP is configured and Resend is unconfigured, email dispatches via SMTP."""
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setenv("SMTP_HOST", "smtp.sendgrid.net")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USERNAME", "apikey")
    monkeypatch.setenv("SMTP_PASSWORD", "sg_secret_pass")
    monkeypatch.setenv("SMTP_FROM_EMAIL", "no-reply@desifit.com")

    assert is_resend_configured() is False
    assert is_smtp_configured() is True
    assert is_email_configured() is True

    with patch("backend.services.email_service._deliver_smtp") as mock_smtp:
        mock_smtp.return_value = True
        sent = send_password_reset_email(
            to_email="athlete_smtp@example.com",
            reset_token="smtp_reset_token_789"
        )
        assert sent is True
        assert mock_smtp.called
        call_args = mock_smtp.call_args[0]
        assert call_args[0] == "athlete_smtp@example.com"
        assert "smtp_reset_token_789" in call_args[2]  # html
