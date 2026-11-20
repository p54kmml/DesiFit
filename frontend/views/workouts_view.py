import streamlit as st
from datetime import date
from frontend.api_client import DesiFitAPIClient


def render_workouts_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                Workout <span style="color: #a3e635;">Management</span> 🏋️‍♂️
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Design targeted workout plans, record completed training sessions, and monitor progression.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_log, tab_plans, tab_history = st.tabs(["📝 Log Completed Workout", "📋 Workout Plans", "📜 History & Logs"])

    # Load exercises list for dropdowns
    try:
        exercises = api.get_exercises()
        exercise_options = {f"{ex['name']} ({ex['muscle_group']})": ex["id"] for ex in exercises}
    except Exception as e:
        exercises = []
        exercise_options = {}
        st.error(f"Error loading exercises: {str(e)}")

    # ==========================================
    # TAB 1: LOG A COMPLETED WORKOUT
    # ==========================================
    with tab_log:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Record a Completed Workout</h3>", unsafe_allow_html=True)
        with st.form("log_workout_form"):
            w_col1, w_col2, w_col3 = st.columns([2, 1, 1])
            with w_col1:
                title = st.text_input("Workout Title / Focus", value="Upper Body Hypertrophy", placeholder="e.g. Chest & Triceps Blast")
            with w_col2:
                duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, value=50, step=5)
            with w_col3:
                w_date = st.date_input("Date of Workout", value=date.today())

            notes = st.text_area("Session Notes (optional)", placeholder="Felt energized, hit a PR on bench press!", height=70)

            st.markdown("<h4 style='color: #a3e635; margin: 15px 0 10px 0;'>Add Exercises Performed</h4>", unsafe_allow_html=True)

            # Up to 4 exercises in this quick logging form
            logged_items = []
            for i in range(1, 4):
                st.markdown(f"<div style='font-size: 0.85rem; font-weight: 700; color: #8b949e;'>Exercise #{i}</div>", unsafe_allow_html=True)
                e_col1, e_col2, e_col3, e_col4 = st.columns([3, 1, 1, 1])
                with e_col1:
                    sel_name = st.selectbox(
                        f"Select Exercise #{i}",
                        options=["None"] + list(exercise_options.keys()),
                        index=i if i < len(exercise_options) else 0,
                        key=f"ex_sel_{i}",
                        label_visibility="collapsed"
                    )
                with e_col2:
                    sets = st.number_input(f"Sets #{i}", min_value=1, max_value=20, value=3, key=f"sets_{i}")
                with e_col3:
                    reps = st.number_input(f"Reps #{i}", min_value=1, max_value=100, value=10, key=f"reps_{i}")
                with e_col4:
                    wt = st.number_input(f"Weight (kg) #{i}", min_value=0.0, max_value=500.0, value=20.0 * i, step=2.5, key=f"wt_{i}")

                if sel_name != "None":
                    logged_items.append({
                        "exercise_id": exercise_options[sel_name],
                        "sets_completed": sets,
                        "reps_completed": reps,
                        "weight_kg": wt,
                        "notes": ""
                    })

            log_btn = st.form_submit_button("Save Completed Workout ✅", use_container_width=True)

            if log_btn:
                if not title:
                    st.error("Please enter a workout title.")
                elif not logged_items:
                    st.error("Please select at least one exercise.")
                else:
                    try:
                        api.record_workout_log({
                            "title": title,
                            "notes": notes,
                            "duration_minutes": duration,
                            "date": str(w_date),
                            "completed": True,
                            "logged_exercises": logged_items
                        })
                        st.success("Workout recorded successfully! Great effort! 🚀")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to record workout: {str(e)}")

    # ==========================================
    # TAB 2: WORKOUT PLANS
    # ==========================================
    with tab_plans:
        p_col1, p_col2 = st.columns([1.2, 1.0])

        with p_col1:
            st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Your Custom Workout Plans</h3>", unsafe_allow_html=True)
            try:
                plans = api.get_workout_plans()
            except Exception as e:
                plans = []
                st.error(f"Error fetching plans: {str(e)}")

            if not plans:
                st.info("You haven't created any custom workout plans yet. Use the form on the right to build one!")
            else:
                for plan in plans:
                    with st.expander(f"📋 {plan['title']} ({plan.get('goal', 'General')})", expanded=False):
                        st.write(f"**Difficulty:** {plan.get('difficulty')} | **Description:** {plan.get('description') or 'N/A'}")
                        st.markdown("<h5 style='color: #a3e635; margin-top: 10px;'>Exercises:</h5>", unsafe_allow_html=True)
                        for item in plan.get("exercises", []):
                            ex_info = item.get("exercise", {})
                            st.write(f"• **{ex_info.get('name', 'Exercise')}** ({ex_info.get('muscle_group')}) — {item['sets']} sets × {item['reps']} reps | Rest: {item['rest_seconds']}s")

                        if st.button("Delete Plan", key=f"del_plan_{plan['id']}", type="secondary"):
                            api.delete_workout_plan(plan["id"])
                            st.success("Plan deleted.")
                            st.rerun()

        with p_col2:
            st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Create New Plan</h3>", unsafe_allow_html=True)
            with st.form("create_plan_form"):
                p_title = st.text_input("Plan Name", placeholder="e.g. 3-Day Push Pull Legs")
                p_goal = st.selectbox("Target Goal", ["Muscle Gain", "Fat Loss", "Strength", "Endurance", "General Fitness"])
                p_diff = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
                p_desc = st.text_area("Plan Description", placeholder="Focus on progressive overload on compound lifts.", height=70)

                st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #a3e635; margin: 10px 0;'>Select Exercises for Plan:</div>", unsafe_allow_html=True)
                plan_exs = []
                for idx in range(1, 4):
                    sel_p_ex = st.selectbox(f"Exercise {idx}", ["None"] + list(exercise_options.keys()), key=f"p_ex_{idx}")
                    c_s, c_r, c_rest = st.columns(3)
                    with c_s:
                        s_val = st.number_input(f"Sets {idx}", min_value=1, max_value=10, value=3, key=f"p_s_{idx}")
                    with c_r:
                        r_val = st.number_input(f"Reps {idx}", min_value=1, max_value=50, value=12, key=f"p_r_{idx}")
                    with c_rest:
                        rst_val = st.number_input(f"Rest (s) {idx}", min_value=15, max_value=300, value=60, step=15, key=f"p_rst_{idx}")

                    if sel_p_ex != "None":
                        plan_exs.append({
                            "exercise_id": exercise_options[sel_p_ex],
                            "sets": s_val,
                            "reps": r_val,
                            "rest_seconds": rst_val,
                            "order_index": idx
                        })

                create_plan_btn = st.form_submit_button("Create Workout Plan 📋", use_container_width=True)

                if create_plan_btn:
                    if not p_title:
                        st.error("Please provide a plan name.")
                    elif not plan_exs:
                        st.error("Please add at least one exercise to the plan.")
                    else:
                        try:
                            api.create_workout_plan({
                                "title": p_title,
                                "description": p_desc,
                                "goal": p_goal,
                                "difficulty": p_diff,
                                "exercises": plan_exs
                            })
                            st.success(f"Plan '{p_title}' created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating plan: {str(e)}")

    # ==========================================
    # TAB 3: WORKOUT HISTORY & LOGS
    # ==========================================
    with tab_history:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Workout History Log</h3>", unsafe_allow_html=True)
        try:
            logs = api.get_workout_logs()
        except Exception as e:
            logs = []
            st.error(f"Error fetching logs: {str(e)}")

        if not logs:
            st.info("No workout logs found. Record your workouts in the 'Log Completed Workout' tab!")
        else:
            for l in logs:
                with st.expander(f"🏋️ {l['title']} — {l['date']} ({l['duration_minutes']} min)", expanded=False):
                    if l.get("notes"):
                        st.write(f"**Notes:** {l['notes']}")
                    st.markdown("**Exercises Completed:**")
                    for ex_item in l.get("logged_exercises", []):
                        ex_info = ex_item.get("exercise", {})
                        st.write(f"- **{ex_info.get('name', 'Exercise')}** ({ex_info.get('muscle_group')}): {ex_item['sets_completed']} sets × {ex_item['reps_completed']} reps @ {ex_item['weight_kg']} kg")

                    if st.button("Delete Workout Log", key=f"del_log_{l['id']}", type="secondary"):
                        api.delete_workout_log(l["id"])
                        st.success("Workout log deleted.")
                        st.rerun()
