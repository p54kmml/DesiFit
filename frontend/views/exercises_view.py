import streamlit as st
from html import escape
from frontend.api_client import DesiFitAPIClient


def render_exercises_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                Exercise <span style="color: #a3e635;">Library</span> 📚
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Browse scientifically approved exercises categorized by muscle group with form instructions.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Filter & Search bar
    f_col1, f_col2, f_col3 = st.columns([2, 2, 1.2])

    muscle_options = ["All", "Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs", "Abs"]

    with f_col1:
        selected_muscle = st.selectbox("Filter by Muscle Group", muscle_options, index=0)
    with f_col2:
        search_term = st.text_input("Search Exercise by Name", placeholder="e.g. Bench Press, Squat, Curl...")
    with f_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        show_add_modal = st.checkbox("➕ Add Custom Exercise", value=False)

    # Add custom exercise form expander
    if show_add_modal:
        with st.expander("➕ Register a New Custom Exercise", expanded=True):
            with st.form("custom_exercise_form"):
                c_name = st.text_input("Exercise Name", placeholder="e.g. Bulgarian Split Squat")
                c_muscle = st.selectbox("Target Muscle Group", ["Chest", "Back", "Shoulders", "Biceps", "Triceps", "Legs", "Abs", "Cardio"])
                c_eq = st.text_input("Equipment Required", placeholder="e.g. Dumbbells & Bench")
                c_diff = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
                c_inst = st.text_area("Execution Instructions & Form Cues", placeholder="Step-by-step guidance on posture, breathing, and range of motion.")
                add_ex_btn = st.form_submit_button("Save Exercise to Library 💾", use_container_width=True)

                if add_ex_btn:
                    if not c_name or not c_muscle:
                        st.error("Please provide both name and muscle group.")
                    else:
                        try:
                            api.create_exercise({
                                "name": c_name,
                                "muscle_group": c_muscle,
                                "equipment": c_eq or "Gym Equipment",
                                "difficulty": c_diff,
                                "instructions": c_inst
                            })
                            st.success(f"Exercise '{c_name}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding exercise: {str(e)}")

    # Fetch and display exercises
    try:
        exercises = api.get_exercises(
            muscle_group=None if selected_muscle == "All" else selected_muscle,
            search=search_term if search_term else None
        )
    except Exception as e:
        exercises = []
        st.error(f"Error fetching exercises: {str(e)}")

    st.markdown(f"<div style='color: #8b949e; font-size: 0.9rem; margin-bottom: 15px;'>Showing <b>{len(exercises)}</b> exercises</div>", unsafe_allow_html=True)

    if not exercises:
        st.info("No exercises found matching your criteria.")
    else:
        # Display in 2 responsive columns
        cols = st.columns(2)
        for idx, ex in enumerate(exercises):
            col = cols[idx % 2]
            with col:
                diff_color = {
                    "Beginner": "#22c55e",
                    "Intermediate": "#38bdf8",
                    "Advanced": "#f43f5e"
                }.get(ex.get("difficulty"), "#a3e635")

                custom_badge = "<span style='background: rgba(163,230,53,0.15); color: #a3e635; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; margin-left: 6px;'>CUSTOM</span>" if ex.get("is_custom") else ""
                ex_name = escape(str(ex.get("name", "Exercise")))
                muscle_group = escape(str(ex.get("muscle_group", "General")))
                difficulty = escape(str(ex.get("difficulty", "All Levels")))
                equipment = escape(str(ex.get("equipment") or "General"))
                instructions = escape(str(ex.get("instructions") or "Perform with strict form and full range of motion."))

                st.markdown(
                    f"""
                    <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px; margin-bottom: 16px; min-height: 180px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h4 style="color: #ffffff; margin: 0; font-size: 1.1rem; font-weight: 700;">
                                    {ex_name} {custom_badge}
                                </h4>
                                <div style="color: #a3e635; font-size: 0.82rem; font-weight: 600; margin-top: 4px;">
                                    🎯 {muscle_group}
                                </div>
                            </div>
                            <span style="background: rgba(255,255,255,0.06); color: {diff_color}; font-size: 0.75rem; padding: 3px 8px; border-radius: 6px; font-weight: 600; border: 1px solid {diff_color}44;">
                                {difficulty}
                            </span>
                        </div>
                        <div style="font-size: 0.8rem; color: #8b949e; margin: 8px 0;">
                            <b>Equipment:</b> {equipment}
                        </div>
                        <div style="font-size: 0.85rem; color: #c9d1d9; line-height: 1.5; margin-top: 8px; border-top: 1px solid #21262d; padding-top: 8px;">
                            {instructions}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
