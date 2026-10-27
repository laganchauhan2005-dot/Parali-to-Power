"""
Unit tests for the Parali-to-Power Scheduling and Feasibility Engine.
Tested independently of the Streamlit user interface.
"""
import pytest
import sqlite3
import os
from datetime import datetime, date
from core.db import init_db, reset_database, get_db_connection
from core.scheduler import (
    calculate_haversine_distance,
    check_provider_feasibility,
    check_buyer_feasibility,
    evaluate_candidates_for_request,
    assign_and_schedule_job,
    update_job_status
)


@pytest.fixture(autouse=True)
def setup_fresh_test_db():
    """Ensure a clean, seeded database before each test."""
    reset_database()
    yield


def test_haversine_distance_computation():
    """Verify distance calculation between known coordinates."""
    # Sangrur Hub (30.2458, 75.8421) to Dhuri Village (30.3683, 75.8672) is approx 14-17 km road
    dist = calculate_haversine_distance(30.2458, 75.8421, 30.3683, 75.8672)
    assert 12.0 <= dist <= 20.0
    # Zero distance to self
    assert calculate_haversine_distance(30.0, 75.0, 30.0, 75.0) == 0.0


def test_provider_feasibility_success():
    """A suitable provider within range with capacity passes all checks."""
    provider = {
        "id": "PRV-TEST-1",
        "name": "Test Machinery CHC",
        "equipment_types": "Super Baler, Rake, Trolley",
        "daily_capacity_tonnes": 50.0,
        "max_service_radius_km": 40.0,
        "latitude": 30.25,
        "longitude": 75.85,
        "status": "ACTIVE"
    }
    request = {
        "id": "REQ-TEST-1",
        "latitude": 30.30,
        "longitude": 75.88,
        "estimated_tonnage": 20.0,
        "harvest_date": "2026-10-28",
        "sowing_deadline": "2026-11-03",
        "crop_residue_type": "Paddy Straw (Baled)"
    }
    ok, reasons = check_provider_feasibility(provider, request, "2026-10-29", booked_capacity_today=0.0)
    assert ok is True
    assert len(reasons) == 0


def test_provider_feasibility_radius_rejection():
    """A provider located farther than its service radius is rejected."""
    provider = {
        "id": "PRV-TEST-2",
        "name": "Local CHC",
        "equipment_types": "Super Baler, Rake",
        "daily_capacity_tonnes": 50.0,
        "max_service_radius_km": 20.0, # Low radius
        "latitude": 29.50, # Far away
        "longitude": 76.80,
        "status": "ACTIVE"
    }
    request = {
        "id": "REQ-TEST-2",
        "latitude": 30.30,
        "longitude": 75.88,
        "estimated_tonnage": 20.0,
        "harvest_date": "2026-10-28",
        "sowing_deadline": "2026-11-03"
    }
    ok, reasons = check_provider_feasibility(provider, request, "2026-10-29", booked_capacity_today=0.0)
    assert ok is False
    assert any("exceeds maximum service radius" in r for r in reasons)


def test_provider_feasibility_equipment_rejection():
    """A provider without a baler cannot accept field collection."""
    provider = {
        "id": "PRV-TEST-3",
        "name": "Tractor Only Hub",
        "equipment_types": "Standard Trolley, Cultivator", # No baler
        "daily_capacity_tonnes": 50.0,
        "max_service_radius_km": 50.0,
        "latitude": 30.30,
        "longitude": 75.88,
        "status": "ACTIVE"
    }
    request = {
        "id": "REQ-TEST-3",
        "latitude": 30.30,
        "longitude": 75.88,
        "estimated_tonnage": 20.0,
        "harvest_date": "2026-10-28",
        "sowing_deadline": "2026-11-03"
    }
    ok, reasons = check_provider_feasibility(provider, request, "2026-10-29", booked_capacity_today=0.0)
    assert ok is False
    assert any("baling machinery" in r.lower() for r in reasons)


def test_provider_feasibility_capacity_overflow():
    """A request that exceeds remaining daily capacity is rejected."""
    provider = {
        "id": "PRV-TEST-4",
        "name": "Small Baler Unit",
        "equipment_types": "Super Baler",
        "daily_capacity_tonnes": 30.0,
        "max_service_radius_km": 50.0,
        "latitude": 30.30,
        "longitude": 75.88,
        "status": "ACTIVE"
    }
    request = {
        "id": "REQ-TEST-4",
        "latitude": 30.30,
        "longitude": 75.88,
        "estimated_tonnage": 35.0, # Exceeds 30t
        "harvest_date": "2026-10-28",
        "sowing_deadline": "2026-11-03"
    }
    ok, reasons = check_provider_feasibility(provider, request, "2026-10-29", booked_capacity_today=0.0)
    assert ok is False
    assert any("exceeds provider's total daily capacity" in r for r in reasons)


def test_buyer_feasibility_quota_overflow():
    """A buyer with insufficient remaining quota is rejected."""
    buyer = {
        "id": "BYR-TEST-1",
        "name": "Test Bio-CNG Depot",
        "status": "ACCEPTING",
        "accepted_residue_types": "Paddy Straw (Baled)",
        "daily_intake_capacity_tonnes": 50.0,
        "current_booked_intake_tonnes": 45.0, # Only 5.0t left
        "latitude": 30.30,
        "longitude": 75.88
    }
    request = {
        "estimated_tonnage": 20.0, # Needs 20t, only 5t available
        "crop_residue_type": "Paddy Straw (Baled)",
        "latitude": 30.30,
        "longitude": 75.88
    }
    ok, reasons = check_buyer_feasibility(buyer, request)
    assert ok is False
    assert any("Intake quota exceeded" in r for r in reasons)


def test_assign_and_schedule_job_prevents_double_booking():
    """Cannot assign a request that is already scheduled, and verifies capacity safety."""
    # REQ-102 (38t) on 2026-10-30 where PRV-001 (60t capacity) has 0 booked capacity
    ok1, msg1 = assign_and_schedule_job("REQ-102", "PRV-001", "BYR-001", "2026-10-30")
    assert ok1 is True, f"Expected assignment to succeed, got: {msg1}"

    # Attempting to assign the same request again must fail
    ok2, msg2 = assign_and_schedule_job("REQ-102", "PRV-002", "BYR-002", "2026-10-30")
    assert ok2 is False
    assert "already in status 'SCHEDULED'" in msg2


def test_job_status_lifecycle_transitions():
    """Validates sequential lifecycle progression and prevents illegal jumps."""
    conn = get_db_connection()
    cur = conn.cursor()
    # Find existing scheduled job
    cur.execute("SELECT id FROM jobs WHERE status = 'SCHEDULED' LIMIT 1")
    job_id = cur.fetchone()["id"]
    conn.close()

    # Illegal jump: SCHEDULED cannot jump straight to COMPLETED
    bad_ok, bad_msg = update_job_status(job_id, "COMPLETED")
    assert bad_ok is False

    # Valid step: SCHEDULED -> IN_COLLECTION
    ok1, _ = update_job_status(job_id, "IN_COLLECTION", "Balers in field")
    assert ok1 is True

    # Valid step: IN_COLLECTION -> IN_TRANSIT
    ok2, _ = update_job_status(job_id, "IN_TRANSIT", "Trolleys dispatched")
    assert ok2 is True

    # Valid step: IN_TRANSIT -> COMPLETED
    ok3, _ = update_job_status(job_id, "COMPLETED", "Weighed at gate")
    assert ok3 is True


def test_cancellation_releases_buyer_quota_and_resets_request():
    """Cancelling an active job resets the request to UNASSIGNED and restores buyer intake."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT j.id, j.request_id, j.buyer_id, b.current_booked_intake_tonnes FROM jobs j JOIN buyers b ON j.buyer_id = b.id WHERE j.status = 'SCHEDULED' LIMIT 1")
    row = cur.fetchone()
    job_id = row["id"]
    req_id = row["request_id"]
    buyer_id = row["buyer_id"]
    initial_booked = float(row["current_booked_intake_tonnes"])
    conn.close()

    ok, msg = update_job_status(job_id, "CANCELLED", "Weather delay cancel")
    assert ok is True

    # Verify request status reverted to UNASSIGNED
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT status FROM requests WHERE id = ?", (req_id,))
    req_status = cur.fetchone()["status"]
    assert req_status == "UNASSIGNED"

    # Verify buyer booked capacity was restored
    cur.execute("SELECT current_booked_intake_tonnes FROM buyers WHERE id = ?", (buyer_id,))
    updated_booked = float(cur.fetchone()[0])
    assert updated_booked < initial_booked
    conn.close()
