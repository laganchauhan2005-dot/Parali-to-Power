"""
Service Providers & Scheduling View for Parali-to-Power.
Evaluates candidate pairs with hard feasibility rules, transparent ranking,
and explicit rejection explanations in a clean, spacious light layout.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from core.db import get_db_connection
from core.scheduler import (
    evaluate_candidates_for_request,
    assign_and_schedule_job
)
from styles import (
    get_status_badge_html,
    PRIMARY_FOREST,
    SECONDARY_SAGE,
    TEXT_MAIN,
    TEXT_SECONDARY,
    BORDER_LIGHT,
    WARN_BG,
    ERROR_BG
)


def render_scheduling():
    st.markdown('<div class="sim-banner">Simulated Demo Data — Intelligent Scheduling Engine</div>', unsafe_allow_html=True)
    st.title("🚜 Service Providers & Intelligent Scheduling")
    st.caption("Coordinate field baling fleets, assess hard physical and operational feasibility constraints, and dispatch to verified energy off-takers.")

    # 1. Registered Service Providers Fleet Overview
    with st.expander("🔍 View All Registered Machinery Hubs (CHCs) & Fleet Status", expanded=False):
        conn = get_db_connection()
        p_df = pd.read_sql_query("SELECT id, name, district, hub_location, equipment_types, daily_capacity_tonnes, max_service_radius_km, base_rate_per_tonne, status FROM providers", conn)
        conn.close()
        st.dataframe(p_df.rename(columns={
            "id": "Provider ID",
            "name": "Hub / Organization",
            "hub_location": "Base Town",
            "equipment_types": "Fleet Machinery",
            "daily_capacity_tonnes": "Capacity (t/day)",
            "max_service_radius_km": "Max Radius (km)",
            "base_rate_per_tonne": "Rate (₹/tonne)",
            "status": "Operational Status"
        }), use_container_width=True, hide_index=True)

    # 2. Select an Unassigned Request to Schedule
    conn = get_db_connection()
    unassigned_reqs = pd.read_sql_query("SELECT * FROM requests WHERE status = 'UNASSIGNED' ORDER BY sowing_deadline ASC", conn)
    conn.close()

    with st.container(border=True):
        st.subheader("🎯 Schedule an Unassigned Residue Request")

        if unassigned_reqs.empty:
            st.success("🎉 All registered requests have been scheduled or completed! You can create a new request in the 'Farmer Requests' view.")
            return

        # Select box to pick request
        req_labels = [
            f"{r['id']} — {r['farmer_name']} ({r['village']}, {r['district']}) | {r['estimated_tonnage']}t {r['crop_residue_type']} | Deadline: {r['sowing_deadline']}"
            for _, r in unassigned_reqs.iterrows()
        ]
        selected_idx = st.selectbox("Select Pending Request for Automated Matching", range(len(req_labels)), format_func=lambda i: req_labels[i])
        selected_req = unassigned_reqs.iloc[selected_idx].to_dict()

        # Request Detail Card (Soft-tinted background, no duplicate white nested box)
        st.markdown(f"""
        <div style="background-color: #F7F8F4; border: 1px solid {BORDER_LIGHT}; padding: 12px 16px; border-radius: 8px; margin-top: 10px; margin-bottom: 14px;">
            <div style="display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                <div><strong style="color:{TEXT_MAIN};">Farmer:</strong> {selected_req['farmer_name']} &nbsp;|&nbsp; <strong style="color:{TEXT_MAIN};">Location:</strong> {selected_req['village']}, {selected_req['district']}</div>
                <div><span class="badge badge-unassigned">STATUS: UNASSIGNED</span></div>
            </div>
            <div style="margin-top: 6px; font-size: 0.88rem; color: {TEXT_SECONDARY};">
                🌾 <strong>Crop Residue:</strong> {selected_req['estimated_tonnage']} tonnes of {selected_req['crop_residue_type']} &nbsp;|&nbsp; 
                📅 <strong>Harvest Date:</strong> {selected_req['harvest_date']} &nbsp;|&nbsp; 
                ⚠️ <strong>Sowing Deadline:</strong> <span style="color:#BC4749; font-weight:700;">{selected_req['sowing_deadline']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Target dispatch date selector
        c_date, _ = st.columns([1, 2])
        with c_date:
            target_date = st.date_input("Target Collection Dispatch Date", value=datetime.strptime(selected_req["harvest_date"], "%Y-%m-%d").date())
            target_date_str = target_date.strftime("%Y-%m-%d")

    # Run Feasibility & Ranking Engine
    eval_result = evaluate_candidates_for_request(selected_req["id"], target_date_str)
    feasible_matches = eval_result.get("feasible_matches", [])
    rejections = eval_result.get("rejections", [])

    # Feasible Matches Section
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.subheader(f"✅ Feasible Candidate Matches ({len(feasible_matches)})")
    st.caption("Ranked by explainable multi-factor score: Proximity (50%) + Sowing Deadline Buffer (30%) + Service Cost Efficiency (20%).")

    if not feasible_matches:
        with st.container(border=True):
            st.error("❌ No feasible candidate combinations passed all hard physical and capacity constraints for this date.")
            st.info("Inspect the Infeasibility Audit below to see why each provider or buyer was rejected.")
    else:
        # Display each match in a spacious, clear card
        for idx, match in enumerate(feasible_matches):
            with st.container(border=True):
                # Header row
                c_top1, c_top2 = st.columns([3, 1])
                with c_top1:
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                        <span style="font-size: 1.15rem; font-weight: 800; color: {PRIMARY_FOREST};">
                            #{idx+1} Match Option
                        </span>
                        <span style="background-color: #E3F2E6; color: #166534; font-weight: 700; font-size: 0.82rem; padding: 3px 10px; border-radius: 6px; border: 1px solid #B4DCBE;">
                            Score: {match['score']} / 100
                        </span>
                        <span style="background-color: {WARN_BG}; color: #78350F; font-weight: 600; font-size: 0.82rem; padding: 3px 10px; border-radius: 6px; border: 1px solid #E6D07A;">
                            ⏱️ {match['slack_days_before_deadline']} days deadline buffer
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with c_top2:
                    btn_key = f"assign_btn_{selected_req['id']}_{match['provider_id']}_{match['buyer_id']}"
                    if st.button(f"Confirm Assignment #{idx+1}", key=btn_key, use_container_width=True):
                        ok, msg = assign_and_schedule_job(
                            request_id=selected_req["id"],
                            provider_id=match["provider_id"],
                            buyer_id=match["buyer_id"],
                            scheduled_date=target_date_str,
                            notes=f"Auto-matched via Intelligent Scheduler (Score: {match['score']})"
                        )
                        if ok:
                            st.success(f"🎉 {msg}")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: {msg}")

                # Logistics Details Grid
                c_det1, c_det2, c_det3, c_det4 = st.columns(4)
                with c_det1:
                    st.markdown(f"""
                    <div style="font-size:0.80rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">Machinery Provider</div>
                    <div style="font-size:0.95rem; font-weight:700; color:{TEXT_MAIN};">{match['provider_name']}</div>
                    <div style="font-size:0.82rem; color:{TEXT_SECONDARY};">{match['provider_district']} ({match['distance_prov_km']} km to farm)</div>
                    """, unsafe_allow_html=True)

                with c_det2:
                    st.markdown(f"""
                    <div style="font-size:0.80rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">Energy Off-Taker</div>
                    <div style="font-size:0.95rem; font-weight:700; color:{TEXT_MAIN};">{match['buyer_name']}</div>
                    <div style="font-size:0.82rem; color:{TEXT_SECONDARY};">{match['buyer_type']} ({match['distance_buyer_km']} km)</div>
                    """, unsafe_allow_html=True)

                with c_det3:
                    st.markdown(f"""
                    <div style="font-size:0.80rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">Total Transit Distance</div>
                    <div style="font-size:1.15rem; font-weight:700; color:{PRIMARY_FOREST};">{match['total_distance_km']} km</div>
                    <div style="font-size:0.82rem; color:{TEXT_SECONDARY};">Hub ➔ Farm ➔ Plant</div>
                    """, unsafe_allow_html=True)

                with c_det4:
                    st.markdown(f"""
                    <div style="font-size:0.80rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">Financial Estimate</div>
                    <div style="font-size:1.0rem; font-weight:700; color:{TEXT_MAIN};">₹{match['estimated_service_cost_inr']:,.2f}</div>
                    <div style="font-size:0.82rem; color:{SECONDARY_SAGE}; font-weight:600;">Plant Value: ₹{match['estimated_buyer_payout_inr']:,.2f}</div>
                    """, unsafe_allow_html=True)

    # Rejection and Infeasibility Audit Section
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("🚫 Infeasibility Audit & Rejection Explanations")
        st.caption("Transparent evaluation: reasons why candidates did not qualify for this specific request.")

        if not rejections:
            st.info("No candidates were rejected for this request.")
        else:
            rej_cols = st.columns(2)
            for i, rej in enumerate(rejections):
                col = rej_cols[i % 2]
                with col:
                    with st.expander(f"{rej['type']}: {rej['name']}", expanded=True):
                        for reason in rej["reasons"]:
                            st.markdown(f"""
                            <div style="display:flex; align-items:flex-start; gap:8px; margin-bottom:4px; font-size:0.88rem; color:#1F2933;">
                                <span style="color:#BC4749; font-weight:700;">✕</span>
                                <span>{reason}</span>
                            </div>
                            """, unsafe_allow_html=True)
