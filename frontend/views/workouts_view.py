import streamlit as st
from datetime import date
from frontend.api_client import DesiFitAPIClient


def add_plan_exercise():
    """Callback to add a new exercise row to the Workout Plan builder."""
    if "plan_exercise_row_ids" not in st.session_state:
        init_cnt = st.session_state.get("plan_exercise_count", 3)
        init_cnt = max(1, min(50, init_cnt))
        st.session_state["plan_exercise_row_ids"] = list(range(1, init_cnt + 1))
        st.session_state["plan_next_row_id"] = init_cnt + 1

    row_ids = st.session_state["plan_exercise_row_ids"]
    if len(row_ids) < 50:
        new_id = st.session_state.get("plan_next_row_id", max(row_ids, default=0) + 1)
        st.session_state["plan_next_row_id"] = new_id + 1
        st.session_state["plan_exercise_row_ids"].append(new_id)
        st.session_state["plan_exercise_count"] = len(st.session_state["plan_exercise_row_ids"])
        st.session_state[f"p_ex_{new_id}"] = "None"
        st.session_state[f"p_s_{new_id}"] = 3
        st.session_state[f"p_r_{new_id}"] = 12
        st.session_state[f"p_rst_{new_id}"] = 60
        st.session_state["workout_active_tab"] = "📋 Workout Planner"


def remove_plan_exercise(row_id: int):
    """Callback to remove a specific exercise row from the Workout Plan builder."""
    if "plan_exercise_row_ids" not in st.session_state:
        init_cnt = st.session_state.get("plan_exercise_count", 3)
        init_cnt = max(1, min(50, init_cnt))
        st.session_state["plan_exercise_row_ids"] = list(range(1, init_cnt + 1))
        st.session_state["plan_next_row_id"] = init_cnt + 1

    row_ids = st.session_state["plan_exercise_row_ids"]
    if len(row_ids) > 1 and row_id in row_ids:
        row_ids.remove(row_id)
        st.session_state.pop(f"p_ex_{row_id}", None)
        st.session_state.pop(f"p_s_{row_id}", None)
        st.session_state.pop(f"p_r_{row_id}", None)
        st.session_state.pop(f"p_rst_{row_id}", None)
        st.session_state["plan_exercise_count"] = len(row_ids)
        st.session_state["workout_active_tab"] = "📋 Workout Planner"
    elif len(row_ids) == 1 and row_id in row_ids:
        st.session_state[f"p_ex_{row_id}"] = "None"
        st.session_state["workout_active_tab"] = "📋 Workout Planner"


def add_log_exercise():
    """Callback to add a new exercise row to the Workout Log recorder."""
    if "log_exercise_row_ids" not in st.session_state:
        init_cnt = st.session_state.get("log_exercise_count", 3)
        init_cnt = max(1, min(50, init_cnt))
        st.session_state["log_exercise_row_ids"] = list(range(1, init_cnt + 1))
        st.session_state["log_next_row_id"] = init_cnt + 1

    row_ids = st.session_state["log_exercise_row_ids"]
    if len(row_ids) < 50:
        new_id = st.session_state.get("log_next_row_id", max(row_ids, default=0) + 1)
        st.session_state["log_next_row_id"] = new_id + 1
        st.session_state["log_exercise_row_ids"].append(new_id)
        st.session_state["log_exercise_count"] = len(st.session_state["log_exercise_row_ids"])
        st.session_state[f"log_ex_{new_id}"] = "None"
        st.session_state[f"log_s_{new_id}"] = 3
        st.session_state[f"log_r_{new_id}"] = 10
        st.session_state[f"log_w_{new_id}"] = 20.0
        st.session_state["workout_active_tab"] = "📝 Record Completed Workout"


def remove_log_exercise(row_id: int):
    """Callback to remove a specific exercise row from the Workout Log recorder."""
    if "log_exercise_row_ids" not in st.session_state:
        init_cnt = st.session_state.get("log_exercise_count", 3)
        init_cnt = max(1, min(50, init_cnt))
        st.session_state["log_exercise_row_ids"] = list(range(1, init_cnt + 1))
        st.session_state["log_next_row_id"] = init_cnt + 1

    row_ids = st.session_state["log_exercise_row_ids"]
    if len(row_ids) > 1 and row_id in row_ids:
        row_ids.remove(row_id)
        st.session_state.pop(f"log_ex_{row_id}", None)
        st.session_state.pop(f"log_s_{row_id}", None)
        st.session_state.pop(f"log_r_{row_id}", None)
        st.session_state.pop(f"log_w_{row_id}", None)
        st.session_state["log_exercise_count"] = len(row_ids)
        st.session_state["workout_active_tab"] = "📝 Record Completed Workout"
    elif len(row_ids) == 1 and row_id in row_ids:
        st.session_state[f"log_ex_{row_id}"] = "None"
        st.session_state["workout_active_tab"] = "📝 Record Completed Workout"


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

    # Tab configuration: "📋 Workout Planner" is Tab 0 (primary default)
    tab_aliases = {
        "📋 Workout Plans": "📋 Workout Planner",
        "Workout Plans": "📋 Workout Planner",
        "Workout Planner": "📋 Workout Planner",
        "📝 Log Completed Workout": "📝 Record Completed Workout",
        "Log Completed Workout": "📝 Record Completed Workout",
        "Record Completed Workout": "📝 Record Completed Workout",
        "History & Logs": "📜 History & Logs",
    }
    tabs_list = ["📋 Workout Planner", "📝 Record Completed Workout", "📜 History & Logs"]
    raw_active_tab = st.session_state.get("workout_active_tab", "📋 Workout Planner")
    active_tab = tab_aliases.get(raw_active_tab, "📋 Workout Planner")
    if active_tab not in tabs_list:
        active_tab = "📋 Workout Planner"
    st.session_state["workout_active_tab"] = active_tab

    try:
        tab_planner, tab_log, tab_history = st.tabs(tabs_list, default=active_tab)
    except TypeError:
        tab_planner, tab_log, tab_history = st.tabs(tabs_list)

    # Load exercises list for dropdowns
    try:
        exercises = api.get_exercises()
        exercise_options = {f"{ex['name']} ({ex['muscle_group']})": ex["id"] for ex in exercises}
        options_list = ["None"] + list(exercise_options.keys())
    except Exception as e:
        exercises = []
        exercise_options = {}
        options_list = ["None"]
        st.error(f"Error loading exercises: {str(e)}")

    # ==========================================
    # TAB 1: WORKOUT PLANNER (PRIMARY)
    # ==========================================
    with tab_planner:
        p_col1, p_col2 = st.columns([1.1, 1.2])

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
                    plan_exercises = plan.get("exercises", [])
                    ex_count = len(plan_exercises)
                    with st.expander(f"📋 {plan['title']} ({plan.get('goal', 'General')}) — {ex_count} Exercise(s)", expanded=False):
                        st.write(f"**Difficulty:** {plan.get('difficulty')} | **Description:** {plan.get('description') or 'N/A'}")
                        st.markdown("<h5 style='color: #a3e635; margin-top: 10px;'>Exercises:</h5>", unsafe_allow_html=True)
                        for item in plan_exercises:
                            ex_info = item.get("exercise", {})
                            st.write(f"• **{ex_info.get('name', 'Exercise')}** ({ex_info.get('muscle_group')}) — {item['sets']} sets × {item['reps']} reps | Rest: {item['rest_seconds']}s")

                        b1, b2 = st.columns([1, 1])
                        with b1:
                            if st.button("✏️ Edit Plan", key=f"edit_plan_{plan['id']}", use_container_width=True):
                                st.session_state["editing_plan_id"] = plan["id"]
                                st.session_state["p_title_input"] = plan.get("title", "")
                                st.session_state["p_goal_input"] = plan.get("goal", "Muscle Gain")
                                st.session_state["p_diff_input"] = plan.get("difficulty", "Intermediate")
                                st.session_state["p_desc_input"] = plan.get("description", "") or ""
                                n_ex = max(1, min(50, len(plan_exercises)))
                                st.session_state["plan_exercise_row_ids"] = list(range(1, n_ex + 1))
                                st.session_state["plan_next_row_id"] = n_ex + 1
                                st.session_state["plan_exercise_count"] = n_ex
                                # Pre-populate builder fields
                                for idx, p_item in enumerate(plan_exercises, start=1):
                                    e_inf = p_item.get("exercise", {})
                                    key_label = f"{e_inf.get('name')} ({e_inf.get('muscle_group')})"
                                    st.session_state[f"p_ex_{idx}"] = key_label if key_label in exercise_options else "None"
                                    st.session_state[f"p_s_{idx}"] = p_item.get("sets", 3)
                                    st.session_state[f"p_r_{idx}"] = p_item.get("reps", 12)
                                    st.session_state[f"p_rst_{idx}"] = p_item.get("rest_seconds", 60)
                                st.session_state["workout_active_tab"] = "📋 Workout Planner"
                                st.rerun()

                        with b2:
                            if st.button("🗑️ Delete Plan", key=f"del_plan_{plan['id']}", type="secondary", use_container_width=True):
                                api.delete_workout_plan(plan["id"])
                                if st.session_state.get("editing_plan_id") == plan["id"]:
                                    st.session_state.pop("editing_plan_id", None)
                                st.success("Plan deleted.")
                                st.session_state["workout_active_tab"] = "📋 Workout Planner"
                                st.rerun()

        with p_col2:
            is_editing = "editing_plan_id" in st.session_state and st.session_state["editing_plan_id"] is not None
            editing_id = st.session_state.get("editing_plan_id")

            if is_editing:
                st.markdown(f"<h3 style='color: #ffffff; margin-top: 0;'>✏️ Edit Workout Plan #{editing_id}</h3>", unsafe_allow_html=True)
                if st.button("✖️ Cancel Editing", key="btn_cancel_edit_plan", type="secondary"):
                    st.session_state.pop("editing_plan_id", None)
                    st.session_state.pop("p_title_input", None)
                    st.session_state.pop("p_desc_input", None)
                    st.session_state["plan_exercise_row_ids"] = [1, 2, 3]
                    st.session_state["plan_next_row_id"] = 4
                    st.session_state["plan_exercise_count"] = 3
                    for k in range(1, 100):
                        st.session_state.pop(f"p_ex_{k}", None)
                        st.session_state.pop(f"p_s_{k}", None)
                        st.session_state.pop(f"p_r_{k}", None)
                        st.session_state.pop(f"p_rst_{k}", None)
                    st.session_state["workout_active_tab"] = "📋 Workout Planner"
                    st.rerun()
            else:
                st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Create New Workout Plan</h3>", unsafe_allow_html=True)

            # Manage dynamic exercise rows using stable row IDs
            if "plan_exercise_row_ids" not in st.session_state:
                init_cnt = st.session_state.get("plan_exercise_count", 3)
                init_cnt = max(1, min(50, init_cnt))
                st.session_state["plan_exercise_row_ids"] = list(range(1, init_cnt + 1))
                st.session_state["plan_next_row_id"] = init_cnt + 1
            else:
                if not st.session_state["plan_exercise_row_ids"]:
                    st.session_state["plan_exercise_row_ids"] = [1]
                    st.session_state["plan_next_row_id"] = 2

            row_ids = st.session_state["plan_exercise_row_ids"]
            st.session_state["plan_exercise_count"] = len(row_ids)

            goal_opts = ["Muscle Gain", "Fat Loss", "Strength", "Endurance", "General Fitness"]
            diff_opts = ["Beginner", "Intermediate", "Advanced"]

            # Initialize builder values if not present
            if "p_title_input" not in st.session_state:
                st.session_state["p_title_input"] = ""
            if "p_goal_input" not in st.session_state:
                st.session_state["p_goal_input"] = "Muscle Gain"
            if "p_diff_input" not in st.session_state:
                st.session_state["p_diff_input"] = "Intermediate"
            if "p_desc_input" not in st.session_state:
                st.session_state["p_desc_input"] = ""

            p_title = st.text_input("Plan Name", key="p_title_input", placeholder="e.g. Upper Body Hypertrophy")
            p_goal = st.selectbox("Target Goal", goal_opts, key="p_goal_input")
            p_diff = st.selectbox("Difficulty", diff_opts, key="p_diff_input")
            p_desc = st.text_area("Plan Description", key="p_desc_input", placeholder="Comprehensive daily routine focusing on progressive overload and balanced muscle development.", height=70)

            # Header above exercises with current count and top Add button
            c_hdr, c_top_add = st.columns([1.8, 1.2])
            with c_hdr:
                st.markdown(
                    f"<div style='font-size: 0.95rem; font-weight: 700; color: #a3e635; margin-top: 6px;'>"
                    f"Plan Exercises ({len(row_ids)}/50)</div>",
                    unsafe_allow_html=True
                )
            with c_top_add:
                st.button(
                    "➕ Add Exercise",
                    key="btn_add_plan_exercise_top",
                    on_click=add_plan_exercise,
                    use_container_width=True,
                    type="secondary"
                )

            allow_plan_dups = st.checkbox("Allow duplicate exercises in plan", value=False, key="chk_allow_plan_dups")

            # Render dynamic exercise rows
            plan_exs = []
            for display_idx, r_id in enumerate(row_ids, start=1):
                st.markdown(f"<div style='font-size: 0.85rem; font-weight: 700; color: #8b949e; margin-top: 12px; margin-bottom: 2px;'>Exercise #{display_idx}</div>", unsafe_allow_html=True)

                if f"p_ex_{r_id}" not in st.session_state:
                    def_opt_idx = display_idx if display_idx < len(options_list) else 0
                    st.session_state[f"p_ex_{r_id}"] = options_list[def_opt_idx]

                r_col_drop, r_col_del = st.columns([4.2, 1.0])
                with r_col_drop:
                    sel_p_ex = st.selectbox(
                        f"Select Exercise #{display_idx}",
                        options=options_list,
                        key=f"p_ex_{r_id}",
                        label_visibility="collapsed"
                    )
                with r_col_del:
                    st.button(
                        "🗑️",
                        key=f"btn_del_row_{r_id}",
                        on_click=remove_plan_exercise,
                        args=(r_id,),
                        use_container_width=True,
                        help=f"Remove exercise #{display_idx}"
                    )

                c_s, c_r, c_rest = st.columns(3)
                with c_s:
                    if f"p_s_{r_id}" not in st.session_state:
                        st.session_state[f"p_s_{r_id}"] = 3
                    s_val = st.number_input(f"Sets #{display_idx}", min_value=1, max_value=20, key=f"p_s_{r_id}")
                with c_r:
                    if f"p_r_{r_id}" not in st.session_state:
                        st.session_state[f"p_r_{r_id}"] = 12
                    r_val = st.number_input(f"Reps #{display_idx}", min_value=1, max_value=100, key=f"p_r_{r_id}")
                with c_rest:
                    if f"p_rst_{r_id}" not in st.session_state:
                        st.session_state[f"p_rst_{r_id}"] = 60
                    rst_val = st.number_input(f"Rest (s) #{display_idx}", min_value=15, max_value=600, step=15, key=f"p_rst_{r_id}")

                if sel_p_ex != "None" and sel_p_ex in exercise_options:
                    plan_exs.append({
                        "exercise_id": exercise_options[sel_p_ex],
                        "exercise_name": sel_p_ex,
                        "sets": s_val,
                        "reps": r_val,
                        "rest_seconds": rst_val,
                        "order_index": len(plan_exs) + 1
                    })

            # Clearly visible + Add Exercise button below the exercise fields
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.button(
                "➕ Add Exercise",
                key="btn_add_plan_slot",
                on_click=add_plan_exercise,
                use_container_width=True,
                type="secondary"
            )

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            submit_btn_label = "💾 Update Workout Plan" if is_editing else "📋 Create Workout Plan"
            if st.button(submit_btn_label, key="btn_save_workout_plan", type="primary", use_container_width=True):
                p_title_clean = st.session_state.get("p_title_input", "").strip()
                if not p_title_clean:
                    st.error("Please provide a plan name.")
                elif not plan_exs:
                    st.error("Please select at least one exercise for the plan (change slot dropdown from 'None').")
                elif len(plan_exs) > 50:
                    st.error("A workout plan can contain a maximum of 50 exercises.")
                else:
                    chosen_plan_ids = [it["exercise_id"] for it in plan_exs]
                    if len(chosen_plan_ids) != len(set(chosen_plan_ids)) and not allow_plan_dups:
                        seen_p = set()
                        dups_p = {it["exercise_name"] for it in plan_exs if it["exercise_id"] in seen_p or seen_p.add(it["exercise_id"])}
                        dup_str_p = ", ".join(dups_p)
                        st.error(f"Duplicate exercises detected in your plan ({dup_str_p}). Please ensure each exercise is unique or check 'Allow duplicate exercises in plan'.")
                    else:
                        clean_plan_items = [
                            {
                                "exercise_id": it["exercise_id"],
                                "sets": it["sets"],
                                "reps": it["reps"],
                                "rest_seconds": it["rest_seconds"],
                                "order_index": i + 1
                            }
                            for i, it in enumerate(plan_exs)
                        ]
                        plan_payload = {
                            "title": p_title_clean,
                            "description": st.session_state.get("p_desc_input", ""),
                            "goal": st.session_state.get("p_goal_input", "Muscle Gain"),
                            "difficulty": st.session_state.get("p_diff_input", "Intermediate"),
                            "exercises": clean_plan_items
                        }
                        try:
                            if is_editing:
                                api.update_workout_plan(editing_id, plan_payload)
                                st.session_state.pop("editing_plan_id", None)
                                st.success(f"Plan '{p_title_clean}' updated successfully with {len(clean_plan_items)} exercises!")
                            else:
                                api.create_workout_plan(plan_payload)
                                st.success(f"Plan '{p_title_clean}' created successfully with {len(clean_plan_items)} exercises!")

                            # Reset builder inputs
                            st.session_state["p_title_input"] = ""
                            st.session_state["p_desc_input"] = ""
                            st.session_state["plan_exercise_row_ids"] = [1, 2, 3]
                            st.session_state["plan_next_row_id"] = 4
                            st.session_state["plan_exercise_count"] = 3
                            for k in range(1, 100):
                                st.session_state.pop(f"p_ex_{k}", None)
                                st.session_state.pop(f"p_s_{k}", None)
                                st.session_state.pop(f"p_r_{k}", None)
                                st.session_state.pop(f"p_rst_{k}", None)
                            st.session_state["workout_active_tab"] = "📋 Workout Planner"
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving plan: {str(e)}")

    # ==========================================
    # TAB 2: RECORD COMPLETED WORKOUT
    # ==========================================
    with tab_log:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Record a Completed Workout</h3>", unsafe_allow_html=True)

        # Dynamic, user-defined exercise rows using stable row IDs (1-50 exercises)
        if "log_exercise_row_ids" not in st.session_state:
            init_cnt = st.session_state.get("log_exercise_count", 3)
            init_cnt = max(1, min(50, init_cnt))
            st.session_state["log_exercise_row_ids"] = list(range(1, init_cnt + 1))
            st.session_state["log_next_row_id"] = init_cnt + 1
        else:
            if not st.session_state["log_exercise_row_ids"]:
                st.session_state["log_exercise_row_ids"] = [1]
                st.session_state["log_next_row_id"] = 2

        log_row_ids = st.session_state["log_exercise_row_ids"]
        st.session_state["log_exercise_count"] = len(log_row_ids)

        if "log_title_input" not in st.session_state:
            st.session_state["log_title_input"] = "Full Training Session"
        if "log_duration_input" not in st.session_state:
            st.session_state["log_duration_input"] = 60
        if "log_date_input" not in st.session_state:
            st.session_state["log_date_input"] = date.today()
        if "log_notes_input" not in st.session_state:
            st.session_state["log_notes_input"] = ""

        w_col1, w_col2, w_col3 = st.columns([2, 1, 1])
        with w_col1:
            title = st.text_input("Workout Title / Focus", key="log_title_input", placeholder="e.g. Chest & Triceps Blast")
        with w_col2:
            duration = st.number_input("Duration (minutes)", min_value=5, max_value=240, step=5, key="log_duration_input")
        with w_col3:
            w_date = st.date_input("Date of Workout", key="log_date_input")

        notes = st.text_area("Session Notes (optional)", key="log_notes_input", placeholder="Felt energized, great pump, progressive overload achieved!", height=70)

        st.markdown(
            f"<div style='font-size: 1.05rem; font-weight: 700; color: #a3e635; margin: 15px 0 6px 0;'>"
            f"Exercises Performed ({len(log_row_ids)}/50)</div>",
            unsafe_allow_html=True
        )
        allow_log_duplicates = st.checkbox(
            "Allow duplicate exercises (e.g. multiple distinct set protocols or supersets)",
            value=False,
            key="chk_allow_log_dups"
        )

        logged_items = []
        for display_idx, r_id in enumerate(log_row_ids, start=1):
            st.markdown(f"<div style='font-size: 0.85rem; font-weight: 700; color: #8b949e; margin-top: 10px; margin-bottom: 2px;'>Exercise #{display_idx}</div>", unsafe_allow_html=True)
            e_col_drop, e_col_del = st.columns([4.2, 1.0])

            if f"log_ex_{r_id}" not in st.session_state:
                def_idx = display_idx if display_idx < len(options_list) else 0
                st.session_state[f"log_ex_{r_id}"] = options_list[def_idx]

            with e_col_drop:
                sel_name = st.selectbox(
                    f"Select Exercise #{display_idx}",
                    options=options_list,
                    key=f"log_ex_{r_id}",
                    label_visibility="collapsed"
                )
            with e_col_del:
                st.button(
                    "🗑️",
                    key=f"btn_del_log_{r_id}",
                    on_click=remove_log_exercise,
                    args=(r_id,),
                    use_container_width=True,
                    help=f"Remove exercise #{display_idx}"
                )

            e_s, e_r, e_w = st.columns(3)
            with e_s:
                if f"log_s_{r_id}" not in st.session_state:
                    st.session_state[f"log_s_{r_id}"] = 3
                sets = st.number_input(f"Sets #{display_idx}", min_value=1, max_value=20, key=f"log_s_{r_id}")
            with e_r:
                if f"log_r_{r_id}" not in st.session_state:
                    st.session_state[f"log_r_{r_id}"] = 10
                reps = st.number_input(f"Reps #{display_idx}", min_value=1, max_value=100, key=f"log_r_{r_id}")
            with e_w:
                if f"log_w_{r_id}" not in st.session_state:
                    st.session_state[f"log_w_{r_id}"] = float(15.0 + (display_idx * 2.5))
                wt = st.number_input(f"Weight (kg) #{display_idx}", min_value=0.0, max_value=500.0, step=2.5, key=f"log_w_{r_id}")

            if sel_name != "None" and sel_name in exercise_options:
                logged_items.append({
                    "exercise_id": exercise_options[sel_name],
                    "exercise_name": sel_name,
                    "sets_completed": sets,
                    "reps_completed": reps,
                    "weight_kg": wt,
                    "notes": ""
                })

        # Clearly visible + Add Exercise button below the exercise fields
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.button(
            "➕ Add Exercise",
            key="btn_add_log_slot",
            on_click=add_log_exercise,
            use_container_width=True,
            type="secondary"
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("Save Completed Workout ✅", key="btn_save_workout_log", type="primary", use_container_width=True):
            clean_title = (title or "").strip()
            if not clean_title:
                st.error("Please enter a workout title.")
            elif not logged_items:
                st.error("Please select at least one exercise (change slot dropdown from 'None').")
            else:
                chosen_ids = [it["exercise_id"] for it in logged_items]
                if len(chosen_ids) != len(set(chosen_ids)) and not allow_log_duplicates:
                    seen = set()
                    dups = {it["exercise_name"] for it in logged_items if it["exercise_id"] in seen or seen.add(it["exercise_id"])}
                    dup_str = ", ".join(dups)
                    st.error(f"Duplicate exercises detected ({dup_str}). Please select unique exercises or check 'Allow duplicate exercises'.")
                else:
                    try:
                        clean_items = [
                            {
                                "exercise_id": it["exercise_id"],
                                "sets_completed": it["sets_completed"],
                                "reps_completed": it["reps_completed"],
                                "weight_kg": it["weight_kg"],
                                "notes": it["notes"]
                            }
                            for it in logged_items
                        ]
                        api.record_workout_log({
                            "title": clean_title,
                            "notes": notes,
                            "duration_minutes": duration,
                            "date": str(w_date),
                            "completed": True,
                            "logged_exercises": clean_items
                        })
                        st.success(f"Workout recorded successfully with {len(clean_items)} exercises! Great effort! 🚀")
                        # Reset inputs
                        st.session_state["log_title_input"] = "Full Training Session"
                        st.session_state["log_duration_input"] = 60
                        st.session_state["log_date_input"] = date.today()
                        st.session_state["log_notes_input"] = ""
                        st.session_state["log_exercise_row_ids"] = [1, 2, 3]
                        st.session_state["log_next_row_id"] = 4
                        st.session_state["log_exercise_count"] = 3
                        for k in range(1, 100):
                            st.session_state.pop(f"log_ex_{k}", None)
                            st.session_state.pop(f"log_s_{k}", None)
                            st.session_state.pop(f"log_r_{k}", None)
                            st.session_state.pop(f"log_w_{k}", None)
                        st.session_state["workout_active_tab"] = "📝 Record Completed Workout"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to record workout: {str(e)}")

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
                logged_exs = l.get("logged_exercises", [])
                with st.expander(f"🏋️ {l['title']} — {l['date']} ({l['duration_minutes']} min, {len(logged_exs)} exercise(s))", expanded=False):
                    if l.get("notes"):
                        st.write(f"**Notes:** {l['notes']}")
                    st.markdown("**Exercises Completed:**")
                    for ex_item in logged_exs:
                        ex_info = ex_item.get("exercise", {})
                        st.write(f"- **{ex_info.get('name', 'Exercise')}** ({ex_info.get('muscle_group')}): {ex_item['sets_completed']} sets × {ex_item['reps_completed']} reps @ {ex_item['weight_kg']} kg")

                    if st.button("Delete Workout Log", key=f"del_log_{l['id']}", type="secondary"):
                        api.delete_workout_log(l["id"])
                        st.success("Workout log deleted.")
                        st.rerun()
