import streamlit as st
from frontend.api_client import DesiFitAPIClient


def render_profile_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                User <span style="color: #a3e635;">Profile & Settings</span> ⚙️
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Customize your personal biometrics, fitness goals, dietary preferences, and macro targets.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    try:
        profile = api.get_profile()
        user_info = api.get_me()
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")
        return

    has_saved_profile = bool(profile.get("current_weight_kg") and profile.get("height_cm"))
    if not has_saved_profile:
        st.warning(
            "⚠️ **Profile Incomplete**: You have not yet configured your personal biometrics. "
            "Please enter your metrics below. DesiFit never pre-fills your account with another user's personal information."
        )

    has_age = profile.get("age") is not None
    has_height = profile.get("height_cm") is not None
    has_weight = profile.get("current_weight_kg") is not None
    has_target_wt = profile.get("target_weight_kg") is not None
    has_cal = profile.get("target_calories") is not None
    has_pro = profile.get("target_protein_g") is not None
    has_carbs = profile.get("target_carbs_g") is not None
    has_fat = profile.get("target_fat_g") is not None

    # Profile Form
    with st.form("profile_form"):
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Biometrics & Identity</h3>", unsafe_allow_html=True)
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.text_input("Full Name (Registered)", value=user_info.get("full_name", ""), disabled=True)
            st.text_input("Username", value=user_info.get("username", ""), disabled=True)
            age = st.number_input(
                "Age (years)",
                min_value=12,
                max_value=100,
                value=int(profile["age"]) if has_age else None,
                placeholder="Unavailable — enter your age",
                step=1
            )
            gender_options = ["Male", "Female", "Non-Binary", "Prefer not to say"]
            curr_gender = profile.get("gender") or "Male"
            gender = st.selectbox("Biological Sex / Gender", gender_options, index=gender_options.index(curr_gender) if curr_gender in gender_options else 0)

        with col_u2:
            st.text_input("Email Address", value=user_info.get("email", ""), disabled=True)
            height_cm = st.number_input(
                "Height (cm)",
                min_value=90.0,
                max_value=250.0,
                value=float(profile["height_cm"]) if has_height else None,
                placeholder="Unavailable — enter height in cm",
                step=0.5
            )
            current_wt = st.number_input(
                "Current Weight (kg)",
                min_value=30.0,
                max_value=300.0,
                value=float(profile["current_weight_kg"]) if has_weight else None,
                placeholder="Unavailable — enter weight in kg",
                step=0.5
            )
            target_wt = st.number_input(
                "Target Weight (kg)",
                min_value=30.0,
                max_value=300.0,
                value=float(profile["target_weight_kg"]) if has_target_wt else None,
                placeholder="Unavailable — enter target weight in kg",
                step=0.5
            )

        st.markdown("<hr style='border-color: #21262d; margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Training & Lifestyle Preferences</h3>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns(3)

        exp_options = ["Beginner", "Intermediate", "Advanced"]
        curr_exp = profile.get("fitness_experience") or "Intermediate"
        with col_p1:
            experience = st.selectbox("Fitness Experience", exp_options, index=exp_options.index(curr_exp) if curr_exp in exp_options else 1)

        goal_options = ["Muscle Gain", "Fat Loss", "Maintenance", "Endurance", "Strength"]
        curr_goal = profile.get("fitness_goal") or "Muscle Gain"
        with col_p2:
            fitness_goal = st.selectbox("Primary Fitness Goal", goal_options, index=goal_options.index(curr_goal) if curr_goal in goal_options else 0)

        diet_options = ["Vegetarian", "Non-Vegetarian", "Vegan", "Eggetarian", "Jain"]
        curr_diet = profile.get("dietary_preference") or "Non-Vegetarian"
        with col_p3:
            dietary_preference = st.selectbox("Dietary Preference", diet_options, index=diet_options.index(curr_diet) if curr_diet in diet_options else 1)

        act_options = ["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "Extremely Active"]
        curr_act = profile.get("activity_level") or "Moderately Active"
        activity_level = st.selectbox("Activity Level", act_options, index=act_options.index(curr_act) if curr_act in act_options else 2)

        st.markdown("<hr style='border-color: #21262d; margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Workout & Training Split Preferences 🏋️</h3>", unsafe_allow_html=True)
        col_w1, col_w2 = st.columns(2)

        freq_options = [1, 2, 3, 4, 5, 6, 7]
        saved_freq = profile.get("workout_frequency_days") or 6
        freq_idx = freq_options.index(saved_freq) if saved_freq in freq_options else 5

        with col_w1:
            workout_frequency = st.selectbox(
                "Weekly Training Frequency (Days/Week)",
                freq_options,
                index=freq_idx,
                help="How many days per week you actively lift or train."
            )

        split_options = [
            "Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)",
            "Push / Pull / Legs (PPL)",
            "Upper / Lower Split (4-Day)",
            "Bro Split / Body Part (5-Day)",
            "Full Body Routine (3-Day)",
            "Custom Split"
        ]
        saved_split = profile.get("preferred_split") or "Chest+Tri / Back+Bi / Legs / Chest+Shoulders / Arms / Back+Shoulders (Custom 6-Day)"
        split_idx = split_options.index(saved_split) if saved_split in split_options else 0

        with col_w2:
            preferred_split = st.selectbox(
                "Preferred Workout Split",
                split_options,
                index=split_idx,
                help="Select your favorite training split archetype."
            )

        default_custom_details = (
            profile.get("custom_split_details") or
            "1. Chest + Triceps\n2. Back + Biceps\n3. Legs\n4. Chest + Shoulders\n5. Arms (Biceps + Triceps)\n6. Back + Shoulders\n7. Rest"
        )
        custom_split_details = st.text_area(
            "Day-by-Day Split Details (Customizable)",
            value=default_custom_details,
            height=130,
            help="Define or customize what muscle groups you train each day. DesiFit AI will dynamically generate your routines following this exact schedule."
        )

        st.markdown("<hr style='border-color: #21262d; margin: 20px 0;'>", unsafe_allow_html=True)

        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Daily Nutrition Targets</h3>", unsafe_allow_html=True)
        auto_calc = st.checkbox("⚡ Auto-recalculate optimal targets using Mifflin-St Jeor formula based on biometrics above", value=False)

        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        with col_t1:
            target_calories = st.number_input(
                "Target Calories (kcal)",
                min_value=1000,
                max_value=6000,
                value=int(profile["target_calories"]) if has_cal else None,
                placeholder="Unavailable",
                step=50,
                disabled=auto_calc
            )
        with col_t2:
            target_protein = st.number_input(
                "Target Protein (g)",
                min_value=30.0,
                max_value=400.0,
                value=float(profile["target_protein_g"]) if has_pro else None,
                placeholder="Unavailable",
                step=5.0,
                disabled=auto_calc
            )
        with col_t3:
            target_carbs = st.number_input(
                "Target Carbs (g)",
                min_value=30.0,
                max_value=600.0,
                value=float(profile["target_carbs_g"]) if has_carbs else None,
                placeholder="Unavailable",
                step=5.0,
                disabled=auto_calc
            )
        with col_t4:
            target_fat = st.number_input(
                "Target Fat (g)",
                min_value=15.0,
                max_value=250.0,
                value=float(profile["target_fat_g"]) if has_fat else None,
                placeholder="Unavailable",
                step=2.5,
                disabled=auto_calc
            )

        update_profile_btn = st.form_submit_button("Save Profile & Targets 💾", use_container_width=True)

        if update_profile_btn:
            try:
                updated_profile = {
                    "age": int(age) if age is not None else None,
                    "gender": gender,
                    "height_cm": float(height_cm) if height_cm is not None else None,
                    "current_weight_kg": float(current_wt) if current_wt is not None else None,
                    "target_weight_kg": float(target_wt) if target_wt is not None else None,
                    "fitness_experience": experience,
                    "fitness_goal": fitness_goal,
                    "dietary_preference": dietary_preference,
                    "activity_level": activity_level,
                    "target_calories": None if auto_calc else (int(target_calories) if target_calories is not None else None),
                    "target_protein_g": None if auto_calc else (float(target_protein) if target_protein is not None else None),
                    "target_carbs_g": None if auto_calc else (float(target_carbs) if target_carbs is not None else None),
                    "target_fat_g": None if auto_calc else (float(target_fat) if target_fat is not None else None),
                    "workout_frequency_days": int(workout_frequency) if workout_frequency else None,
                    "preferred_split": preferred_split,
                    "custom_split_details": custom_split_details
                }
                res = api.update_profile(updated_profile)
                st.session_state["is_onboarded"] = res.get("is_onboarded", True)
                st.session_state["user_profile"] = res
                st.success("Profile and nutrition targets successfully updated! ✅")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update profile: {str(e)}")
