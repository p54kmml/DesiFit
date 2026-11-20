import streamlit as st
from html import escape
from datetime import date
from frontend.api_client import DesiFitAPIClient
from frontend.components.charts import create_macro_donut_chart


def render_nutrition_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                Nutrition & <span style="color: #a3e635;">Macro Tracker</span> 🥗
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Track calories, protein, carbs, and fats with comprehensive Indian and global food items.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Date selector
    col_d1, col_d2 = st.columns([1.5, 4])
    with col_d1:
        selected_date = st.date_input("Select Tracking Date", value=date.today())

    date_str = str(selected_date)

    # Fetch daily summary
    try:
        summary = api.get_daily_nutrition_summary(log_date=date_str)
    except Exception as e:
        st.error(f"Error loading nutrition summary: {str(e)}")
        summary = {
            "calories_consumed": 0, "protein_consumed_g": 0, "carbs_consumed_g": 0, "fat_consumed_g": 0,
            "target_calories": 2200, "target_protein_g": 140, "target_carbs_g": 240, "target_fat_g": 65,
            "logs": []
        }

    # Macro Progress Section
    cals_c = summary.get("calories_consumed", 0)
    cals_t = summary.get("target_calories", 2200)
    pro_c = summary.get("protein_consumed_g", 0)
    pro_t = summary.get("target_protein_g", 140.0)
    carbs_c = summary.get("carbs_consumed_g", 0)
    carbs_t = summary.get("target_carbs_g", 240.0)
    fat_c = summary.get("fat_consumed_g", 0)
    fat_t = summary.get("target_fat_g", 65.0)

    st.markdown("<h3 style='color: #ffffff; margin-top: 15px;'>Daily Macro Targets</h3>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        cal_pct = min(1.0, cals_c / cals_t) if cals_t > 0 else 0.0
        st.metric("Calories", f"{int(cals_c)} / {int(cals_t)} kcal", f"{int(cal_pct * 100)}%")
        st.progress(cal_pct)
    with m2:
        pro_pct = min(1.0, pro_c / pro_t) if pro_t > 0 else 0.0
        st.metric("Protein", f"{int(pro_c)} / {int(pro_t)} g", f"{int(pro_pct * 100)}%")
        st.progress(pro_pct)
    with m3:
        carb_pct = min(1.0, carbs_c / carbs_t) if carbs_t > 0 else 0.0
        st.metric("Carbohydrates", f"{int(carbs_c)} / {int(carbs_t)} g", f"{int(carb_pct * 100)}%")
        st.progress(carb_pct)
    with m4:
        fat_pct = min(1.0, fat_c / fat_t) if fat_t > 0 else 0.0
        st.metric("Fats", f"{int(fat_c)} / {int(fat_t)} g", f"{int(fat_pct * 100)}%")
        st.progress(fat_pct)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Food Log & Meal Form
    col_log, col_donut = st.columns([1.6, 1.0])

    # Load food items
    try:
        food_items = api.get_food_items()
        food_map = {f"{f['name']} ({f['serving_size']}) — {int(f['calories'])} kcal, {f['protein_g']}g P": f for f in food_items}
    except Exception as e:
        food_items = []
        food_map = {}
        st.error(f"Error fetching foods: {str(e)}")

    with col_log:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Log Food Intake</h3>", unsafe_allow_html=True)
        with st.form("log_meal_form"):
            selected_food_label = st.selectbox("Select Food Item", options=list(food_map.keys()) if food_map else ["No foods available"])
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                meal_type = st.selectbox("Meal Category", ["Breakfast", "Lunch", "Dinner", "Snacks"])
            with f_col2:
                servings = st.number_input("Number of Servings", min_value=0.25, max_value=20.0, value=1.0, step=0.25)

            # Display preview of calories & macros for selected servings
            if selected_food_label in food_map:
                f_obj = food_map[selected_food_label]
                st.markdown(
                    f"""
                    <div style="background: #21262d; border-radius: 6px; padding: 10px 14px; margin: 8px 0; font-size: 0.85rem; color: #c9d1d9;">
                        <b>Preview for {servings} serving(s):</b> 
                        <span style="color: #a3e635;">{round(f_obj['calories'] * servings, 1)} kcal</span> | 
                        Protein: <span style="color: #38bdf8;">{round(f_obj['protein_g'] * servings, 1)}g</span> | 
                        Carbs: {round(f_obj['carbs_g'] * servings, 1)}g | 
                        Fat: {round(f_obj['fat_g'] * servings, 1)}g
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            log_food_btn = st.form_submit_button("Add to Food Log 🥗", use_container_width=True)

            if log_food_btn:
                if selected_food_label not in food_map:
                    st.error("Please select a valid food item.")
                else:
                    try:
                        food_selected = food_map[selected_food_label]
                        api.log_meal({
                            "food_item_id": food_selected["id"],
                            "meal_type": meal_type,
                            "servings": servings,
                            "date": date_str
                        })
                        st.success(f"Added {servings} serving(s) of {food_selected['name']} to {meal_type}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to log meal: {str(e)}")

    with col_donut:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Macro Ratio</h3>", unsafe_allow_html=True)
        fig_donut = create_macro_donut_chart(pro_c, carbs_c, fat_c)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Add custom food item expander
    with st.expander("➕ Add Custom Food Item to DesiFit Database", expanded=False):
        with st.form("custom_food_form"):
            cf_col1, cf_col2 = st.columns(2)
            with cf_col1:
                cf_name = st.text_input("Food Item Name", placeholder="e.g. Sattu Drink, Oats Porridge...")
                cf_serv = st.text_input("Serving Size", value="100g", placeholder="e.g. 100g, 1 bowl, 1 piece")
                cf_desi = st.checkbox("Is Desi / Indian Special?", value=True)
            with cf_col2:
                cf_cals = st.number_input("Calories (kcal)", min_value=0.0, max_value=2000.0, value=150.0, step=5.0)
                cf_pro = st.number_input("Protein (g)", min_value=0.0, max_value=200.0, value=10.0, step=0.5)
                cf_carbs = st.number_input("Carbohydrates (g)", min_value=0.0, max_value=200.0, value=20.0, step=0.5)
                cf_fat = st.number_input("Fat (g)", min_value=0.0, max_value=200.0, value=3.0, step=0.5)

            add_custom_food_btn = st.form_submit_button("Save Food to Database 💾", use_container_width=True)
            if add_custom_food_btn:
                if not cf_name:
                    st.error("Please provide food name.")
                else:
                    try:
                        api.create_food_item({
                            "name": cf_name,
                            "serving_size": cf_serv,
                            "calories": cf_cals,
                            "protein_g": cf_pro,
                            "carbs_g": cf_carbs,
                            "fat_g": cf_fat,
                            "is_desi_special": cf_desi
                        })
                        st.success(f"Food item '{cf_name}' added to database!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding food item: {str(e)}")

    st.markdown("<hr style='border-color: #21262d; margin: 25px 0;'>", unsafe_allow_html=True)

    # Display today's meals grouped by category
    st.markdown(f"<h3 style='color: #ffffff; margin-top: 0;'>Logged Meals for {date_str}</h3>", unsafe_allow_html=True)
    logs = summary.get("logs", [])

    if not logs:
        st.info("No meals logged for this date. Select a food item above to start logging!")
    else:
        meal_groups = {"Breakfast": [], "Lunch": [], "Dinner": [], "Snacks": []}
        for l in logs:
            meal_groups.setdefault(l["meal_type"], []).append(l)

        for m_type, m_logs in meal_groups.items():
            if m_logs:
                sub_cals = sum(x["total_calories"] for x in m_logs)
                sub_pro = sum(x["total_protein_g"] for x in m_logs)
                safe_meal_type = escape(str(m_type))
                st.markdown(
                    f"""
                    <div style="background: #161b22; border-left: 3px solid #a3e635; padding: 8px 14px; margin-top: 15px; margin-bottom: 8px; border-radius: 4px; display: flex; justify-content: space-between;">
                        <span style="font-weight: 700; color: #ffffff;">{safe_meal_type}</span>
                        <span style="font-size: 0.85rem; color: #8b949e;">{int(sub_cals)} kcal | {round(sub_pro, 1)}g Protein</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                for item in m_logs:
                    food_info = item.get("food_item", {})
                    col_info, col_del = st.columns([5, 1])
                    with col_info:
                        st.write(
                            f"• **{food_info.get('name', 'Food')}** — {item['servings']} serving(s) "
                            f"({item['total_calories']} kcal, {item['total_protein_g']}g P, {item['total_carbs_g']}g C, {item['total_fat_g']}g F)"
                        )
                    with col_del:
                        if st.button("Delete", key=f"del_nlog_{item['id']}", type="secondary"):
                            api.delete_nutrition_log(item["id"])
                            st.success("Entry deleted.")
                            st.rerun()
