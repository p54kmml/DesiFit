CUSTOM_CSS = """
<style>
/* Main Background & Fonts */
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d;
}

section[data-testid="stSidebar"] .stMarkdown h2, 
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a3e635 !important;
}

/* Primary buttons - Lime Green */
div.stButton > button:first-child {
    background-color: #a3e635 !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.55rem 1.25rem !important;
    transition: all 0.2s ease-in-out;
}

div.stButton > button:first-child:hover {
    background-color: #bef264 !important;
    color: #000000 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(163, 230, 53, 0.35);
}

/* Secondary / Outline buttons */
div.stButton > button[kind="secondary"] {
    background-color: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
}

/* Input Fields & Selectboxes */
input, textarea, select, div[data-baseweb="select"] {
    background-color: #161b22 !important;
    color: #f0f6fc !important;
    border-color: #30363d !important;
    border-radius: 6px !important;
}

/* Cards & Containers */
.desifit-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}

.desifit-metric-box {
    background: linear-gradient(135deg, #161b22 0%, #1f242c 100%);
    border: 1px solid #30363d;
    border-top: 3px solid #a3e635;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 15px;
}

.desifit-metric-title {
    font-size: 0.85rem;
    color: #8b949e;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.desifit-metric-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: #ffffff;
    margin-top: 4px;
}

.desifit-metric-sub {
    font-size: 0.82rem;
    color: #a3e635;
    margin-top: 4px;
}

/* Header & Logo styling */
.desifit-header-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 16px;
    margin-bottom: 24px;
    border-bottom: 1px solid #30363d;
}

.desifit-brand {
    font-size: 1.8rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.5px;
}

.desifit-brand span {
    color: #a3e635;
}

.desifit-badge {
    background-color: rgba(163, 230, 53, 0.15);
    color: #a3e635;
    border: 1px solid rgba(163, 230, 53, 0.3);
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
}

/* Chat bubble styling */
.user-chat-bubble {
    background-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 12px 12px 2px 12px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #f0f6fc;
}

.ai-chat-bubble {
    background-color: #161b22;
    border: 1px solid #38424e;
    border-left: 3px solid #a3e635;
    border-radius: 12px 12px 12px 2px;
    padding: 14px 18px;
    margin: 8px 0;
    color: #f0f6fc;
}

/* Streamlit Tabs */
button[data-baseweb="tab"] {
    color: #8b949e !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #a3e635 !important;
    border-bottom-color: #a3e635 !important;
}
</style>
"""


def render_logo(size: str = "normal") -> str:
    font_size = "1.8rem" if size == "normal" else "2.4rem"
    return f"""
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
        <div style="background: #a3e635; color: #0d1117; width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; font-weight: 900; box-shadow: 0 0 15px rgba(163, 230, 53, 0.5);">
            ⚡
        </div>
        <div>
            <div style="font-size: {font_size}; font-weight: 900; color: #ffffff; line-height: 1.1; letter-spacing: -0.5px;">
                DESI<span style="color: #a3e635;">FIT</span>
            </div>
            <div style="font-size: 0.72rem; color: #8b949e; letter-spacing: 1px; text-transform: uppercase; font-weight: 600;">
                AI Fitness Companion
            </div>
        </div>
    </div>
    """


def render_metric_card(title: str, value: str, subtext: str = "", border_color: str = "#a3e635") -> str:
    return f"""
    <div style="background: linear-gradient(135deg, #161b22 0%, #1c222b 100%); border: 1px solid #30363d; border-top: 3px solid {border_color}; border-radius: 10px; padding: 16px 18px; margin-bottom: 12px; height: 100%;">
        <div style="font-size: 0.75rem; color: #8b949e; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">
            {title}
        </div>
        <div style="font-size: 1.7rem; font-weight: 800; color: #ffffff; margin-top: 4px;">
            {value}
        </div>
        <div style="font-size: 0.8rem; color: {border_color}; margin-top: 4px; font-weight: 500;">
            {subtext}
        </div>
    </div>
    """
