import streamlit as st
from datetime import date
from frontend.api_client import DesiFitAPIClient
from frontend.components.charts import (
    create_weight_trend_chart,
    create_measurements_chart
)


def render_progress_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                Body Progress <span style="color: #a3e635;">Tracker</span> 📏
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Track weight transformations, body circumferences, and physique milestones over time.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_charts, tab_log, tab_history = st.tabs(["📊 Progress Charts", "✍️ Record Measurements", "📋 History Log"])

    # Fetch measurements
    measurements = []
    profile = {}
    target_wt = 68.0
    try:
        measurements = api.get_measurements(limit=50)
        profile = api.get_profile() or {}
        target_wt = profile.get("target_weight_kg", 68.0)
    except Exception as e:
        measurements = []
        profile = {}
        target_wt = 68.0
        st.error(f"Error loading body measurements: {str(e)}")

    # ==========================================
    # TAB 1: PROGRESS CHARTS
    # ==========================================
    with tab_charts:
        if not measurements:
            st.info("No body measurements recorded yet. Head over to the 'Record Measurements' tab to log your starting stats!")
        else:
            col_ch1, col_ch2 = st.columns(2)
            with col_ch1:
                st.markdown("<h4 style='color: #ffffff; margin-bottom: 8px;'>Weight Trajectory</h4>", unsafe_allow_html=True)
                fig_wt = create_weight_trend_chart(measurements, target_wt)
                st.plotly_chart(fig_wt, use_container_width=True)

            with col_ch2:
                st.markdown("<h4 style='color: #ffffff; margin-bottom: 8px;'>Body Circumferences Trend</h4>", unsafe_allow_html=True)
                fig_circ = create_measurements_chart(measurements)
                st.plotly_chart(fig_circ, use_container_width=True)

    # ==========================================
    # TAB 2: RECORD MEASUREMENTS
    # ==========================================
    with tab_log:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Log New Measurements</h3>", unsafe_allow_html=True)
        with st.form("measurement_form"):
            c_date, c_wt = st.columns(2)
            with c_date:
                m_date = st.date_input("Date of Measurement", value=date.today())
            with c_wt:
                curr_def = profile.get("current_weight_kg", 70.0) if profile else 70.0
                m_weight = st.number_input("Body Weight (kg) *", min_value=30.0, max_value=300.0, value=float(curr_def), step=0.1)

            st.markdown("<h5 style='color: #a3e635; margin: 15px 0 10px 0;'>Circumferences (cm) - Optional</h5>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                m_chest = st.number_input("Chest (cm)", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
            with c2:
                m_waist = st.number_input("Waist (cm)", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
            with c3:
                m_arm = st.number_input("Arm / Bicep (cm)", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            with c4:
                m_thigh = st.number_input("Thigh (cm)", min_value=0.0, max_value=150.0, value=0.0, step=0.5)

            m_notes = st.text_area("Progress Notes", placeholder="e.g. Feeling leaner around waist, veins showing in forearms.", height=70)

            save_meas_btn = st.form_submit_button("Record Measurements 📏", use_container_width=True)

            if save_meas_btn:
                try:
                    payload = {
                        "weight_kg": m_weight,
                        "chest_cm": m_chest if m_chest > 0 else None,
                        "waist_cm": m_waist if m_waist > 0 else None,
                        "arm_cm": m_arm if m_arm > 0 else None,
                        "thigh_cm": m_thigh if m_thigh > 0 else None,
                        "notes": m_notes if m_notes else None,
                        "date": str(m_date)
                    }
                    api.record_measurement(payload)
                    st.success("Measurements recorded successfully! Your profile weight was also updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving measurement: {str(e)}")

    # ==========================================
    # TAB 3: HISTORY LOG TABLE
    # ==========================================
    with tab_history:
        st.markdown("<h3 style='color: #ffffff; margin-top: 0;'>Historical Records</h3>", unsafe_allow_html=True)
        if not measurements:
            st.info("No records to display.")
        else:
            for item in reversed(measurements):
                with st.expander(f"📅 {item['date']} — Weight: {item['weight_kg']} kg", expanded=False):
                    col_m1, col_m2 = st.columns([4, 1])
                    with col_m1:
                        st.write(
                            f"**Waist:** {item.get('waist_cm') or 'N/A'} cm | "
                            f"**Chest:** {item.get('chest_cm') or 'N/A'} cm | "
                            f"**Arm:** {item.get('arm_cm') or 'N/A'} cm | "
                            f"**Thigh:** {item.get('thigh_cm') or 'N/A'} cm"
                        )
                        if item.get("notes"):
                            st.write(f"*Notes:* {item['notes']}")
                    with col_m2:
                        if st.button("Delete Record", key=f"del_m_{item['id']}", type="secondary"):
                            api.delete_measurement(item["id"])
                            st.success("Record deleted.")
                            st.rerun()
