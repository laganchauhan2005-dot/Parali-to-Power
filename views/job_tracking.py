"""
Job Tracking View for Parali-to-Power.
Allows field dispatchers and coordinators to track active jobs,
transition status through valid lifecycle stages, and audit operational notes.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from core.db import get_db_connection
from core.scheduler import update_job_status
from styles import get_status_badge_html, TEXT_MAIN, TEXT_SECONDARY, BORDER_LIGHT, PRIMARY_FOREST


def render_job_tracking():
    st.markdown('<div class="sim-banner">Simulated Demo Data — Dispatch & Logistics Tracking</div>', unsafe_allow_html=True)
    st.title("📍 Field Job Tracking & Logistics Pipeline")
    st.caption("Manage execution lifecycle: Scheduled ➔ In-Field Collection ➔ In-Transit ➔ Delivered & Verified.")

    conn = get_db_connection()
    jobs_df = pd.read_sql_query("""
        SELECT j.*, 
               r.farmer_name, r.village, r.district as farm_district, r.crop_residue_type, r.estimated_tonnage, r.sowing_deadline,
               p.name as provider_name, p.hub_location as provider_hub,
               b.name as buyer_name, b.facility_type
        FROM jobs j
        JOIN requests r ON j.request_id = r.id
        JOIN providers p ON j.provider_id = p.id
        JOIN buyers b ON j.buyer_id = b.id
        ORDER BY j.updated_at DESC
    """, conn)
    conn.close()

    if jobs_df.empty:
        st.info("No jobs have been scheduled yet. Schedule a pending request from the 'Service Providers & Scheduling' view.")
        return

    # 1. Job Lifecycle Transition Station
    with st.container(border=True):
        st.subheader("⚙️ Update Active Job Status")

        job_options = [
            f"{r['id']} — {r['farmer_name']} ({r['village']}) ➔ {r['buyer_name']} [{r['status']}]"
            for _, r in jobs_df.iterrows()
        ]
        selected_idx = st.selectbox("Select Job to Inspect or Advance", range(len(job_options)), format_func=lambda i: job_options[i])
        selected_job = jobs_df.iloc[selected_idx].to_dict()

        # Visual pipeline progression bar
        status_steps = ["SCHEDULED", "IN_COLLECTION", "IN_TRANSIT", "COMPLETED"]
        curr_status = selected_job["status"]

        c_info1, c_info2, c_info3, c_info4 = st.columns(4)
        with c_info1:
            st.markdown(f"**Job ID:** `{selected_job['id']}`")
            st.markdown(f"**Request:** `{selected_job['request_id']}`")
        with c_info2:
            st.markdown(f"**Farmer:** {selected_job['farmer_name']} ({selected_job['village']})")
            st.markdown(f"**Tonnage:** {selected_job['estimated_tonnage']}t {selected_job['crop_residue_type']}")
        with c_info3:
            st.markdown(f"**Fleet:** {selected_job['provider_name']}")
            st.markdown(f"**Off-Taker:** {selected_job['buyer_name']}")
        with c_info4:
            st.markdown(f"**Scheduled Date:** {selected_job['scheduled_date']}")
            st.markdown(f"**Est. Distance:** {selected_job['estimated_distance_km']} km")

        st.markdown("<hr style='margin:14px 0; border:0; border-top:1px solid #DCE4DC;'>", unsafe_allow_html=True)
        
        if curr_status in status_steps:
            step_idx = status_steps.index(curr_status)
            pct = (step_idx + 1) / len(status_steps)
            st.markdown(f"**Current Pipeline Stage:** `{curr_status}`")
            st.progress(pct)
        elif curr_status == "CANCELLED":
            st.error("⚠️ This job was CANCELLED. Associated farm request has been returned to UNASSIGNED.")

        # Status update controls
        valid_transitions = {
            "SCHEDULED": ["IN_COLLECTION", "CANCELLED"],
            "IN_COLLECTION": ["IN_TRANSIT", "CANCELLED"],
            "IN_TRANSIT": ["COMPLETED", "CANCELLED"],
            "COMPLETED": [],
            "CANCELLED": []
        }

        allowed_next = valid_transitions.get(curr_status, [])

        if allowed_next:
            col_act1, col_act2 = st.columns([1.1, 1.9])
            with col_act1:
                next_state = st.selectbox("Advance To Stage", allowed_next)
                status_note = st.text_input("Operational Note", placeholder="e.g. Weighbridge gross verified at 28.2t")
                if st.button("Apply Status Transition"):
                    ok, msg = update_job_status(selected_job["id"], next_state, status_note)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col_act2:
                st.markdown(f"""
                <div style="background:#F7F8F4; padding:14px; border-radius:6px; font-size:0.85rem; border:1px solid {BORDER_LIGHT}; color:{TEXT_MAIN}; line-height:1.5;">
                    <strong>Lifecycle Rules Enforced:</strong><br/>
                    • <code>SCHEDULED</code>: Machinery assigned, date locked.<br/>
                    • <code>IN_COLLECTION</code>: Balers actively collecting straw in farmer's field.<br/>
                    • <code>IN_TRANSIT</code>: Trolleys en-route to buyer depot.<br/>
                    • <code>COMPLETED</code>: Delivered, weighed at plant intake gate, and verified.<br/>
                    • <code>CANCELLED</code>: Re-opens farm request and releases buyer quota automatically.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"Job is in terminal state '{curr_status}'. No further transitions permitted.")

        if selected_job["notes"]:
            st.caption(f"**Log History:** {selected_job['notes']}")

    # 2. Comprehensive Jobs Table
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("📋 All Coordinated Supply Jobs")

        disp_cols = [
            "id", "farmer_name", "village", "estimated_tonnage",
            "provider_name", "buyer_name", "scheduled_date", "estimated_distance_km",
            "estimated_service_cost_inr", "status", "updated_at"
        ]
        renamed = {
            "id": "Job ID",
            "farmer_name": "Farmer",
            "village": "Village",
            "estimated_tonnage": "Tonnes",
            "provider_name": "Machinery Hub",
            "buyer_name": "Energy Off-Taker",
            "scheduled_date": "Date",
            "estimated_distance_km": "Distance (km)",
            "estimated_service_cost_inr": "Est Cost (₹)",
            "status": "Status",
            "updated_at": "Last Updated"
        }

        st.dataframe(jobs_df[disp_cols].rename(columns=renamed), use_container_width=True, hide_index=True)
