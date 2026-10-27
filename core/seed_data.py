"""
Synthetic demonstration dataset for Parali-to-Power (TPPC-2026).
All records are strictly fictional and intended for research/demonstration purposes.
"""
from core.db import get_db_connection, log_action

# Synthetic Punjab & Haryana coordinate anchors (approximate lat/long for demonstration)
LOCATIONS = {
    "Sangrur_Hub": (30.2458, 75.8421),
    "Dhuri_Village": (30.3683, 75.8672),
    "Sunam_Village": (30.1311, 75.8037),
    "Ludhiana_Hub": (30.9010, 75.8573),
    "Samrala_Village": (30.8354, 76.1914),
    "Khanna_Village": (30.7027, 76.2173),
    "Patiala_Hub": (30.3398, 76.3869),
    "Nabha_Village": (30.3752, 76.1517),
    "Samana_Village": (30.0152, 76.1918),
    "Karnal_Hub": (29.6857, 76.9905),
    "Gharaunda_Village": (29.5392, 76.9718),
    "Kaithal_Hub": (29.8015, 76.4027),
    "Far_Remote_Village": (31.4500, 75.2000),  # Remote location specifically to demonstrate rejection
}


def seed_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Seed Providers (Custom Hiring Centers & Aggregators)
    providers = [
        (
            "PRV-001",
            "Kisan Vikas Agro Mech CHC",
            "Harpreet Singh",
            "+91 98721 00101",
            "Dhuri",
            "Sangrur",
            LOCATIONS["Sangrur_Hub"][0],
            LOCATIONS["Sangrur_Hub"][1],
            "Super Baler, Rake, Heavy Trolley",
            60.0,  # tonnes per day capacity
            35.0,  # max service radius km
            450.0, # base service cost per tonne
            "ACTIVE"
        ),
        (
            "PRV-002",
            "Malwa Bio-Harvest Solutions",
            "Jaspal Brar",
            "+91 98721 00102",
            "Nabha Bypass",
            "Patiala",
            LOCATIONS["Patiala_Hub"][0],
            LOCATIONS["Patiala_Hub"][1],
            "Super Baler, Rake, Trolley",
            45.0,
            40.0,
            480.0,
            "ACTIVE"
        ),
        (
            "PRV-003",
            "Satluj Green Farm Machinery Hub",
            "Gurvinder Sidhu",
            "+91 98721 00103",
            "Samrala Road",
            "Ludhiana",
            LOCATIONS["Ludhiana_Hub"][0],
            LOCATIONS["Ludhiana_Hub"][1],
            "Super Baler, Rake, Heavy Trolley",
            75.0,
            45.0,
            420.0,
            "ACTIVE"
        ),
        (
            "PRV-004",
            "Haryana Agro Machinery Cooperative",
            "Rameshwar Sharma",
            "+91 98721 00104",
            "Nilokheri",
            "Karnal",
            LOCATIONS["Karnal_Hub"][0],
            LOCATIONS["Karnal_Hub"][1],
            "Round Baler, Trolley",
            30.0,
            30.0,
            500.0,
            "ACTIVE"
        ),
        (
            "PRV-005",
            "Kaithal Bio-Residue Fleet (Maintenance)",
            "Kuldeep Malik",
            "+91 98721 00105",
            "Cheeka",
            "Kaithal",
            LOCATIONS["Kaithal_Hub"][0],
            LOCATIONS["Kaithal_Hub"][1],
            "Super Baler, Heavy Trolley",
            50.0,
            35.0,
            460.0,
            "MAINTENANCE"  # Under maintenance to demonstrate unavailability filter
        ),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO providers 
        (id, name, contact_person, phone, hub_location, district, latitude, longitude, equipment_types, daily_capacity_tonnes, max_service_radius_km, base_rate_per_tonne, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, providers)

    # 2. Seed Biomass Energy Buyers
    buyers = [
        (
            "BYR-001",
            "Sangrur Compressed Bio-Gas (CBG) Facility",
            "Bio-CNG Plant",
            "Bhaddalwad",
            "Sangrur",
            30.2100,
            75.8200,
            "Paddy Straw (Baled), Basmati Straw",
            120.0,  # daily capacity
            35.0,   # currently booked
            1650.0, # purchase price / tonne
            "ACCEPTING"
        ),
        (
            "BYR-002",
            "Patiala Thermal Co-Firing Depot",
            "Biomass Power Co-Firing",
            "Nabha",
            "Patiala",
            30.3500,
            76.1800,
            "Paddy Straw (Baled)",
            200.0,
            80.0,
            1550.0,
            "ACCEPTING"
        ),
        (
            "BYR-003",
            "Ludhiana Bio-Coal & Pelletization Plant",
            "Pelletization Plant",
            "Sahnewal",
            "Ludhiana",
            30.8200,
            75.9800,
            "Paddy Straw (Baled), Pusa Straw",
            90.0,
            45.0,
            1700.0,
            "ACCEPTING"
        ),
        (
            "BYR-004",
            "Karnal 2G Bio-Ethanol Pilot Refinery",
            "2G Bioethanol",
            "Indri",
            "Karnal",
            29.8800,
            77.0500,
            "Paddy Straw (Baled), Basmati Straw",
            80.0,
            80.0,  # QUOTA FULL scenario
            1600.0,
            "QUOTA_FULL"
        ),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO buyers
        (id, name, facility_type, location, district, latitude, longitude, accepted_residue_types, daily_intake_capacity_tonnes, current_booked_intake_tonnes, purchase_price_per_tonne, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, buyers)

    # 3. Seed Farmers & Requests
    farmers = [
        ("FAR-001", "Balwinder Singh", "+91 94170 12001", "Dhuri", "Sangrur", LOCATIONS["Dhuri_Village"][0], LOCATIONS["Dhuri_Village"][1]),
        ("FAR-002", "Jagtar Singh", "+91 94170 12002", "Sunam", "Sangrur", LOCATIONS["Sunam_Village"][0], LOCATIONS["Sunam_Village"][1]),
        ("FAR-003", "Sukhdev Singh", "+91 94170 12003", "Nabha", "Patiala", LOCATIONS["Nabha_Village"][0], LOCATIONS["Nabha_Village"][1]),
        ("FAR-004", "Manpreet Kaur", "+91 94170 12004", "Samana", "Patiala", LOCATIONS["Samana_Village"][0], LOCATIONS["Samana_Village"][1]),
        ("FAR-005", "Amandeep Singh", "+91 94170 12005", "Samrala", "Ludhiana", LOCATIONS["Samrala_Village"][0], LOCATIONS["Samrala_Village"][1]),
        ("FAR-006", "Hardeep Gill", "+91 94170 12006", "Khanna", "Ludhiana", LOCATIONS["Khanna_Village"][0], LOCATIONS["Khanna_Village"][1]),
        ("FAR-007", "Rajendra Virk", "+91 94170 12007", "Gharaunda", "Karnal", LOCATIONS["Gharaunda_Village"][0], LOCATIONS["Gharaunda_Village"][1]),
        ("FAR-008", "Satnam Singh", "+91 94170 12008", "Kalayat", "Kaithal", LOCATIONS["Kaithal_Hub"][0] + 0.04, LOCATIONS["Kaithal_Hub"][1] - 0.03),
        ("FAR-009", "Pritam Singh", "+91 94170 12009", "Dharangwala", "Remote Border", LOCATIONS["Far_Remote_Village"][0], LOCATIONS["Far_Remote_Village"][1]),
        ("FAR-010", "Charanjit Singh", "+91 94170 12010", "Bhadaur", "Sangrur", 30.4800, 75.3200),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO farmers
        (id, name, phone, village, district, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, farmers)

    # 4. Seed Requests (Diverse states: Unassigned, Scheduled, In Progress, Completed, Infeasible)
    requests = [
        (
            "REQ-101", "FAR-001", "Balwinder Singh", "Dhuri", "Sangrur",
            LOCATIONS["Dhuri_Village"][0], LOCATIONS["Dhuri_Village"][1],
            "Paddy Straw (Baled)", 12.0, 26.5, "2026-10-28", "2026-11-02", "Morning (08:00 - 12:00)",
            "SCHEDULED", "2026-10-26 09:30:00"
        ),
        (
            "REQ-102", "FAR-002", "Jagtar Singh", "Sunam", "Sangrur",
            LOCATIONS["Sunam_Village"][0], LOCATIONS["Sunam_Village"][1],
            "Paddy Straw (Baled)", 18.0, 38.0, "2026-10-29", "2026-11-03", "Afternoon (12:00 - 16:00)",
            "UNASSIGNED", "2026-10-27 08:15:00"
        ),
        (
            "REQ-103", "FAR-003", "Sukhdev Singh", "Nabha", "Patiala",
            LOCATIONS["Nabha_Village"][0], LOCATIONS["Nabha_Village"][1],
            "Basmati Straw", 10.0, 20.0, "2026-10-27", "2026-10-31", "Flexible",
            "IN_COLLECTION", "2026-10-25 11:00:00"
        ),
        (
            "REQ-104", "FAR-004", "Manpreet Kaur", "Samana", "Patiala",
            LOCATIONS["Samana_Village"][0], LOCATIONS["Samana_Village"][1],
            "Paddy Straw (Baled)", 15.0, 32.0, "2026-10-30", "2026-11-04", "Morning (08:00 - 12:00)",
            "UNASSIGNED", "2026-10-27 10:00:00"
        ),
        (
            "REQ-105", "FAR-005", "Amandeep Singh", "Samrala", "Ludhiana",
            LOCATIONS["Samrala_Village"][0], LOCATIONS["Samrala_Village"][1],
            "Paddy Straw (Baled)", 22.0, 48.0, "2026-10-28", "2026-11-01", "Morning (08:00 - 12:00)",
            "UNASSIGNED", "2026-10-27 11:30:00"
        ),
        (
            "REQ-106", "FAR-006", "Hardeep Gill", "Khanna", "Ludhiana",
            LOCATIONS["Khanna_Village"][0], LOCATIONS["Khanna_Village"][1],
            "Paddy Straw (Baled)", 14.0, 30.0, "2026-10-25", "2026-10-29", "Flexible",
            "COMPLETED", "2026-10-24 08:00:00"
        ),
        (
            "REQ-107", "FAR-007", "Rajendra Virk", "Gharaunda", "Karnal",
            LOCATIONS["Gharaunda_Village"][0], LOCATIONS["Gharaunda_Village"][1],
            "Basmati Straw", 8.0, 16.0, "2026-10-31", "2026-11-05", "Afternoon (12:00 - 16:00)",
            "UNASSIGNED", "2026-10-27 12:45:00"
        ),
        (
            "REQ-108", "FAR-008", "Satnam Singh", "Kalayat", "Kaithal",
            LOCATIONS["Kaithal_Hub"][0] + 0.04, LOCATIONS["Kaithal_Hub"][1] - 0.03,
            "Paddy Straw (Baled)", 25.0, 52.0, "2026-10-29", "2026-11-02", "Morning (08:00 - 12:00)",
            "UNASSIGNED", "2026-10-27 13:10:00"
        ),
        (
            "REQ-109", "FAR-009", "Pritam Singh", "Dharangwala", "Remote Border",
            LOCATIONS["Far_Remote_Village"][0], LOCATIONS["Far_Remote_Village"][1],
            "Paddy Straw (Baled)", 30.0, 65.0, "2026-10-28", "2026-10-29", "Morning (08:00 - 12:00)",
            "UNASSIGNED", "2026-10-27 14:00:00"  # Infeasible demo candidate (too far, very tight deadline)
        ),
        (
            "REQ-110", "FAR-010", "Charanjit Singh", "Bhadaur", "Sangrur",
            30.4800, 75.3200,
            "Paddy Straw (Baled)", 16.0, 34.0, "2026-10-30", "2026-11-04", "Flexible",
            "UNASSIGNED", "2026-10-27 15:20:00"
        ),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO requests
        (id, farmer_id, farmer_name, village, district, latitude, longitude, crop_residue_type, field_area_acres, estimated_tonnage, harvest_date, sowing_deadline, preferred_pickup_window, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, requests)

    # 5. Seed Existing Jobs (Corresponding to scheduled/in-progress/completed requests)
    jobs = [
        (
            "JOB-501", "REQ-101", "PRV-001", "BYR-001",
            "2026-10-29", 14.8, 11925.0, "SCHEDULED",
            "Confirmed with Kisan Vikas CHC. Scheduled for 29 Oct morning.",
            "2026-10-26 14:00:00", "2026-10-26 14:00:00"
        ),
        (
            "JOB-502", "REQ-103", "PRV-002", "BYR-002",
            "2026-10-27", 18.2, 9600.0, "IN_COLLECTION",
            "Super Baler deployed in field. Moisture level confirmed at 14%.",
            "2026-10-26 10:30:00", "2026-10-27 09:15:00"
        ),
        (
            "JOB-503", "REQ-106", "PRV-003", "BYR-003",
            "2026-10-26", 24.5, 12600.0, "COMPLETED",
            "Successfully baled and delivered 30 tonnes to Sahnewal pellet plant.",
            "2026-10-24 16:00:00", "2026-10-26 17:30:00"
        ),
    ]

    cursor.executemany("""
        INSERT OR REPLACE INTO jobs
        (id, request_id, provider_id, buyer_id, scheduled_date, estimated_distance_km, estimated_service_cost_inr, status, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, jobs)

    conn.commit()
    conn.close()

    log_action("SYSTEM_INIT", "Database seeded with demonstration records for TPPC-2026.")
