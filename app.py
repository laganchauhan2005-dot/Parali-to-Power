"""
Parali-to-Power: An Intelligent Biomass Supply & Energy Coordination System
Main Application Entry Point for TPPC-2026.
"""
import streamlit as st
import os

# Page configuration
st.set_page_config(
    page_title="Parali-to-Power | Biomass Coordination",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database is initialized before any view renders
from core.db import init_db, reset_database, get_db_connection
from styles import apply_custom_styles, PRIMARY_FOREST, TEXT_MAIN, TEXT_SECONDARY, BORDER_LIGHT, WARN_BG
from views.dashboard import render_dashboard
from views.farmer_requests import render_farmer_requests
from views.scheduling import render_scheduling
from views.buyers import render_buyers
from views.job_tracking import render_job_tracking
from views.algorithm_eval import render_evaluation

# Initialize SQLite database schema and seed data if fresh
init_db(seed=True)

# Apply cohesive light-mode styling
apply_custom_styles()


def render_sidebar():
    """Render the persistent sidebar navigation and control panel."""
    with st.sidebar:
        # App Branding Header
        st.markdown(f"""
        <div style="padding: 4px 0 14px 0;">
            <div style="font-size: 1.35rem; font-weight: 800; color: {PRIMARY_FOREST}; line-height: 1.2;">
                🌾 Parali-to-Power
            </div>
            <div style="font-size: 0.80rem; font-weight: 700; color: #2D6A4F; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 3px;">
                Intelligent Biomass Coordination
            </div>
            <div style="font-size: 0.74rem; color: {TEXT_SECONDARY}; margin-top: 2px;">
                TPPC-2026 Technical Poster Presentation
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: {WARN_BG}; border: 1px solid #E6D07A; border-radius: 6px; padding: 8px 10px; margin-bottom: 16px;">
            <div style="font-size: 0.74rem; font-weight: 700; color: #78350F; text-transform: uppercase; letter-spacing: 0.04em;">
                ⚠️ Simulated Demo Data
            </div>
            <div style="font-size: 0.72rem; color: #78350F; margin-top: 3px; line-height: 1.3;">
                Synthetic demonstration records for Punjab/Haryana supply clusters.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<p style='font-size: 0.80rem; font-weight: 700; color: {TEXT_SECONDARY}; text-transform: uppercase; margin-bottom: 6px;'>Navigation</p>", unsafe_allow_html=True)

        nav_options = [
            "1. Operations Overview",
            "2. Farmer Requests",
            "3. Providers & Scheduling",
            "4. Buyers & Deliveries",
            "5. Field Job Tracking",
            "6. Algorithm Evaluation"
        ]

        choice = st.radio(
            "Select Page",
            options=nav_options,
            index=0,
            label_visibility="collapsed"
        )

        st.markdown(f"<hr style='margin: 18px 0 14px 0; border:0; border-top: 1px solid {BORDER_LIGHT};'>", unsafe_allow_html=True)

        # Quick DB Status Summary
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM requests")
        num_reqs = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM jobs WHERE status != 'CANCELLED'")
        num_jobs = cur.fetchone()[0]
        conn.close()

        st.markdown(f"""
        <div style="font-size: 0.80rem; color: {TEXT_SECONDARY}; line-height: 1.5; margin-bottom: 14px;">
            <strong style="color: {TEXT_MAIN};">System State:</strong><br/>
            • Total Requests: <strong style="color: {TEXT_MAIN};">{num_reqs}</strong><br/>
            • Active / Done Jobs: <strong style="color: {TEXT_MAIN};">{num_jobs}</strong><br/>
            • Persistence: <strong style="color: {PRIMARY_FOREST};">SQLite (Active)</strong>
        </div>
        """, unsafe_allow_html=True)

        # Reset button to return to clean demo state
        if st.button("🔄 Reset Demo Scenario Data", use_container_width=True):
            reset_database()
            st.session_state.last_submission = None
            st.success("Database restored to initial state!")
            st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.caption("TPPC-2026 Competition Entry • System v1.0")

    return choice


def main():
    selected_page = render_sidebar()

    if "1. Operations Overview" in selected_page:
        render_dashboard()
    elif "2. Farmer Requests" in selected_page:
        render_farmer_requests()
    elif "3. Providers & Scheduling" in selected_page:
        render_scheduling()
    elif "4. Buyers & Deliveries" in selected_page:
        render_buyers()
    elif "5. Field Job Tracking" in selected_page:
        render_job_tracking()
    elif "6. Algorithm Evaluation" in selected_page:
        render_evaluation()


if __name__ == "__main__":
    main()
