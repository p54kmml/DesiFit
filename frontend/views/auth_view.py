import os
import streamlit as st
from frontend.api_client import DesiFitAPIClient
from frontend.styles import render_logo


def is_production() -> bool:
    """Detects whether frontend is operating in a production or deployed cloud environment."""
    env = os.getenv("ENVIRONMENT", "").strip().lower()
    if env in ("production", "prod", "staging"):
        return True
    if os.getenv("ENV", "").strip().lower() in ("production", "prod", "staging"):
        return True
    if os.getenv("RENDER", "").strip().lower() == "true":
        return True
    if bool(os.getenv("RENDER_SERVICE_ID", "").strip()):
        return True
    backend_url = os.getenv("BACKEND_API_URL", "").lower()
    if "onrender.com" in backend_url or "streamlit.app" in backend_url:
        return True
    return False


def set_auth_view(view: str, token: str = None, verify_token: str = None):
    """Safely updates auth navigation state and synchronizes query parameters."""
    st.session_state["auth_view"] = view
    if token:
        st.session_state["reset_token"] = token
        st.query_params["token"] = token
    elif "token" in st.query_params and view != "reset_password":
        try:
            del st.query_params["token"]
        except Exception:
            pass

    if verify_token:
        st.session_state["verify_token"] = verify_token
        st.query_params["verify_token"] = verify_token
    elif "verify_token" in st.query_params and view != "verify_email":
        try:
            del st.query_params["verify_token"]
        except Exception:
            pass

    if view == "login":
        st.query_params.clear()
    else:
        st.query_params["view"] = view


def render_forgot_password_view(api: DesiFitAPIClient):
    """Step 1: Renders the email submission screen for password recovery."""
    st.subheader("Account Recovery")
    st.markdown(
        """
        <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 20px;">
            Enter your registered email address to generate a secure password recovery token.
        </p>
        """,
        unsafe_allow_html=True
    )

    with st.form("forgot_password_form"):
        email = st.text_input("Registered Email Address", placeholder="e.g. arjun@example.com")
        submit_btn = st.form_submit_button("Send Recovery Link", use_container_width=True)

        if submit_btn:
            if not email or "@" not in email:
                st.error("Please enter a valid email address.")
            else:
                try:
                    res = api.forgot_password(email=email.strip())
                    st.session_state["forgot_response"] = res
                except Exception as e:
                    st.error(f"Recovery request failed: {str(e)}")

    if "forgot_response" in st.session_state:
        res = st.session_state["forgot_response"]
        st.success(res.get("message", "If this email is registered, a password reset link has been sent."))

        # Display dev token helper box ONLY when strictly running in local development mode
        if not is_production() and res.get("dev_token"):
            dev_tok = res.get("dev_token")
            st.markdown(
                f"""
                <div style="background-color: #21262d; border: 1px solid #a3e635; border-radius: 8px; padding: 16px; margin-top: 15px; margin-bottom: 15px;">
                    <div style="color: #a3e635; font-weight: 700; font-size: 0.9rem; margin-bottom: 6px;">
                        🛠️ Development Mode (SMTP Not Configured)
                    </div>
                    <div style="color: #c9d1d9; font-size: 0.85rem; margin-bottom: 10px;">
                        SMTP email delivery is not configured in this environment. Your temporary 15-minute recovery token is:
                    </div>
                    <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 8px 12px; font-family: monospace; font-size: 0.82rem; color: #a3e635; word-break: break-all;">
                        {dev_tok}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("👉 Proceed to Reset Password with Token", use_container_width=True, key="btn_proceed_dev_reset"):
                set_auth_view("reset_password", token=dev_tok)
                st.rerun()

        elif not is_production() and res.get("dev_note"):
            # Inform developer if email was not found in database during development
            st.markdown(
                f"""
                <div style="background-color: #21262d; border: 1px solid #f59e0b; border-radius: 8px; padding: 16px; margin-top: 15px; margin-bottom: 15px;">
                    <div style="color: #f59e0b; font-weight: 700; font-size: 0.9rem; margin-bottom: 6px;">
                        ⚠️ Development Mode Notice
                    </div>
                    <div style="color: #c9d1d9; font-size: 0.85rem;">
                        {res.get('dev_note')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<hr style='border-color: #30363d; margin: 20px 0;'>", unsafe_allow_html=True)

    col_back, col_have_token = st.columns([1, 1])
    with col_back:
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="btn_back_login_from_forgot"):
            st.session_state.pop("forgot_response", None)
            set_auth_view("login")
            st.rerun()
    with col_have_token:
        if st.button("🔑 Already have a token?", use_container_width=True, type="secondary", key="btn_have_token_goto_enter"):
            set_auth_view("enter_token")
            st.rerun()


def render_enter_token_view(api: DesiFitAPIClient):
    """Step 2: Renders the token-entry form to verify an existing token before password reset."""
    st.subheader("Enter Recovery Token")
    st.markdown(
        """
        <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 20px;">
            Please enter your 43-character password recovery token. Once verified, you will be prompted to set a new password.
        </p>
        """,
        unsafe_allow_html=True
    )

    preset_tok = st.session_state.get("reset_token", "") or st.query_params.get("token", "")

    with st.form("enter_token_form"):
        token_input = st.text_input("Recovery Token", value=preset_tok, placeholder="Paste your 43-character token here")
        submit_token_btn = st.form_submit_button("Verify Token & Continue", use_container_width=True)

        if submit_token_btn:
            clean_token = token_input.strip()
            if not clean_token:
                st.error("Please enter a recovery token.")
            elif len(clean_token) < 10:
                st.error("Token is too short. Please provide a valid recovery token.")
            else:
                try:
                    # Verify token validity against backend API
                    res = api.verify_reset_token(token=clean_token)
                    if res.get("valid"):
                        st.session_state["token_verified"] = True
                        set_auth_view("reset_password", token=clean_token)
                        st.rerun()
                    else:
                        st.error("Invalid recovery token.")
                except Exception as e:
                    st.error(f"Token Verification Failed: {str(e)}")

    st.markdown("<hr style='border-color: #30363d; margin: 20px 0;'>", unsafe_allow_html=True)

    col_back_forgot, col_back_login = st.columns([1, 1])
    with col_back_forgot:
        if st.button("⬅️ Request a New Token", use_container_width=True, type="secondary", key="btn_back_forgot_from_enter"):
            set_auth_view("forgot_password")
            st.rerun()
    with col_back_login:
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="btn_back_login_from_enter"):
            set_auth_view("login")
            st.rerun()


def render_reset_password_view(api: DesiFitAPIClient):
    """Step 3: Renders the new password form once token is validated."""
    st.subheader("Set New Password")
    st.markdown(
        """
        <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 20px;">
            Choose a new, strong password for your DesiFit account.
        </p>
        """,
        unsafe_allow_html=True
    )

    current_tok = st.session_state.get("reset_token", "") or st.query_params.get("token", "")

    # Display active token status badge
    if current_tok:
        tok_preview = f"{current_tok[:8]}...{current_tok[-6:]}"
        st.markdown(
            f"""
            <div style="background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 10px 14px; margin-bottom: 15px; font-size: 0.82rem; color: #8b949e;">
                🔑 Active Token: <span style="color: #a3e635; font-family: monospace;">{tok_preview}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    with st.form("reset_password_form"):
        # Editable token field in case user needs to view or tweak it
        token_field = st.text_input("Reset Token", value=current_tok, placeholder="Paste your token here")
        new_password = st.text_input("New Password", type="password", placeholder="At least 8 chars (uppercase, lowercase, number)")
        confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter your new password")

        st.markdown(
            """
            <div style="background-color: #21262d; border-radius: 6px; padding: 10px 14px; margin-top: 5px; margin-bottom: 15px; font-size: 0.8rem; color: #8b949e;">
                🔒 <strong>Password Strength Requirements:</strong><br>
                • Minimum 8 characters<br>
                • At least one uppercase letter (A-Z)<br>
                • At least one lowercase letter (a-z)<br>
                • At least one numeric digit (0-9)
            </div>
            """,
            unsafe_allow_html=True
        )

        submitted = st.form_submit_button("Update Password", use_container_width=True)

        if submitted:
            clean_token = token_field.strip()
            if not clean_token:
                st.error("Please enter your password reset token.")
            elif not new_password or not confirm_password:
                st.error("Please fill in both password fields.")
            elif new_password != confirm_password:
                st.error("New password and confirmation password do not match.")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
            elif not any(c.isupper() for c in new_password) or not any(c.islower() for c in new_password) or not any(c.isdigit() for c in new_password):
                st.error("Password must contain at least one uppercase letter, one lowercase letter, and one number.")
            else:
                try:
                    res = api.reset_password(
                        token=clean_token,
                        new_password=new_password,
                        confirm_password=confirm_password
                    )
                    st.session_state["reset_success"] = res.get(
                        "message",
                        "Password has been successfully reset! You can now log in with your new password."
                    )
                    st.session_state.pop("reset_token", None)
                    st.session_state.pop("token_verified", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Password reset failed: {str(e)}")

    if "reset_success" in st.session_state:
        st.success(st.session_state["reset_success"])
        if st.button("🚀 Return to Login", use_container_width=True, key="btn_return_login_after_success"):
            st.session_state.pop("reset_success", None)
            set_auth_view("login")
            st.rerun()

    st.markdown("<hr style='border-color: #30363d; margin: 20px 0;'>", unsafe_allow_html=True)
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ Change Token", key="btn_back_enter_from_reset", use_container_width=True, type="secondary"):
            set_auth_view("enter_token")
            st.rerun()
    with col_nav2:
        if st.button("⬅️ Back to Login", key="btn_back_login_from_reset", use_container_width=True, type="secondary"):
            st.session_state.pop("reset_success", None)
            set_auth_view("login")
            st.rerun()


def render_verify_email_view(api: DesiFitAPIClient):
    """Renders the account email verification screen."""
    st.subheader("Account Verification")
    token = st.session_state.get("verify_token") or st.query_params.get("verify_token")
    if not token:
        st.error("No verification token was provided.")
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="btn_back_no_verify_token"):
            set_auth_view("login")
            st.rerun()
        return

    if "verification_result" not in st.session_state:
        try:
            res = api.verify_email(token)
            st.session_state["verification_result"] = {
                "success": True,
                "message": res.get("message", "Email successfully verified!")
            }
        except Exception as e:
            st.session_state["verification_result"] = {
                "success": False,
                "message": str(e)
            }

    result = st.session_state["verification_result"]
    if result["success"]:
        st.success(f"🎉 {result['message']}")
        st.markdown(
            """
            <p style="color: #c9d1d9; font-size: 0.9rem; margin: 15px 0;">
                Your DesiFit account has been verified. You can now sign in with your credentials.
            </p>
            """,
            unsafe_allow_html=True
        )
        if st.button("👉 Sign In to DesiFit", use_container_width=True, key="btn_signin_after_verify"):
            st.session_state.pop("verification_result", None)
            st.session_state.pop("verify_token", None)
            set_auth_view("login")
            st.rerun()
    else:
        st.error(f"Verification Failed: {result['message']}")
        if st.button("⬅️ Back to Login", use_container_width=True, type="secondary", key="btn_back_verify_fail"):
            st.session_state.pop("verification_result", None)
            st.session_state.pop("verify_token", None)
            set_auth_view("login")
            st.rerun()


def render_auth_page(api: DesiFitAPIClient):
    # Synchronize initial auth_view from query params on first load
    if "auth_view" not in st.session_state:
        query_token = st.query_params.get("token")
        query_verify_token = st.query_params.get("verify_token")
        query_view = st.query_params.get("view")

        if query_token:
            st.session_state["auth_view"] = "reset_password"
            st.session_state["reset_token"] = query_token
        elif query_verify_token:
            st.session_state["auth_view"] = "verify_email"
            st.session_state["verify_token"] = query_verify_token
        elif query_view in ["forgot_password", "enter_token", "reset_password", "verify_email", "login"]:
            st.session_state["auth_view"] = query_view
        else:
            st.session_state["auth_view"] = "login"

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(render_logo(size="large"), unsafe_allow_html=True)
        st.markdown(
            """
            <div style="background-color: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; margin-bottom: 25px;">
                <h3 style="color: #ffffff; margin-top: 0; font-weight: 700;">Welcome to DesiFit</h3>
                <p style="color: #8b949e; font-size: 0.9rem; margin-bottom: 0;">
                    Your AI-powered workout companion, desi nutrition planner, and fitness intelligence suite.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        current_view = st.session_state.get("auth_view", "login")

        # View 1: Forgot Password (Request Token via Email)
        if current_view == "forgot_password":
            render_forgot_password_view(api)

        # View 2: Enter Token (Verify Token)
        elif current_view == "enter_token":
            render_enter_token_view(api)

        # View 3: Reset Password (Set New Password with Token)
        elif current_view == "reset_password":
            render_reset_password_view(api)

        # View 4: Account Verification
        elif current_view == "verify_email":
            render_verify_email_view(api)

        # View 5: Default Login / Registration Tabs
        else:
            tab_login, tab_register = st.tabs(["⚡ Log In", "🚀 Create Account"])

            with tab_login:
                with st.form("login_form"):
                    st.subheader("Account Login")
                    username = st.text_input("Username", placeholder="e.g. arjun_fit")
                    password = st.text_input("Password", type="password", placeholder="••••••••")

                    col_submit, col_forgot_btn = st.columns([1.2, 1])
                    with col_submit:
                        submitted = st.form_submit_button("Sign In to DesiFit", use_container_width=True)
                    with col_forgot_btn:
                        forgot_btn_clicked = st.form_submit_button("🔑 Forgot Password?", type="secondary", use_container_width=True)

                    if forgot_btn_clicked:
                        set_auth_view("forgot_password")
                        st.rerun()

                    if submitted:
                        if not username or not password:
                            st.error("Please enter both username and password.")
                        else:
                            try:
                                res = api.login(username=username, password=password)
                                st.session_state["token"] = res["access_token"]
                                st.session_state["username"] = res["username"]
                                st.session_state["user_id"] = res["user_id"]
                                api.token = res["access_token"]

                                user_info = api.get_me()
                                st.session_state["user"] = user_info

                                prof = api.get_profile()
                                st.session_state["is_onboarded"] = prof.get("is_onboarded", False)
                                st.session_state["user_profile"] = prof

                                st.success(f"Welcome back, {user_info.get('full_name')}!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Login failed: {str(e)}")

            with tab_register:
                with st.form("register_form"):
                    st.subheader("Join DesiFit")
                    full_name = st.text_input("Full Name", placeholder="e.g. Arjun Sharma")
                    email = st.text_input("Email Address", placeholder="arjun@example.com")
                    reg_username = st.text_input("Username", placeholder="Choose unique username")
                    reg_password = st.text_input("Password", type="password", placeholder="At least 6 characters")
                    reg_submitted = st.form_submit_button("Create My Account", use_container_width=True)

                    if reg_submitted:
                        if not full_name or not email or not reg_username or not reg_password:
                            st.error("Please fill in all registration fields.")
                        elif len(reg_password) < 6:
                            st.error("Password must be at least 6 characters long.")
                        else:
                            try:
                                api.register(
                                    email=email,
                                    username=reg_username,
                                    full_name=full_name,
                                    password=reg_password
                                )
                                # Automatically log in after registration
                                login_res = api.login(username=reg_username, password=reg_password)
                                st.session_state["token"] = login_res["access_token"]
                                st.session_state["username"] = login_res["username"]
                                st.session_state["user_id"] = login_res["user_id"]
                                api.token = login_res["access_token"]
                                st.session_state["user"] = api.get_me()

                                # Brand new users start un-onboarded
                                st.session_state["is_onboarded"] = False

                                st.success("Account created successfully! Let's set up your profile.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Registration failed: {str(e)}")
