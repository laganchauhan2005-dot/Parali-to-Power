"""
Database schema, connection management, and persistence layer for Parali-to-Power.
All data is stored in SQLite and loaded dynamically.
"""
import sqlite3
import os
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "parali_to_power.db")


def get_db_connection():
    """Create a connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed=True):
    """Initialize database tables and optionally seed demonstration records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Farmers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            village TEXT NOT NULL,
            district TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL
        )
    """)

    # 2. Residue Requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id TEXT PRIMARY KEY,
            farmer_id TEXT NOT NULL,
            farmer_name TEXT NOT NULL,
            village TEXT NOT NULL,
            district TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            crop_residue_type TEXT NOT NULL,
            field_area_acres REAL NOT NULL,
            estimated_tonnage REAL NOT NULL,
            harvest_date TEXT NOT NULL,
            sowing_deadline TEXT NOT NULL,
            preferred_pickup_window TEXT NOT NULL,
            status TEXT NOT NULL, -- 'UNASSIGNED', 'SCHEDULED', 'IN_COLLECTION', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED'
            created_at TEXT NOT NULL,
            FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        )
    """)

    # 3. Service Providers / CHCs (Custom Hiring Centers)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS providers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            phone TEXT NOT NULL,
            hub_location TEXT NOT NULL,
            district TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            equipment_types TEXT NOT NULL, -- comma-separated: 'Super Baler, Rake, Trolley'
            daily_capacity_tonnes REAL NOT NULL,
            max_service_radius_km REAL NOT NULL,
            base_rate_per_tonne REAL NOT NULL,
            status TEXT NOT NULL -- 'ACTIVE', 'MAINTENANCE', 'OFFLINE'
        )
    """)

    # 4. Biomass Energy Buyers (Power / Bio-CNG / Pellet plants)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            facility_type TEXT NOT NULL, -- 'Bio-CNG Plant', 'Biomass Power Co-Firing', 'Pelletization Plant', '2G Bioethanol'
            location TEXT NOT NULL,
            district TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            accepted_residue_types TEXT NOT NULL, -- comma-separated
            daily_intake_capacity_tonnes REAL NOT NULL,
            current_booked_intake_tonnes REAL DEFAULT 0.0,
            purchase_price_per_tonne REAL NOT NULL,
            status TEXT NOT NULL -- 'ACCEPTING', 'QUOTA_FULL', 'MAINTENANCE'
        )
    """)

    # 5. Scheduled Jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            request_id TEXT NOT NULL UNIQUE,
            provider_id TEXT NOT NULL,
            buyer_id TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            estimated_distance_km REAL NOT NULL,
            estimated_service_cost_inr REAL NOT NULL,
            status TEXT NOT NULL, -- 'SCHEDULED', 'IN_COLLECTION', 'IN_TRANSIT', 'COMPLETED', 'CANCELLED'
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (request_id) REFERENCES requests (id),
            FOREIGN KEY (provider_id) REFERENCES providers (id),
            FOREIGN KEY (buyer_id) REFERENCES buyers (id)
        )
    """)

    # 6. Audit & Activity Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        )
    """)

    conn.commit()

    # Check if empty, seed if requested
    cursor.execute("SELECT COUNT(*) FROM requests")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0 and seed:
        from core.seed_data import seed_database
        seed_database()


def reset_database():
    """Wipe all records and reseed clean demonstration state."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS jobs")
    cursor.execute("DROP TABLE IF EXISTS requests")
    cursor.execute("DROP TABLE IF EXISTS providers")
    cursor.execute("DROP TABLE IF EXISTS buyers")
    cursor.execute("DROP TABLE IF EXISTS farmers")
    cursor.execute("DROP TABLE IF EXISTS audit_logs")
    conn.commit()
    conn.close()
    init_db(seed=True)


def log_action(action: str, details: str):
    """Insert an audit log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (timestamp, action, details) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), action, details)
    )
    conn.commit()
    conn.close()
