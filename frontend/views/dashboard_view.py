import streamlit as st
from html import escape
from frontend.api_client import DesiFitAPIClient
from frontend.styles import render_metric_card
from frontend.components.charts import (
    create_weekly_activity_chart,
    create_macro_donut_chart,
    create_weight_trend_chart
)


def render_dashboard_page(api: DesiFitAPIClient):
    try:
        stats = api.get_dashboard_stats()
    except Exception as e:
        st.error(f"Error loading dashboard statistics: {str(e)}")
        return

    # Header section
    user_name = escape(str(stats.get("full_name", "Athlete")))
    goal = escape(str(stats.get("fitness_goal", "General Fitness")))

    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #161b22 0%, #1f2833 100%); border: 1px solid #30363d; border-radius: 12px; padding: 22px 26px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                    Welcome back, <span style="color: #a3e635;">{user_name}</span>! 💪
                </h1>
                <p style="color: #8b949e; margin: 5px 0 0 0; font-size: 0.95rem;">
                    Target Goal: <span style="color: #f0f6fc; font-weight: 600;">{goal}</span> | Stay consistent today!
                </p>
            </div>
            <div style="margin-top: 10px;">
                <span class="desifit-badge">DesiFit Active</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Key Metrics Cards Row
    c1, c2, c3, c4 = st.columns(4)

    curr_wt = stats.get("current_weight_kg", 0.0)
    targ_wt = stats.get("target_weight_kg", 0.0)
    wt_diff = round(curr_wt - targ_wt, 1)
    wt_sub = f"{abs(wt_diff)} kg to target" if wt_diff != 0 else "Goal achieved! 🎉"

    cal_consumed = stats.get("today_calories_consumed", 0.0)
    cal_target = stats.get("daily_calorie_target", 2200)
    cal_pct = int((cal_consumed / cal_target) * 100) if cal_target > 0 else 0

    pro_consumed = stats.get("today_protein_consumed", 0.0)
    pro_target = stats.get("daily_protein_target", 140.0)
    pro_pct = int((pro_consumed / pro_target) * 100) if pro_target > 0 else 0

    total_w = stats.get("total_workouts_completed", 0)
    week_w = stats.get("this_week_workouts_count", 0)

    with c1:
        st.markdown(render_metric_card("Current Weight", f"{curr_wt} kg", f"Target: {targ_wt} kg ({wt_sub})", "#38bdf8"), unsafe_allow_html=True)
    with c2:
        st.markdown(render_metric_card("Daily Calories", f"{int(cal_consumed)} kcal", f"{cal_pct}% of {cal_target} kcal target", "#a3e635"), unsafe_allow_html=True)
    with c3:
        st.markdown(render_metric_card("Daily Protein", f"{int(pro_consumed)}g", f"{pro_pct}% of {int(pro_target)}g target", "#fbbf24"), unsafe_allow_html=True)
    with c4:
        st.markdown(render_metric_card("Workouts Done", f"{total_w}", f"{week_w} completed this week", "#ec4899"), unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Quick Action Buttons
    st.markdown("<h4 style='color: #ffffff; margin-bottom: 12px; font-weight: 700;'>⚡ Quick Actions</h4>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)

    with q1:
        if st.button("🤖 Ask DesiFit AI", use_container_width=True):
            st.session_state["nav_page"] = "AI Fitness Assistant"
            st.rerun()
    with q2:
        if st.button("🏋️ Log Workout", use_container_width=True):
            st.session_state["nav_page"] = "Workout Planner"
            st.rerun()
    with q3:
        if st.button("🥗 Log Meal / Food", use_container_width=True):
            st.session_state["nav_page"] = "Nutrition Tracker"
            st.rerun()
    with q4:
        if st.button("📏 Track Weight / Body", use_container_width=True):
            st.session_state["nav_page"] = "Body Progress"
            st.rerun()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Charts Row
    ch1, ch2 = st.columns([1.6, 1.0])

    with ch1:
        st.markdown("<h4 style='color: #ffffff; margin-bottom: 10px; font-weight: 700;'>📅 Weekly Training Frequency</h4>", unsafe_allow_html=True)
        weekly_act = stats.get("weekly_activity", [])
        if weekly_act:
            fig_act = create_weekly_activity_chart(weekly_act)
            st.plotly_chart(fig_act, use_container_width=True)
        else:
            st.info("No workout activity recorded in the past 7 days.")

    with ch2:
        st.markdown("<h4 style='color: #ffffff; margin-bottom: 10px; font-weight: 700;'>🍎 Today's Macro Distribution</h4>", unsafe_allow_html=True)
        # Fetch today's summary for macro details
        try:
            summary = api.get_daily_nutrition_summary()
            fig_macro = create_macro_donut_chart(
                summary.get("protein_consumed_g", 0),
                summary.get("carbs_consumed_g", 0),
                summary.get("fat_consumed_g", 0)
            )
            st.plotly_chart(fig_macro, use_container_width=True)
        except Exception:
            st.info("Log meals to view today's macro distribution.")

    # Recent Activity Row
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    r1, r2 = st.columns(2)

    with r1:
        st.markdown("<h4 style='color: #ffffff; margin-bottom: 10px; font-weight: 700;'>🏋️ Recent Completed Workouts</h4>", unsafe_allow_html=True)
        recent_w = stats.get("recent_workouts", [])
        if recent_w:
            for w in recent_w[:4]:
                workout_title = escape(str(w.get("title", "Workout")))
                st.markdown(
                    f"""
                    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #ffffff;">{workout_title}</span>
                            <span style="font-size: 0.8rem; color: #a3e635; font-weight: 600;">{w.get('duration_minutes')} mins</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #8b949e; margin-top: 4px;">
                            Date: {w.get('date')} | {len(w.get('logged_exercises', []))} exercises completed
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No workouts logged yet. Start by logging your first session!")

    with r2:
        st.markdown("<h4 style='color: #ffffff; margin-bottom: 10px; font-weight: 700;'>📈 Recent Body Measurements</h4>", unsafe_allow_html=True)
        recent_m = stats.get("recent_measurements", [])
        if recent_m:
            for m in recent_m[:4]:
                notes_str = f" — {escape(str(m.get('notes')))}" if m.get("notes") else ""
                st.markdown(
                    f"""
                    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 700; color: #38bdf8;">Weight: {m.get('weight_kg')} kg</span>
                            <span style="font-size: 0.8rem; color: #8b949e;">{m.get('date')}</span>
                        </div>
                        <div style="font-size: 0.82rem; color: #8b949e; margin-top: 4px;">
                            Waist: {m.get('waist_cm') or '-'} cm | Chest: {m.get('chest_cm') or '-'} cm{notes_str}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No body measurements recorded yet. Track your weight today!")
