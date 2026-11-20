import streamlit as st
from frontend.api_client import DesiFitAPIClient


def render_ai_page(api: DesiFitAPIClient):
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="color: #ffffff; margin: 0; font-size: 1.8rem; font-weight: 800;">
                DesiFit AI <span style="color: #a3e635;">Assistant</span> 🤖
            </h1>
            <p style="color: #8b949e; margin-top: 4px; font-size: 0.95rem;">
                Your 24/7 personal coach for training splits, exercise form, desi nutrition, macros & recovery.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # API Status Banner
    try:
        status_info = api.get_ai_status()
        is_connected = status_info.get("api_connected", False)
        if is_connected:
            st.markdown(
                """
                <div style="background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; border-radius: 8px; padding: 10px 16px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="color: #4ade80; font-size: 0.88rem; font-weight: 600;">
                        🟢 <b>OpenAI Live API Connected</b> — Running live LLM intelligence.
                    </span>
                    <span style="font-size: 0.75rem; color: #86efac; background: rgba(34,197,94,0.2); padding: 3px 8px; border-radius: 12px;">gpt-4o-mini</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background: rgba(234, 179, 8, 0.1); border: 1px solid #eab308; border-radius: 8px; padding: 12px 16px; margin-bottom: 18px;">
                    <div style="color: #fde047; font-size: 0.88rem; font-weight: 700; margin-bottom: 4px;">
                        🟡 <b>DesiFit Rule-Based Expert Assistant Active (Fallback Mode)</b>
                    </div>
                    <div style="color: #d1d5db; font-size: 0.82rem;">
                        No OpenAI API key was detected in <code>.env</code>. The assistant is running on its built-in, 
                        scientifically tailored fitness engine personalized to your profile. 
                        To connect live OpenAI, add <code>OPENAI_API_KEY="your-key"</code> to your <code>.env</code> file.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        pass

    # Quick Suggestion Chips
    st.markdown("<div style='font-size: 0.85rem; color: #8b949e; margin-bottom: 8px; font-weight: 600;'>💡 SUGGESTED TOPICS:</div>", unsafe_allow_html=True)
    chip_cols = st.columns(4)
    suggested_prompt = None

    with chip_cols[0]:
        if st.button("🥗 High-Protein Desi Diet", use_container_width=True):
            suggested_prompt = "What is the best high-protein vegetarian and non-vegetarian desi diet plan for my goal?"
    with chip_cols[1]:
        user_prof = st.session_state.get("user_profile") or {}
        user_days = user_prof.get("workout_frequency_days") or 6
        if st.button(f"🏋️ {user_days}-Day Workout Split", use_container_width=True):
            suggested_prompt = f"Design my personalized {user_days}-day workout split customized for my goals."
    with chip_cols[2]:
        if st.button("🔥 Fat Loss Strategy", use_container_width=True):
            suggested_prompt = "How can I lose body fat while maintaining lean muscle and strength?"
    with chip_cols[3]:
        if st.button("💤 Muscle Recovery Guide", use_container_width=True):
            suggested_prompt = "What are the essential sleep and recovery practices to avoid muscle soreness and burnout?"

    st.markdown("<hr style='border-color: #21262d; margin: 15px 0 20px 0;'>", unsafe_allow_html=True)

    # Fetch Conversation History
    try:
        history = api.get_chat_history()
    except Exception as e:
        history = []
        st.error(f"Could not load conversation history: {str(e)}")

    # Display chat history using Streamlit's sanitized Markdown renderer.
    # Do not interpolate user/AI text into unsafe HTML (stored chat can contain HTML).
    chat_container = st.container()
    with chat_container:
        if not history:
            st.markdown(
                """
                <div style="text-align: center; padding: 40px 20px; color: #8b949e; background: #161b22; border: 1px dashed #30363d; border-radius: 12px; margin-bottom: 20px;">
                    <div style="font-size: 2.2rem; margin-bottom: 10px;">💬</div>
                    <div style="font-weight: 600; color: #ffffff; font-size: 1.1rem;">Start a Conversation with DesiFit AI</div>
                    <div style="font-size: 0.85rem; margin-top: 6px;">
                        Ask about workout volume, calorie deficits, Indian protein sources, or exercise technique.
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "assistant"
                with st.chat_message(role):
                    st.markdown(msg.get("content", ""))

    # Input Form
    user_query = None
    if suggested_prompt:
        user_query = suggested_prompt

    with st.form("ai_chat_form", clear_on_submit=True):
        col_input, col_submit = st.columns([5, 1])
        with col_input:
            input_text = st.text_input(
                "Ask DesiFit AI",
                value=suggested_prompt or "",
                placeholder="Ask anything about exercises, macros, splits, or diet...",
                label_visibility="collapsed"
            )
        with col_submit:
            submit_btn = st.form_submit_button("Send 🚀", use_container_width=True)

        if submit_btn and input_text:
            user_query = input_text

    if user_query:
        with st.spinner("DesiFit AI is analyzing your profile and formulating guidance..."):
            try:
                api.chat_ai(user_query)
                st.rerun()
            except Exception as e:
                st.error(f"Error communicating with AI Assistant: {str(e)}")

    # Footer options: Clear History
    if history:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        col_l, col_r = st.columns([4, 1])
        with col_r:
            if st.button("🗑️ Clear History", use_container_width=True, type="secondary"):
                try:
                    api.clear_chat_history()
                    st.success("Chat history cleared.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear history: {str(e)}")
