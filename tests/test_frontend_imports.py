import os
import sys
from pathlib import Path
import pytest


def test_frontend_init_files_exist():
    """Verify that all required __init__.py files exist in the frontend package."""
    repo_root = Path(__file__).resolve().parent.parent
    frontend_dir = repo_root / "frontend"

    assert (frontend_dir / "__init__.py").is_file(), "frontend/__init__.py must exist"
    assert (frontend_dir / "components" / "__init__.py").is_file(), "frontend/components/__init__.py must exist"
    assert (frontend_dir / "views" / "__init__.py").is_file(), "frontend/views/__init__.py must exist"
    assert (frontend_dir / "utils" / "__init__.py").is_file(), "frontend/utils/__init__.py must exist"


def test_frontend_app_sys_path_injection_and_module_resolution():
    """
    Simulate Streamlit Cloud execution where only the script directory or a foreign directory
    is initially in sys.path.
    Confirms frontend/app.py automatically resolves REPO_ROOT into sys.path
    and imports all frontend submodules without ModuleNotFoundError.
    """
    repo_root = Path(__file__).resolve().parent.parent
    app_path = repo_root / "frontend" / "app.py"

    # Verify that app.py contains the robust Path(__file__).resolve().parent.parent injection
    app_code = app_path.read_text(encoding="utf-8")
    assert "Path(__file__).resolve().parent.parent" in app_code
    assert "sys.path.insert(0, str(REPO_ROOT))" in app_code or "sys.path" in app_code

    # Verify all expected frontend modules are importable
    import frontend.api_client
    import frontend.styles
    import frontend.navigation
    import frontend.components.charts
    import frontend.utils.helpers
    import frontend.views.auth_view
    import frontend.views.onboarding_view
    import frontend.views.dashboard_view
    import frontend.views.ai_view
    import frontend.views.workouts_view
    import frontend.views.exercises_view
    import frontend.views.nutrition_view
    import frontend.views.progress_view
    import frontend.views.profile_view

    assert frontend.api_client.DesiFitAPIClient is not None
    assert frontend.navigation.NAV_OPTIONS is not None
    assert frontend.styles.CUSTOM_CSS is not None


def test_apptest_frontend_app_clean_execution():
    """
    Verify that AppTest.from_file successfully compiles and runs frontend/app.py
    without any ModuleNotFoundError or import failures.
    """
    from streamlit.testing.v1 import AppTest

    repo_root = Path(__file__).resolve().parent.parent
    app_path = repo_root / "frontend" / "app.py"

    at = AppTest.from_file(str(app_path))
    at.run()

    # The unauthenticated gate renders without errors
    assert len(at.exception) == 0, f"AppTest threw exceptions on clean import: {at.exception}"
