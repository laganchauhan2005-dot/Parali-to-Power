"""
Biomass Buyers & Deliveries View for Parali-to-Power.
Displays off-taker facilities (Bio-CNG, Power Co-Firing, Pelletization),
their active daily quotas, and scheduled delivery tracking.
"""
import streamlit as st
import pandas as pd
from core.db import get_db_connection, log_action
from styles import get_status_badge_html, TEXT_MAIN, TEXT_SECONDARY, BORDER_LIGHT, PRIMARY_FOREST


def render_buyers():
    st.markdown('<div class="sim-banner">Simulated Demo Data — Industrial Off-Takers</div>', unsafe_allow_html=True)
    st.title("🏭 Biomass Buyers & Energy Off-Take Depots")
    st.caption("Manage thermal power plants, compressed bio-gas (CBG) refineries, and pellet manufacturing facilities.")

    conn = get_db_connection()
    buyers_df = pd.read_sql_query("SELECT * FROM buyers", conn)
    jobs_df = pd.read_sql_query("""
        SELECT j.*, r.farmer_name, r.village, r.crop_residue_type, r.estimated_tonnage, p.name as provider_name
        FROM jobs j
        JOIN requests r ON j.request_id = r.id
        JOIN providers p ON j.provider_id = p.id
    """, conn)
    conn.close()

    # 1. Facility Cards with Live Intake Quotas
    st.subheader("🏢 Active Off-Take Plants & Capacity Status")
    
    cols = st.columns(2)
    for i, (_, buyer) in enumerate(buyers_df.iterrows()):
        col = cols[i % 2]
        with col:
            with st.container(border=True):
                cap = float(buyer["daily_intake_capacity_tonnes"])
                booked = float(buyer["current_booked_intake_tonnes"])
                util_pct = min(100.0, round((booked / max(1.0, cap)) * 100, 1))

                status_color = "#2D6A4F" if buyer["status"] == "ACCEPTING" else "#BC4749"

                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                    <div style="font-size:1.1rem; font-weight:700; color:{PRIMARY_FOREST};">{buyer['name']}</div>
                    <span style="background:{status_color}22; color:{status_color}; font-size:0.78rem; font-weight:700; padding:2px 8px; border-radius:4px; border:1px solid {status_color}55;">
                        {buyer['status']}
                    </span>
                </div>
                <div style="margin-bottom:10px; font-size:0.85rem; color:{TEXT_SECONDARY};">
                    <strong>Type:</strong> {buyer['facility_type']} &nbsp;|&nbsp; 
                    <strong>District:</strong> {buyer['district']} ({buyer['location']})
                </div>
                <div style="font-size:0.88rem; margin-bottom:6px; color:{TEXT_MAIN};">
                    <strong>Daily Quota Utilized:</strong> {booked:.1f}t / {cap:.1f}t (<strong>{util_pct}%</strong>)
                </div>
                """, unsafe_allow_html=True)

                st.progress(util_pct / 100.0)

                st.markdown(f"""
                <div style="font-size:0.85rem; color:{TEXT_SECONDARY}; margin-top:10px; margin-bottom:12px; line-height:1.5;">
                    🌾 <strong>Accepted Residue:</strong> {buyer['accepted_residue_types']}<br/>
                    💵 <strong>Purchase Price:</strong> ₹{buyer['purchase_price_per_tonne']:,.2f} / tonne
                </div>
                """, unsafe_allow_html=True)

                # Interactive status toggle
                new_status = st.selectbox(
                    f"Update Operational Status for {buyer['id']}",
                    options=["ACCEPTING", "QUOTA_FULL", "MAINTENANCE"],
                    index=["ACCEPTING", "QUOTA_FULL", "MAINTENANCE"].index(buyer["status"]),
                    key=f"status_toggle_{buyer['id']}"
                )

                if new_status != buyer["status"]:
                    c_update = get_db_connection()
                    cur = c_update.cursor()
                    cur.execute("UPDATE buyers SET status = ? WHERE id = ?", (new_status, buyer["id"]))
                    c_update.commit()
                    c_update.close()
                    log_action("BUYER_STATUS_UPDATE", f"Updated {buyer['id']} status to {new_status}")
                    st.success(f"Status updated to {new_status}")
                    st.rerun()

    # 2. Incoming Deliveries Table
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("🚚 Scheduled Biomass Shipments by Facility")
        st.caption("All confirmed collection jobs en-route or delivered to processing depots.")

        if jobs_df.empty:
            st.info("No active or scheduled delivery jobs recorded yet.")
        else:
            disp_jobs = jobs_df[[
                "id", "buyer_id", "provider_name", "farmer_name", "village",
                "crop_residue_type", "estimated_tonnage", "scheduled_date", "status"
            ]].rename(columns={
                "id": "Job ID",
                "buyer_id": "Buyer ID",
                "provider_name": "Machinery Fleet",
                "farmer_name": "Farmer Source",
                "village": "Village",
                "crop_residue_type": "Residue",
                "estimated_tonnage": "Volume (t)",
                "scheduled_date": "Scheduled Date",
                "status": "Job Status"
            })
            st.dataframe(disp_jobs, use_container_width=True, hide_index=True)
