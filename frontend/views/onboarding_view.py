import streamlit as st
from frontend.api_client import DesiFitAPIClient
from frontend.styles import render_logo


def calculate_preview_macros(weight_kg, height_cm, age, gender, activity_level, goal):
    if not (weight_kg > 0 and height_cm > 0 and age > 0):
        return None, None, None, None, None

    # Mifflin-St Jeor Formula
    if gender.lower() == "female":
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) - 161.0
    else:
        bmr = (10.0 * weight_kg) + (6.25 * height_cm) - (5.0 * age) + 5.0

    multipliers = {
        "Sedentary (Little/no exercise)": 1.2,
        "Lightly Active (1-3 days/week)": 1.375,
        "Moderately Active (3-5 days/week)": 1.55,
        "Very Active (6-7 days/week)": 1.725,
        "Extremely Active (Physical job + training)": 1.9
    }
    multiplier = multipliers.get(activity_level, 1.4)
    tdee = bmr * multiplier

    goal_lower = goal.lower()
    if "fat loss" in goal_lower:
        cals = max(1300, int(tdee - 450))
        pro = round(weight_kg * 2.0, 1)
    elif "muscle" in goal_lower:
        cals = int(tdee + 300)
        pro = round(weight_kg * 2.0, 1)
    elif "strength" in goal_lower:
        cals = int(tdee + 200)
        pro = round(weight_kg * 1.8, 1)
    elif "endurance" in goal_lower:
        cals = int(tdee + 150)
        pro = round(weight_kg * 1.5, 1)
    else:
        cals = int(tdee)
        pro = round(weight_kg * 1.6, 1)

    fat = round((cals * 0.25) / 9.0, 1)
    carbs = round(max(0, cals - (fat * 9.0 + pro * 4.0)) / 4.0, 1)
    return int(bmr), int(tdee), cals, pro, carbs, fat


def render_onboarding_page(api: DesiFitAPIClient):
    col1, col2, col3 = st.columns([1, 2.8, 1])

    with col2:
        st.markdown(render_logo(size="large"), unsafe_allow_html=True)

        user_info = st.session_state.get("user", {})
        full_name = user_info.get("full_name", "Athlete")

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #161b22 0%, #1f2833 100%); border: 1px solid #30363d; border-top: 3px solid #a3e635; border-radius: 12px; padding: 22px 26px; margin-bottom: 25px;">
                <h2 style="color: #ffffff; margin: 0; font-size: 1.6rem; font-weight: 800;">
                    Welcome, <span style="color: #a3e635;">{full_name}</span>! 👋
                </h2>
                <p style="color: #8b949e; margin: 8px 0 0 0; font-size: 0.95rem; line-height: 1.5;">
                    Please complete your <b>personal fitness onboarding baseline</b>. DesiFit is a multi-user platform—your metrics, calorie targets, workout volume, and nutrition recommendations will be calibrated specifically to your body.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.form("onboarding_form"):
            st.markdown("<h4 style='color: #ffffff; margin-top: 0;'>1. Biometrics & Physical Profile</h4>", unsafe_allow_html=True)
            b_col1, b_col2 = st.columns(2)

            with b_col1:
                gender = st.selectbox(
                    "Biological Sex (for metabolic Mifflin-St Jeor BMR calculation) *",
                    ["Male", "Female"]
                )
                age = st.number_input("Age (years) *", min_value=14, max_value=100, value=None, placeholder="e.g. 25", step=1)
                height = st.number_input("Height (cm) *", min_value=90.0, max_value=240.0, value=None, placeholder="e.g. 172.0", step=0.5)

            with b_col2:
                curr_weight = st.number_input("Current Body Weight (kg) *", min_value=30.0, max_value=300.0, value=None, placeholder="e.g. 68.5", step=0.5)
                target_weight = st.number_input("Target Goal Weight (kg) *", min_value=30.0, max_value=300.0, value=None, placeholder="e.g. 65.0", step=0.5)

            st.markdown("<hr style='border-color: #21262d; margin: 18px 0;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffffff; margin-top: 0;'>2. Fitness Goals & Lifestyle</h4>", unsafe_allow_html=True)

            g_col1, g_col2 = st.columns(2)
            with g_col1:
                fitness_goal = st.selectbox(
                    "Primary Fitness Goal *",
                    ["Muscle Gain", "Fat Loss", "Maintenance", "Endurance", "Strength"]
                )
                experience = st.selectbox(
                    "Training Experience *",
                    ["Beginner (< 1 year)", "Intermediate (1 - 3 years)", "Advanced (3+ years)"]
                )

            with g_col2:
                dietary_pref = st.selectbox(
                    "Dietary Preference *",
                    ["Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian", "Jain"]
                )
                activity_level = st.selectbox(
                    "Weekly Physical Activity Level *",
                    [
                        "Sedentary (Little/no exercise)",
                        "Lightly Active (1-3 days/week)",
                        "Moderately Active (3-5 days/week)",
                        "Very Active (6-7 days/week)",
                        "Extremely Active (Physical job + training)"
                    ],
                    index=2
                )

            # Clean selected values for backend
            clean_activity = activity_level.split(" (")[0]
            clean_exp = experience.split(" (")[0]

            st.markdown("<hr style='border-color: #21262d; margin: 18px 0;'>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #ffffff; margin-top: 0;'>3. Workout & Training Split Preferences</h4>", unsafe_allow_html=True)
            w_col1, w_col2 = st.columns(2)
            with w_col1:
                onboard_freq = st.selectbox("Training Frequency (Days/Week)", [3, 4, 5, 6, 7], index=3) # default 6 days
            with w_col2:
                onboard_split = st.selectbox(
                    "Preferred Training Split",
                    [
                        "Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)",
                        "Push / Pull / Legs (PPL)",
                        "Upper / Lower Split (4-Day)",
                        "Bro Split / Body Part (5-Day)",
                        "Full Body Routine (3-Day)",
                        "Custom Split"
                    ]
                )

            # Live preview of calculated targets (only when all metrics are provided)
            if curr_weight and height and age:
                res = calculate_preview_macros(curr_weight, height, age, gender, activity_level, fitness_goal)
                if res[0] is not None:
                    bmr_val, tdee_val, cal_val, pro_val, carbs_val, fat_val = res
                    st.markdown(
                        f"""
                        <div style="background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 14px 18px; margin: 15px 0;">
                            <div style="font-size: 0.8rem; color: #8b949e; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">
                                ⚡ Live Scientific Target Calibration
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; flex-wrap: wrap; gap: 10px;">
                                <div>
                                    <span style="color: #8b949e; font-size: 0.82rem;">Basal Metabolic Rate:</span><br>
                                    <b style="color: #ffffff; font-size: 1.1rem;">{bmr_val} kcal</b>
                                </div>
                                <div>
                                    <span style="color: #8b949e; font-size: 0.82rem;">Total Daily TDEE:</span><br>
                                    <b style="color: #38bdf8; font-size: 1.1rem;">{tdee_val} kcal</b>
                                </div>
                                <div>
                                    <span style="color: #8b949e; font-size: 0.82rem;">Daily Calorie Target:</span><br>
                                    <b style="color: #a3e635; font-size: 1.2rem;">{cal_val} kcal</b>
                                </div>
                                <div>
                                    <span style="color: #8b949e; font-size: 0.82rem;">Protein Target:</span><br>
                                    <b style="color: #fbbf24; font-size: 1.2rem;">{pro_val} g/day</b>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                st.info("ℹ️ Enter your age, height, and current weight above to see your calibrated targets.")

            submit_onboard = st.form_submit_button("Complete Setup & Launch Dashboard 🚀", use_container_width=True)

            if submit_onboard:
                if not (curr_weight and height and age and target_weight and curr_weight > 0 and height > 0 and age > 0):
                    st.error("Please enter valid positive values for age, height, current weight, and target weight.")
                else:
                    try:
                        onboard_payload = {
                            "age": int(age),
                            "gender": gender,
                            "height_cm": float(height),
                            "current_weight_kg": float(curr_weight),
                            "target_weight_kg": float(target_weight),
                            "fitness_experience": clean_exp,
                            "fitness_goal": fitness_goal,
                            "dietary_preference": dietary_pref,
                            "activity_level": clean_activity,
                            "workout_frequency_days": int(onboard_freq),
                            "preferred_split": onboard_split,
                            "custom_split_details": (
                                "1. Chest + Triceps\n2. Back + Biceps\n3. Legs\n4. Chest + Shoulders\n5. Arms (Biceps + Triceps)\n6. Back + Shoulders\n7. Rest"
                                if "Chest+Tri" in onboard_split else None
                            )
                        }
                        profile_res = api.complete_onboarding(onboard_payload)
                        st.session_state["is_onboarded"] = True
                        st.session_state["user_profile"] = profile_res
                        st.session_state["nav_page"] = "Dashboard"
                        st.success("Your personalized profile is configured! Redirecting to Dashboard...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Onboarding failed: {str(e)}")
