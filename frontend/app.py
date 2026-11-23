import sys
from pathlib import Path

# Ensure repository root is in sys.path before any frontend package imports execute
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import streamlit as st
from html import escape
from frontend.api_client import DesiFitAPIClient
from frontend.styles import CUSTOM_CSS, render_logo
from frontend.views.auth_view import render_auth_page
from frontend.views.onboarding_view import render_onboarding_page
from frontend.views.dashboard_view import render_dashboard_page
from frontend.views.ai_view import render_ai_page
from frontend.views.workouts_view import render_workouts_page
from frontend.views.exercises_view import render_exercises_page
from frontend.views.nutrition_view import render_nutrition_page
from frontend.views.progress_view import render_progress_page
from frontend.views.profile_view import render_profile_page

# Configure Streamlit page
st.set_page_config(
    page_title="DesiFit – AI Fitness Companion",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global dark / lime SaaS stylesheet
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

from frontend.navigation import NAV_OPTIONS, PAGE_ALIASES, logout_user

# Initialize Session State
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "is_onboarded" not in st.session_state:
    st.session_state["is_onboarded"] = False
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = "Dashboard"

# Normalize nav_page through aliases to ensure valid route
raw_nav = st.session_state.get("nav_page", "Dashboard")
normalized_nav = PAGE_ALIASES.get(raw_nav, raw_nav)
if normalized_nav not in NAV_OPTIONS:
    normalized_nav = "Dashboard"
st.session_state["nav_page"] = normalized_nav

# Initialize API client
api = DesiFitAPIClient(token=st.session_state.get("token"))

# 1. Unauthenticated Gate
if not st.session_state["token"]:
    render_auth_page(api)

else:
    # Check onboarding status
    is_onboarded = st.session_state.get("is_onboarded")
    if not is_onboarded:
        try:
            prof = api.get_profile()
            is_onboarded = prof.get("is_onboarded", False)
            st.session_state["is_onboarded"] = is_onboarded
        except Exception:
            is_onboarded = False

    # 2. First-Time Onboarding Gate
    if not is_onboarded:
        # Show logout option in small banner or top corner
        col_space, col_exit = st.columns([6, 1])
        with col_exit:
            if st.button("🚪 Cancel / Log Out", use_container_width=True, type="secondary"):
                logout_user()
                st.rerun()

        render_onboarding_page(api)

    # 3. Main Application for Onboarded Users
    else:
        # Sidebar Navigation
        with st.sidebar:
            st.markdown(render_logo(size="normal"), unsafe_allow_html=True)

            user_info = st.session_state.get("user", {})
            full_name = escape(str(user_info.get("full_name", "Athlete"))) if user_info else "Athlete"
            username = escape(str(user_info.get("username", ""))) if user_info else ""

            st.markdown(
                f"""
                <div style="background-color: #21262d; border: 1px solid #30363d; border-radius: 8px; padding: 12px 14px; margin-bottom: 20px;">
                    <div style="font-size: 0.75rem; color: #8b949e; text-transform: uppercase; font-weight: 700;">Active Athlete</div>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #ffffff; margin-top: 2px;">{full_name}</div>
                    <div style="font-size: 0.8rem; color: #a3e635; margin-top: 2px;">@{username}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            def on_nav_change():
                selected_page = st.session_state["nav_radio"]
                st.session_state["nav_page"] = selected_page
                if selected_page == "Workout Planner":
                    st.session_state["workout_active_tab"] = "📋 Workout Planner"

            # Synchronize widget state before radio is instantiated if changed programmatically
            if "nav_radio" not in st.session_state or st.session_state["nav_radio"] != st.session_state.get("nav_page", "Dashboard"):
                st.session_state["nav_radio"] = st.session_state.get("nav_page", "Dashboard")

            st.radio(
                "Navigation",
                options=NAV_OPTIONS,
                key="nav_radio",
                on_change=on_nav_change,
                label_visibility="collapsed"
            )

            st.markdown("<hr style='border-color: #30363d; margin: 30px 0 20px 0;'>", unsafe_allow_html=True)

            # Logout button
            if st.button("🚪 Log Out", use_container_width=True, type="secondary"):
                logout_user()
                st.rerun()

            st.markdown(
                """
                <div style="text-align: center; color: #8b949e; font-size: 0.72rem; margin-top: 25px;">
                    DesiFit v1.0 • Commercial Fitness SaaS<br>FastAPI + Streamlit + SQLite
                </div>
                """,
                unsafe_allow_html=True
            )

        # Route Page
        page = st.session_state["nav_page"]
        if page == "Dashboard":
            render_dashboard_page(api)
        elif page == "AI Fitness Assistant":
            render_ai_page(api)
        elif page == "Workout Planner":
            render_workouts_page(api)
        elif page == "Exercise Library":
            render_exercises_page(api)
        elif page == "Nutrition Tracker":
            render_nutrition_page(api)
        elif page == "Body Progress":
            render_progress_page(api)
        elif page == "User Profile":
            render_profile_page(api)
