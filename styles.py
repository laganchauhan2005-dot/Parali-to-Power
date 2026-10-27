"""
Styling and Design System for Parali-to-Power.
Theme: Modern Indian Agriculture + Clean Sustainability Dashboard (Strict Light Mode)
Palette:
- Page background: #F7F8F4
- Cards / Surfaces: #FFFFFF
- Headings and body text: #1F2933
- Secondary text: #52615A
- Primary accent: #1B4332
- Borders: #DCE4DC
- Warning surface: #FFF4CC with dark text #78350F
- Error surface: #FDE8E7 with dark text #991B1B
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Color constants
PRIMARY_FOREST = "#1B4332"
SECONDARY_SAGE = "#52B788"
ACCENT_BEIGE = "#DDA15E"
BG_PAGE = "#F7F8F4"
CARD_WHITE = "#FFFFFF"
TEXT_MAIN = "#1F2933"
TEXT_SECONDARY = "#52615A"
BORDER_LIGHT = "#DCE4DC"
WARN_BG = "#FFF4CC"
ERROR_BG = "#FDE8E7"


def apply_custom_styles():
    """Inject cohesive light-theme CSS rules into the Streamlit session."""
    st.markdown(f"""
    <style>
        /* Import clean modern typography */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

        /* Global Typography & Base Colors */
        html, body, [class*="css"], .stApp {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            background-color: {BG_PAGE} !important;
            color: {TEXT_MAIN} !important;
        }}

        /* Streamlit Top Header (integrated light theme) */
        header[data-testid="stHeader"] {{
            background-color: {BG_PAGE} !important;
            border-bottom: 1px solid {BORDER_LIGHT} !important;
            height: 3.2rem !important;
        }}
        header[data-testid="stHeader"] svg {{
            fill: {TEXT_MAIN} !important;
        }}

        /* Main Container Layout & Spacing - ensure top banner is NEVER clipped */
        .block-container {{
            padding-top: 5.2rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1280px !important;
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid {BORDER_LIGHT} !important;
        }}
        section[data-testid="stSidebar"] * {{
            color: {TEXT_MAIN} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-top: 1px solid {BORDER_LIGHT} !important;
        }}

        /* Headings & Paragraphs */
        h1, h2, h3, h4, h5, h6 {{
            color: {TEXT_MAIN} !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
            margin-top: 0.2rem !important;
            margin-bottom: 0.5rem !important;
        }}
        p, span, label, li {{
            color: {TEXT_MAIN};
        }}
        .stCaption, [data-testid="stCaptionContainer"] p, small {{
            color: {TEXT_SECONDARY} !important;
            font-size: 0.88rem !important;
            margin-bottom: 0.8rem !important;
        }}

        /* Streamlit Native Bordered Containers (Cards) */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {CARD_WHITE} !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 10px !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
            padding: 18px 20px !important;
            margin-bottom: 16px !important;
        }}

        /* Expanders */
        [data-testid="stExpander"] {{
            background-color: {CARD_WHITE} !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 8px !important;
            margin-bottom: 14px !important;
        }}
        [data-testid="stExpander"] details {{
            background-color: {CARD_WHITE} !important;
        }}
        [data-testid="stExpander"] summary {{
            color: {TEXT_MAIN} !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
        }}
        [data-testid="stExpander"] summary svg {{
            fill: {TEXT_MAIN} !important;
        }}

        /* Form Inputs & Controls */
        [data-testid="stWidgetLabel"] label, [data-testid="stWidgetLabel"] p {{
            color: {TEXT_MAIN} !important;
            font-weight: 600 !important;
            font-size: 0.90rem !important;
            margin-bottom: 4px !important;
        }}
        input, textarea {{
            background-color: #FFFFFF !important;
            color: {TEXT_MAIN} !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 6px !important;
        }}
        div[data-baseweb="input"] {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 6px !important;
        }}
        div[data-baseweb="input"]:focus-within {{
            border-color: {PRIMARY_FOREST} !important;
            box-shadow: 0 0 0 1px {PRIMARY_FOREST} !important;
        }}
        div[data-baseweb="input"] input {{
            color: {TEXT_MAIN} !important;
            background-color: #FFFFFF !important;
        }}
        div[data-baseweb="select"] {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 6px !important;
        }}
        div[data-baseweb="select"] * {{
            color: {TEXT_MAIN} !important;
        }}
        div[data-baseweb="popover"], ul[role="listbox"] {{
            background-color: #FFFFFF !important;
        }}
        ul[role="listbox"] li {{
            color: {TEXT_MAIN} !important;
            background-color: #FFFFFF !important;
        }}
        ul[role="listbox"] li:hover {{
            background-color: #F0F4F1 !important;
            color: {PRIMARY_FOREST} !important;
        }}

        /* MULTISELECT FILTER CHIPS (Requirement 2): Pale-green background with dark-green text & visible icons */
        div[data-baseweb="tag"], span[data-baseweb="tag"] {{
            background-color: #E3F2E6 !important;
            border: 1px solid #B4DCBE !important;
            border-radius: 4px !important;
            padding: 2px 6px !important;
        }}
        div[data-baseweb="tag"] span, span[data-baseweb="tag"] span {{
            color: #166534 !important;
            font-weight: 700 !important;
            font-size: 0.82rem !important;
        }}
        div[data-baseweb="tag"] svg, span[data-baseweb="tag"] svg {{
            fill: #166534 !important;
            color: #166534 !important;
        }}
        div[data-baseweb="tag"]:hover, span[data-baseweb="tag"]:hover {{
            background-color: #D1EADB !important;
            border-color: #8FD1A3 !important;
        }}

        /* Buttons (including standard and form submit buttons) */
        div.stButton > button, div[data-testid="stFormSubmitButton"] > button {{
            background-color: {PRIMARY_FOREST} !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border: none !important;
            border-radius: 6px !important;
            padding: 0.5rem 1.25rem !important;
            transition: background-color 0.15s ease-in-out;
        }}
        section[data-testid="stSidebar"] div.stButton > button {{
            padding: 0.45rem 0.6rem !important;
            font-size: 0.82rem !important;
            margin-top: 4px !important;
        }}
        section[data-testid="stSidebar"] div.stButton > button p {{
            font-size: 0.82rem !important;
            white-space: normal !important;
            word-break: break-word !important;
        }}
        div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {{
            background-color: #2D6A4F !important;
            color: #FFFFFF !important;
        }}
        div.stButton > button p, div.stButton > button span,
        div[data-testid="stFormSubmitButton"] > button p, div[data-testid="stFormSubmitButton"] > button span {{
            color: #FFFFFF !important;
        }}

        /* Alerts: Strictly high-contrast dark text on light tinted surfaces */
        div[data-testid="stAlert"] * {{
            color: {TEXT_MAIN} !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]) {{
            background-color: {WARN_BG} !important;
            border: 1px solid #E6D07A !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentError"]) {{
            background-color: {ERROR_BG} !important;
            border: 1px solid #F5B5B2 !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentInfo"]) {{
            background-color: #EBF3EE !important;
            border: 1px solid #C5DBD0 !important;
        }}
        div[data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]) {{
            background-color: #E3F2E6 !important;
            border: 1px solid #B4DCBE !important;
        }}

        /* Tables & DataFrames */
        div[data-testid="stDataFrame"] {{
            background-color: #FFFFFF !important;
            border: 1px solid {BORDER_LIGHT} !important;
            border-radius: 8px !important;
        }}

        /* Top Simulation Banner - fully inside page layout with clear spacing */
        .sim-banner {{
            display: inline-flex !important;
            align-items: center !important;
            background-color: {WARN_BG} !important;
            border: 1px solid #E6D07A !important;
            color: #78350F !important;
            font-size: 0.78rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.05em !important;
            padding: 6px 14px !important;
            border-radius: 6px !important;
            margin-top: 0.2rem !important;
            margin-bottom: 0.8rem !important;
            text-transform: uppercase !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        }}

        /* Metric Box */
        .agri-metric-box {{
            background-color: {CARD_WHITE};
            border: 1px solid {BORDER_LIGHT};
            border-radius: 8px;
            padding: 14px 16px;
            text-align: left;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        }}
        .agri-metric-label {{
            font-size: 0.80rem;
            font-weight: 700;
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }}
        .agri-metric-val {{
            font-size: 1.75rem;
            font-weight: 700;
            color: {PRIMARY_FOREST};
            line-height: 1.2;
        }}
        .agri-metric-sub {{
            font-size: 0.80rem;
            color: {TEXT_SECONDARY};
            margin-top: 4px;
        }}

        /* Status Badges */
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .badge-unassigned {{ background-color: {ERROR_BG}; color: #991B1B; border: 1px solid #F5B5B2; }}
        .badge-scheduled {{ background-color: {WARN_BG}; color: #92400E; border: 1px solid #E6D07A; }}
        .badge-in_collection {{ background-color: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE; }}
        .badge-in_transit {{ background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }}
        .badge-completed {{ background-color: #E3F2E6; color: #166534; border: 1px solid #B4DCBE; }}
        .badge-cancelled {{ background-color: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }}
    </style>
    """, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Render a clean HTML pill badge for a given state."""
    normalized = status.lower().strip()
    label = status.replace("_", " ").upper()
    return f'<span class="badge badge-{normalized}">{label}</span>'


def apply_plotly_theme(fig):
    """Apply consistent light forest/sage styling and clean spacing to Plotly figures."""
    fig.update_layout(
        font=dict(family="Plus Jakarta Sans, sans-serif", color=TEXT_MAIN, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1,
            font=dict(size=11, color=TEXT_MAIN)
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="#EBF0E9",
            linecolor=BORDER_LIGHT,
            tickfont=dict(color=TEXT_MAIN),
            title_font=dict(color=TEXT_MAIN),
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#EBF0E9",
            linecolor=BORDER_LIGHT,
            tickfont=dict(color=TEXT_MAIN),
            title_font=dict(color=TEXT_MAIN),
            zeroline=False
        )
    )
    return fig
