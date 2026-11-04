# utils/theme.py — ExamFlow AI Premium Dark Theme CSS Design System
import streamlit as st


def inject_css():
    """Inject the full CSS design system into the Streamlit app."""
    st.markdown("""
    <style>
    /* ─── Global Reset ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: linear-gradient(180deg, #0B0E17 0%, #0F1320 50%, #0B0E17 100%);
    }

    /* ─── Ambient Glow ─────────────────────────────────────────── */
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 20% 80%, rgba(108,99,255,0.04) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(0,217,255,0.03) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(0,230,118,0.02) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
    }

    /* ─── Sidebar ──────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F1320 0%, #131726 100%);
        border-right: 1px solid rgba(108,99,255,0.15);
    }

    section[data-testid="stSidebar"] .stRadio label {
        color: #9AA0A6 !important;
        padding: 0.6rem 1rem !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
        font-size: 0.9rem !important;
    }

    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #E8EAED !important;
        background: rgba(108,99,255,0.1) !important;
    }

    /* ─── Buttons ──────────────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #6C63FF 0%, #5A52E0 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(108,99,255,0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(108,99,255,0.5);
        background: linear-gradient(135deg, #7B73FF 0%, #6C63FF 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* ─── Cards ────────────────────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, #131726 0%, #1C2035 100%);
        border: 1px solid #2D3143;
        border-radius: 14px;
        padding: 1.3rem;
        margin-bottom: 0.8rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #6C63FF, #00D9FF);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .metric-card:hover {
        border-color: rgba(108,99,255,0.4);
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(108,99,255,0.15);
    }

    .metric-card:hover::before {
        opacity: 1;
    }

    .metric-card h3 {
        color: #E8EAED;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0 0 0.4rem 0;
        letter-spacing: 0.01em;
    }

    .metric-card .metric-value {
        color: #6C63FF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }

    .metric-card .metric-sub {
        color: #9AA0A6;
        font-size: 0.75rem;
        margin: 0.3rem 0 0 0;
    }

    /* ─── Glass Panel ─────────────────────────────────────────── */
    .glass-panel {
        background: rgba(19, 23, 38, 0.7);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(108,99,255,0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    /* ─── Session Card ────────────────────────────────────────── */
    .session-card {
        background: linear-gradient(135deg, #131726 0%, #1C2035 100%);
        border: 1px solid #2D3143;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s ease;
    }

    .session-card:hover {
        border-color: rgba(108,99,255,0.3);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    .session-time {
        color: #00D9FF;
        font-size: 0.85rem;
        font-weight: 600;
        min-width: 80px;
    }

    .session-subject {
        color: #E8EAED;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .session-topic {
        color: #9AA0A6;
        font-size: 0.8rem;
    }

    /* ─── Priority Badges ─────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .badge-easy { background: rgba(0,230,118,0.15); color: #00E676; }
    .badge-medium { background: rgba(255,183,64,0.15); color: #FFB740; }
    .badge-hard { background: rgba(255,82,82,0.15); color: #FF5252; }
    .badge-high { background: rgba(108,99,255,0.15); color: #6C63FF; }
    .badge-info { background: rgba(0,217,255,0.15); color: #00D9FF; }
    .badge-success { background: rgba(0,230,118,0.15); color: #00E676; }
    .badge-warning { background: rgba(255,183,64,0.15); color: #FFB740; }
    .badge-danger { background: rgba(255,82,82,0.15); color: #FF5252; }

    .badge-planned { background: rgba(0,217,255,0.15); color: #00D9FF; }
    .badge-completed { background: rgba(0,230,118,0.15); color: #00E676; }
    .badge-skipped { background: rgba(255,183,64,0.15); color: #FFB740; }

    /* ─── Progress Bar ────────────────────────────────────────── */
    .progress-container {
        background: #1C2035;
        border-radius: 10px;
        overflow: hidden;
        height: 10px;
        margin: 0.5rem 0;
    }

    .progress-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.6s ease;
        background: linear-gradient(90deg, #6C63FF, #00D9FF);
    }

    /* ─── Topic Tree ──────────────────────────────────────────── */
    .topic-tree {
        padding: 0.3rem 0;
    }

    .topic-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0.8rem;
        border-radius: 8px;
        margin: 0.2rem 0;
        transition: background 0.2s ease;
    }

    .topic-item:hover {
        background: rgba(108,99,255,0.08);
    }

    .unit-header {
        color: #00D9FF;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.8rem 0 0.3rem 0;
        border-bottom: 1px solid rgba(0,217,255,0.15);
        margin-bottom: 0.3rem;
    }

    /* ─── Reasoning Box ───────────────────────────────────────── */
    .reasoning-box {
        background: rgba(108,99,255,0.08);
        border-left: 3px solid #6C63FF;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
        font-size: 0.85rem;
        color: #BFC3C9;
        line-height: 1.6;
    }

    .reasoning-box .reasoning-label {
        color: #6C63FF;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* ─── Inputs ───────────────────────────────────────────────── */
    .stTextInput input, .stNumberInput input, .stDateInput input,
    .stTextArea textarea, .stSelectbox select {
        background: #1C2035 !important;
        border: 1px solid #2D3143 !important;
        color: #E8EAED !important;
        border-radius: 10px !important;
        transition: border-color 0.3s ease !important;
    }

    .stTextInput input:focus, .stNumberInput input:focus,
    .stTextArea textarea:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,0.2) !important;
    }

    /* ─── Expander ─────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        background: #131726 !important;
        border: 1px solid #2D3143 !important;
        border-radius: 10px !important;
        color: #E8EAED !important;
        font-weight: 500 !important;
    }

    /* ─── Tabs ─────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #9AA0A6;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: 1px solid transparent;
        transition: all 0.3s ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #E8EAED;
        background: rgba(108,99,255,0.1);
    }

    .stTabs [aria-selected="true"] {
        background: rgba(108,99,255,0.15) !important;
        color: #6C63FF !important;
        border-color: #6C63FF !important;
    }

    /* ─── Scrollbar ────────────────────────────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0E17;
    }
    ::-webkit-scrollbar-thumb {
        background: #2D3143;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #6C63FF;
    }

    /* ─── Animations ───────────────────────────────────────────── */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 15px rgba(108,99,255,0.2); }
        50% { box-shadow: 0 0 30px rgba(108,99,255,0.4); }
    }

    .fade-in {
        animation: fadeInUp 0.5s ease-out;
    }

    /* ─── Divider ──────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid #2D3143;
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    """Render a page header with gradient title."""
    sub_html = f'<p style="font-size: 1rem; color: #9AA0A6; margin: 0.5rem 0 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="fade-in" style="margin-bottom: 2rem;">
        <h1 style="font-size: 2rem; margin: 0; letter-spacing: -0.02em;
                    background: linear-gradient(135deg, #6C63FF, #00D9FF);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            {title}
        </h1>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    """Render a section divider with title."""
    st.markdown(f'<h3 style="color: #E8EAED; font-size: 1.1rem; margin: 1.5rem 0 0.8rem 0; font-weight: 600;">{title}</h3>', unsafe_allow_html=True)


def metric_card(label: str, value: str, subtitle: str = ""):
    """Render a single metric card."""
    sub_html = f'<p class="metric-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="metric-card">
        <h3>{label}</h3>
        <p class="metric-value">{value}</p>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def glass_panel(content: str):
    """Render content inside a glassmorphism panel."""
    st.markdown(f'<div class="glass-panel">{content}</div>', unsafe_allow_html=True)


def badge(text: str, variant: str = "info"):
    """Return HTML for a status badge. variant: easy|medium|hard|high|info|success|warning|danger|planned|completed|skipped"""
    return f'<span class="badge badge-{variant}">{text}</span>'


def difficulty_badge(level: str):
    """Return HTML for a difficulty badge."""
    return badge(level.upper(), level.lower())


def progress_bar(value: float, max_val: float = 100.0, color: str = ""):
    """Render a progress bar (0 to max_val)."""
    pct = min((value / max_val) * 100, 100) if max_val > 0 else 0
    style = f"background: {color};" if color else "background: linear-gradient(90deg, #6C63FF, #00D9FF);"
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-fill" style="width: {pct}%; {style}"></div>
    </div>
    """, unsafe_allow_html=True)


def reasoning_box(reasoning: str):
    """Display an AI reasoning box."""
    st.markdown(f"""
    <div class="reasoning-box">
        <div class="reasoning-label">🧠 AI Reasoning</div>
        {reasoning}
    </div>
    """, unsafe_allow_html=True)


def confidence_bar(score: float, color: str = "#6C63FF"):
    """Render a confidence bar (0.0 to 1.0)."""
    pct = min(score * 100, 100)
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div class="progress-container" style="flex: 1;">
            <div class="progress-fill" style="width: {pct}%; background: {color};"></div>
        </div>
        <span style="color: {color}; font-size: 0.8rem; font-weight: 600; min-width: 40px;">{pct:.0f}%</span>
    </div>
    """, unsafe_allow_html=True)
