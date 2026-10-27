"""
Overview Dashboard View for Parali-to-Power.
Displays live operational metrics computed directly from SQLite,
Needs Attention panel, and Plotly visualizations in clean light theme.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from core.db import get_db_connection
from styles import (
    apply_plotly_theme,
    get_status_badge_html,
    PRIMARY_FOREST,
    SECONDARY_SAGE,
    ACCENT_BEIGE,
    TEXT_MAIN,
    TEXT_SECONDARY,
    BORDER_LIGHT,
    WARN_BG
)


def render_dashboard():
    st.markdown('<div class="sim-banner">Simulated Demo Data — TPPC 2026 Evaluation</div>', unsafe_allow_html=True)
    st.title("🌾 Operations Overview Dashboard")
    st.caption("Real-time regional biomass collection, provider dispatch, and energy-depot logistics coordination.")

    conn = get_db_connection()

    # Load live counts and statistics
    req_df = pd.read_sql_query("SELECT * FROM requests", conn)
    prov_df = pd.read_sql_query("SELECT * FROM providers", conn)
    buyer_df = pd.read_sql_query("SELECT * FROM buyers", conn)
    job_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    conn.close()

    total_reqs = len(req_df)
    unassigned_cnt = len(req_df[req_df["status"] == "UNASSIGNED"])
    scheduled_cnt = len(req_df[req_df["status"].isin(["SCHEDULED", "IN_COLLECTION", "IN_TRANSIT"])])
    completed_cnt = len(req_df[req_df["status"] == "COMPLETED"])

    total_tonnage_logged = req_df["estimated_tonnage"].sum() if not req_df.empty else 0.0
    active_jobs_tonnage = req_df[req_df["status"].isin(["SCHEDULED", "IN_COLLECTION", "IN_TRANSIT"])]["estimated_tonnage"].sum()
    delivered_tonnage = req_df[req_df["status"] == "COMPLETED"]["estimated_tonnage"].sum()

    total_est_km = job_df["estimated_distance_km"].sum() if not job_df.empty else 0.0

    # 1. Primary Operational Metrics Grid
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(f"""
        <div class="agri-metric-box">
            <div class="agri-metric-label">Submitted Requests</div>
            <div class="agri-metric-val">{total_reqs}</div>
            <div class="agri-metric-sub">{total_tonnage_logged:.1f} tonnes total</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="agri-metric-box">
            <div class="agri-metric-label">Unassigned</div>
            <div class="agri-metric-val" style="color: #BC4749;">{unassigned_cnt}</div>
            <div class="agri-metric-sub">Awaiting dispatch</div>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="agri-metric-box">
            <div class="agri-metric-label">In Pipeline</div>
            <div class="agri-metric-val" style="color: #2D6A4F;">{scheduled_cnt}</div>
            <div class="agri-metric-sub">{active_jobs_tonnage:.1f}t committed</div>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="agri-metric-box">
            <div class="agri-metric-label">Completed Deliveries</div>
            <div class="agri-metric-val" style="color: #1B4332;">{completed_cnt}</div>
            <div class="agri-metric-sub">{delivered_tonnage:.1f}t verified at plants</div>
        </div>
        """, unsafe_allow_html=True)

    with m5:
        st.markdown(f"""
        <div class="agri-metric-box">
            <div class="agri-metric-label">Transit Distance</div>
            <div class="agri-metric-val">{total_est_km:.1f} <span style="font-size:1rem; font-weight:500;">km</span></div>
            <div class="agri-metric-sub">Active & completed jobs</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 2. Needs Attention Panel & Status Distribution
    c_left, c_right = st.columns([1.2, 0.8])

    with c_left:
        with st.container(border=True):
            st.subheader("⚠️ Urgent Needs Attention")
            st.caption("Requests nearing sowing cutoff dates and resource capacity constraints.")

            urgent_unassigned = req_df[
                (req_df["status"] == "UNASSIGNED") & 
                (req_df["sowing_deadline"] <= "2026-11-01")
            ]

            if not urgent_unassigned.empty:
                for _, r in urgent_unassigned.iterrows():
                    st.warning(
                        f"**Request {r['id']} ({r['farmer_name']}, {r['village']})**: "
                        f"{r['estimated_tonnage']}t {r['crop_residue_type']} — "
                        f"**Deadline: {r['sowing_deadline']}** (Immediate dispatch needed before sowing!)"
                    )
            else:
                st.info("No unassigned requests currently at imminent risk of deadline breach.")

            offline_provs = prov_df[prov_df["status"] != "ACTIVE"]
            if not offline_provs.empty:
                for _, p in offline_provs.iterrows():
                    st.error(f"🚜 Provider **{p['name']}** is {p['status']}: capacity unavailable.")

            full_buyers = buyer_df[buyer_df["status"] == "QUOTA_FULL"]
            if not full_buyers.empty:
                for _, b in full_buyers.iterrows():
                    st.markdown(f"🏭 Off-taker **{b['name']}**: daily receiving quota reached (100% full).")

    with c_right:
        with st.container(border=True):
            st.subheader("📊 Request Status Distribution")
            st.caption("Current state of registered parali collection requests.")

            if not req_df.empty:
                status_counts = req_df["status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]

                color_map = {
                    "UNASSIGNED": "#E76F51",
                    "SCHEDULED": "#E9C46A",
                    "IN_COLLECTION": "#2A9D8F",
                    "IN_TRANSIT": "#457B9D",
                    "COMPLETED": "#2D6A4F",
                    "CANCELLED": "#6C757D"
                }

                fig_donut = px.pie(
                    status_counts,
                    names="Status",
                    values="Count",
                    hole=0.55,
                    color="Status",
                    color_discrete_map=color_map
                )
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                fig_donut = apply_plotly_theme(fig_donut)
                fig_donut.update_layout(height=240, showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_donut, use_container_width=True)

    # 3. Geospatial Coordination Map
    with st.container(border=True):
        st.subheader("🗺️ Regional Hub & Supply Cluster Coordination (Punjab & Haryana)")
        st.caption("Simulated coordinates for farmer collection points, custom hiring machinery centers, and biomass power off-takers.")

        map_points = []
        for _, r in req_df.iterrows():
            map_points.append({
                "Name": f"Req {r['id']} ({r['farmer_name']})",
                "Type": "Farm Request",
                "District": r["district"],
                "Details": f"{r['estimated_tonnage']}t {r['crop_residue_type']} [{r['status']}]",
                "Lat": r["latitude"],
                "Lon": r["longitude"],
                "Size": 10
            })

        for _, p in prov_df.iterrows():
            map_points.append({
                "Name": p["name"],
                "Type": "Machinery Hub (CHC)",
                "District": p["district"],
                "Details": f"{p['equipment_types']} | Cap: {p['daily_capacity_tonnes']}t/d",
                "Lat": p["latitude"],
                "Lon": p["longitude"],
                "Size": 16
            })

        for _, b in buyer_df.iterrows():
            map_points.append({
                "Name": b["name"],
                "Type": "Biomass Energy Buyer",
                "District": b["district"],
                "Details": f"{b['facility_type']} | Intake: {b['daily_intake_capacity_tonnes']}t/d",
                "Lat": b["latitude"],
                "Lon": b["longitude"],
                "Size": 18
            })

        map_df = pd.DataFrame(map_points)

        fig_map = px.scatter(
            map_df,
            x="Lon",
            y="Lat",
            color="Type",
            hover_name="Name",
            hover_data={"District": True, "Details": True, "Lat": False, "Lon": False},
            size="Size",
            color_discrete_map={
                "Farm Request": "#E76F51",
                "Machinery Hub (CHC)": "#2A9D8F",
                "Biomass Energy Buyer": "#1B4332"
            }
        )
        fig_map = apply_plotly_theme(fig_map)
        fig_map.update_layout(
            height=340,
            xaxis_title="Longitude (°E)",
            yaxis_title="Latitude (°N)",
            margin=dict(l=40, r=20, t=10, b=40)
        )
        st.plotly_chart(fig_map, use_container_width=True)
