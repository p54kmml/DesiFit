import streamlit as st

# Navigation Options and Semantic Page Aliases
NAV_OPTIONS = [
    "Dashboard",
    "AI Fitness Assistant",
    "Workout Planner",
    "Exercise Library",
    "Nutrition Tracker",
    "Body Progress",
    "User Profile"
]

PAGE_ALIASES = {
    "AI Coach": "AI Fitness Assistant",
    "Indian Diet Planner": "Nutrition Tracker",
    "Fitness Guides": "Exercise Library",
    "Profile & Tracking": "Body Progress",
    "Profile": "User Profile",
    "Tracking": "Body Progress"
}


def logout_user():
    """
    Cleanly log out the active user and reset navigation state without mutating instantiated widget keys.
    Pre-instantiation synchronization in app.py sets nav_radio cleanly before st.radio renders.
    """
    st.session_state["token"] = None
    st.session_state["user"] = None
    st.session_state["is_onboarded"] = False
    st.session_state["nav_page"] = "Dashboard"
