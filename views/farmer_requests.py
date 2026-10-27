"""
Farmer Requests View for Parali-to-Power.
Allows creating new crop-residue management requests with validation,
rich submission feedback, and filtering/inspecting registered farmer requests.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from core.db import get_db_connection, log_action
from styles import get_status_badge_html

# Known cluster reference locations for demo drop-down
CLUSTER_OPTIONS = {
    "Sangrur - Dhuri Village": (30.3683, 75.8672, "Sangrur"),
    "Sangrur - Sunam Village": (30.1311, 75.8037, "Sangrur"),
    "Sangrur - Bhadaur Village": (30.4800, 75.3200, "Sangrur"),
    "Patiala - Nabha Village": (30.3752, 76.1517, "Patiala"),
    "Patiala - Samana Village": (30.0152, 76.1918, "Patiala"),
    "Ludhiana - Samrala Village": (30.8354, 76.1914, "Ludhiana"),
    "Ludhiana - Khanna Village": (30.7027, 76.2173, "Ludhiana"),
    "Karnal - Gharaunda Village": (29.5392, 76.9718, "Karnal"),
    "Kaithal - Kalayat Village": (29.8415, 76.3727, "Kaithal"),
    "Remote Border Outlier (Infeasible Test)": (31.4500, 75.2000, "Remote Border"),
}


def render_farmer_requests():
    st.markdown('<div class="sim-banner">Simulated Demo Data — Farmer Portal</div>', unsafe_allow_html=True)
    st.title("🚜 Farmer Residue Management Requests")
    st.caption("Register crop residue collection demands to coordinate custom hiring machinery before wheat sowing deadlines.")

    # Storage for submission feedback in session state
    if "last_submission" not in st.session_state:
        st.session_state.last_submission = None

    # Expandable Submission Form (border=False on form to prevent double-bordered box)
    with st.expander("➕ Register New Crop-Residue Request", expanded=True):
        with st.form("new_request_form", clear_on_submit=False, border=False):
            st.markdown("##### 🌾 Farmer & Field Specifications")
            c1, c2 = st.columns(2)
            with c1:
                farmer_name = st.text_input("Farmer Full Name", value="Harjinder Singh", placeholder="e.g. Harjinder Singh")
                phone = st.text_input("Contact Mobile", value="+91 94170 88210")
                selected_loc_name = st.selectbox("Location / Village Cluster", list(CLUSTER_OPTIONS.keys()))
                residue_type = st.selectbox("Crop Residue Variety", [
                    "Paddy Straw (Baled)",
                    "Basmati Straw",
                    "Pusa 44 Straw",
                    "PR-126 Short-Duration Straw"
                ])

            with c2:
                acres = st.number_input("Field Area (Acres)", min_value=1.0, max_value=200.0, value=15.0, step=1.0)
                # Auto estimate: ~2.2 tonnes/acre for paddy residue in Punjab
                default_tonnage = round(acres * 2.2, 1)
                est_tonnage = st.number_input("Estimated Residue Volume (Tonnes)", min_value=1.0, max_value=500.0, value=default_tonnage, step=0.5)

                today = date(2026, 10, 27)
                harvest_date = st.date_input("Combine Harvest Date", value=today + timedelta(days=1))
                sowing_deadline = st.date_input("Target Wheat Sowing Deadline", value=today + timedelta(days=6))
                preferred_slot = st.selectbox("Preferred In-Field Machinery Window", [
                    "Morning (08:00 - 12:00)",
                    "Afternoon (12:00 - 16:00)",
                    "Flexible"
                ])

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Submit Request for Processing")

            if submitted:
                if sowing_deadline <= harvest_date:
                    st.error("Validation Error: Wheat sowing deadline must be strictly after the harvest date.")
                    st.session_state.last_submission = None
                elif not farmer_name.strip():
                    st.error("Validation Error: Farmer name cannot be blank.")
                    st.session_state.last_submission = None
                elif est_tonnage <= 0:
                    st.error("Validation Error: Estimated biomass volume must be greater than 0.")
                    st.session_state.last_submission = None
                else:
                    try:
                        lat, lon, district = CLUSTER_OPTIONS[selected_loc_name]
                        village = selected_loc_name.split(" - ")[-1]

                        req_id = f"REQ-{datetime.now().strftime('%m%d%H%M%S')}"
                        far_id = f"FAR-{datetime.now().strftime('%m%d%H%M')}"
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO farmers (id, name, phone, village, district, latitude, longitude)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (far_id, farmer_name, phone, village, district, lat, lon))

                        cursor.execute("""
                            INSERT INTO requests (id, farmer_id, farmer_name, village, district, latitude, longitude,
                                                  crop_residue_type, field_area_acres, estimated_tonnage,
                                                  harvest_date, sowing_deadline, preferred_pickup_window, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNASSIGNED', ?)
                        """, (req_id, far_id, farmer_name, village, district, lat, lon,
                              residue_type, acres, est_tonnage,
                              harvest_date.strftime("%Y-%m-%d"),
                              sowing_deadline.strftime("%Y-%m-%d"),
                              preferred_slot, now_str))

                        conn.commit()
                        conn.close()

                        log_action("NEW_REQUEST", f"Created request {req_id} for {farmer_name} ({est_tonnage}t)")

                        # Save submission confirmation details in session state
                        st.session_state.last_submission = {
                            "id": req_id,
                            "farmer": farmer_name,
                            "village": village,
                            "district": district,
                            "tonnage": est_tonnage,
                            "residue": residue_type,
                            "deadline": sowing_deadline.strftime("%Y-%m-%d"),
                            "status": "UNASSIGNED"
                        }
                    except Exception as e:
                        st.error(f"Database error during request registration: {str(e)}")
                        st.session_state.last_submission = None

    # Rich Submission Feedback Banner (Requirement 4)
    if st.session_state.last_submission:
        sub = st.session_state.last_submission
        with st.container(border=True):
            st.markdown(f"""
            <div style="background-color: #E3F2E6; border: 1px solid #B4DCBE; border-radius: 8px; padding: 16px 20px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="font-size: 1.15rem; font-weight: 700; color: #166534;">
                        ✅ Request Registered Successfully: <code>{sub['id']}</code>
                    </div>
                    <div>
                        <span class="badge badge-unassigned">STATUS: {sub['status']}</span>
                    </div>
                </div>
                <div style="margin-top: 8px; font-size: 0.90rem; color: #1F2933; line-height: 1.6;">
                    <strong>Farmer:</strong> {sub['farmer']} &nbsp;|&nbsp; 
                    <strong>Location:</strong> {sub['village']}, {sub['district']} &nbsp;|&nbsp; 
                    <strong>Volume:</strong> {sub['tonnage']} tonnes ({sub['residue']}) &nbsp;|&nbsp; 
                    <strong>Deadline:</strong> {sub['deadline']}
                </div>
                <div style="margin-top: 10px; padding: 8px 12px; background-color: #FFFFFF; border: 1px solid #B4DCBE; border-radius: 6px; font-size: 0.88rem; color: #166534; font-weight: 600;">
                    👉 <strong>Next Step:</strong> Open <strong>Providers & Scheduling</strong> from the left sidebar to evaluate nearby custom hiring fleets and assign this request.
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Filter and Table View
    with st.container(border=True):
        st.subheader("📋 Registered Requests Roster")
        st.caption("All crop residue collection demands logged across Punjab & Haryana clusters.")

        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM requests ORDER BY created_at DESC", conn)
        conn.close()

        if df.empty:
            st.info("No requests currently registered in the database.")
            return

        # Filter controls
        f1, f2 = st.columns(2)
        with f1:
            all_statuses = df["status"].unique().tolist()
            status_filter = st.multiselect("Filter by Status", options=all_statuses, default=all_statuses)
        with f2:
            all_districts = df["district"].unique().tolist()
            district_filter = st.multiselect("Filter by District", options=all_districts, default=all_districts)

        filtered_df = df[
            (df["status"].isin(status_filter)) &
            (df["district"].isin(district_filter))
        ]

        st.markdown(f"<p style='color: #52615A; font-size: 0.88rem;'>Showing <strong>{len(filtered_df)}</strong> of <strong>{len(df)}</strong> recorded requests</p>", unsafe_allow_html=True)

        # Display clean table
        display_cols = [
            "id", "farmer_name", "village", "district", "crop_residue_type",
            "field_area_acres", "estimated_tonnage", "harvest_date", "sowing_deadline", "status"
        ]
        renamed_cols = {
            "id": "Request ID",
            "farmer_name": "Farmer",
            "village": "Village",
            "district": "District",
            "crop_residue_type": "Residue Type",
            "field_area_acres": "Area (Acres)",
            "estimated_tonnage": "Est. Tonnes",
            "harvest_date": "Harvest Date",
            "sowing_deadline": "Sowing Deadline",
            "status": "Current Status"
        }

        st.dataframe(
            filtered_df[display_cols].rename(columns=renamed_cols),
            use_container_width=True,
            hide_index=True
        )
