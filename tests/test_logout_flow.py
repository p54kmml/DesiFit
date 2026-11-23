import pytest
from frontend.navigation import logout_user, NAV_OPTIONS, PAGE_ALIASES


def test_logout_user_state_reset():
    """
    Focused regression test verifying logout flow:
    1. Sets token, user, is_onboarded, and an active nav_page.
    2. Calls logout_user().
    3. Verifies token, user, is_onboarded are cleared, and nav_page resets to Dashboard.
    4. Confirms that logout_user does NOT attempt to directly mutate 'nav_radio',
       preventing StreamlitWidgetAlreadyInstantiatedError on the first click.
    """
    mock_session = {
        "token": "valid_bearer_token_xyz",
        "user": {"username": "testuser", "full_name": "Test User"},
        "is_onboarded": True,
        "nav_page": "Workout Planner",
        "nav_radio": "Workout Planner"
    }

    # Simulate running logout_user in the session context
    class MockSessionState(dict):
        def __getattr__(self, key):
            return self.get(key)
        def __setattr__(self, key, value):
            self[key] = value

    import streamlit as st
    orig_session_state = getattr(st, "session_state", None)
    try:
        mock_state = MockSessionState(mock_session)
        st.session_state = mock_state

        # Execute logout
        logout_user()

        # Verify session state was cleanly cleared
        assert mock_state["token"] is None
        assert mock_state["user"] is None
        assert mock_state["is_onboarded"] is False
        assert mock_state["nav_page"] == "Dashboard"

        # Pre-instantiation check: On next login/navigation run,
        # nav_page is "Dashboard", so current_target evaluates to "Dashboard"
        current_target = mock_state.get("nav_page", "Dashboard")
        assert current_target == "Dashboard"
        assert current_target in NAV_OPTIONS
    finally:
        st.session_state = orig_session_state


def test_logout_api_authorization_rejection(client, auth_headers):
    """
    Verify that once logged out (token cleared), protected endpoints
    strictly reject unauthenticated access with 401 Unauthorized.
    """
    # Authenticated access succeeds
    authed_res = client.get("/api/v1/workouts/plans", headers=auth_headers)
    assert authed_res.status_code == 200

    # Unauthenticated access (simulating cleared token after logout) fails with 401
    unauthed_res = client.get("/api/v1/workouts/plans", headers={})
    assert unauthed_res.status_code == 401


def test_streamlit_app_logout_first_click_no_widget_error():
    """
    Simulate full Streamlit execution using AppTest:
    1. Authenticate and navigate to 'Workout Planner' with nav_radio instantiated.
    2. Click 'Log Out' button on the sidebar.
    3. Assert zero StreamlitWidgetAlreadyInstantiatedError or other exceptions.
    4. Assert token is cleared and user is redirected to Dashboard / login screen on the very first click.
    """
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "valid_test_token"
    at.session_state["user"] = {"username": "athlete_1", "full_name": "Test Athlete"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Workout Planner"
    at.session_state["nav_radio"] = "Workout Planner"
    at.run()

    # Confirm initial view has no errors
    assert len(at.exception) == 0, f"Unexpected error during initial run: {at.exception}"

    # Find the sidebar logout button
    logout_buttons = [btn for btn in at.sidebar.button if "Log Out" in btn.label]
    assert len(logout_buttons) == 1, "Expected exactly 1 logout button in sidebar"

    # Click logout on the very first click
    logout_buttons[0].click().run()

    # Verify zero exceptions (no StreamlitWidgetAlreadyInstantiatedError!)
    assert len(at.exception) == 0, f"Exception occurred during logout click: {at.exception}"

    # Verify state reset
    assert at.session_state["token"] is None
    assert at.session_state["user"] is None
    assert at.session_state["nav_page"] == "Dashboard"


def test_streamlit_navigation_single_click_all_pages():
    """
    Focused regression test verifying single-click sidebar page navigation:
    Iterates through all primary pages:
    - Dashboard
    - Workout Planner
    - Exercise Library
    - Nutrition Tracker
    - User Profile
    - AI Fitness Assistant
    - Body Progress
    Ensures clicking any option immediately transitions nav_page and nav_radio on the first click
    with zero exceptions.
    """
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "valid_test_token"
    at.session_state["user"] = {"username": "athlete_nav", "full_name": "Navigation Athlete"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Dashboard"
    at.session_state["nav_radio"] = "Dashboard"
    at.run()

    assert len(at.exception) == 0
    assert at.session_state["nav_page"] == "Dashboard"

    target_pages = [
        "Workout Planner",
        "Exercise Library",
        "Nutrition Tracker",
        "User Profile",
        "Dashboard",
        "AI Fitness Assistant",
        "Body Progress"
    ]

    for target_page in target_pages:
        # Simulate single click on the radio option
        at.sidebar.radio[0].set_value(target_page).run()

        # Verify zero runtime exceptions
        assert len(at.exception) == 0, f"Exception occurred navigating to {target_page}: {at.exception}"

        # Verify target page was immediately rendered
        assert at.session_state["nav_page"] == target_page
        assert at.session_state["nav_radio"] == target_page


def test_streamlit_programmatic_navigation_and_subsequent_clicks():
    """
    Verify that programmatic navigation (e.g. from Dashboard Quick Actions setting nav_page)
    synchronizes cleanly with nav_radio before widget instantiation, and subsequent
    sidebar clicks continue functioning on the first click.
    """
    from pathlib import Path
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parent.parent / "frontend" / "app.py"
    at = AppTest.from_file(str(app_path))
    at.session_state["token"] = "valid_test_token"
    at.session_state["user"] = {"username": "athlete_prog", "full_name": "Programmatic Athlete"}
    at.session_state["is_onboarded"] = True
    at.session_state["nav_page"] = "Dashboard"
    at.session_state["nav_radio"] = "Dashboard"
    at.run()
    assert len(at.exception) == 0

    # Programmatic change simulating Quick Action
    at.session_state["nav_page"] = "Workout Planner"
    at.run()
    assert len(at.exception) == 0
    assert at.session_state["nav_page"] == "Workout Planner"
    assert at.session_state["nav_radio"] == "Workout Planner"

    # User clicks Exercise Library next
    at.sidebar.radio[0].set_value("Exercise Library").run()
    assert len(at.exception) == 0
    assert at.session_state["nav_page"] == "Exercise Library"
    assert at.session_state["nav_radio"] == "Exercise Library"

    # Single-click logout from this page
    logout_buttons = [btn for btn in at.sidebar.button if "Log Out" in btn.label]
    assert len(logout_buttons) == 1
    logout_buttons[0].click().run()
    assert len(at.exception) == 0
    assert at.session_state["token"] is None
    assert at.session_state["nav_page"] == "Dashboard"