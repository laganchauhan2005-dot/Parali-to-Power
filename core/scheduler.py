"""
Feasibility & Scheduling Engine for Parali-to-Power.
Implements hard feasibility checks, rejection reasoning, and explainable ranking.
Completely decoupled from Streamlit UI for unit-testing.
"""
import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple, Optional
from core.db import get_db_connection, log_action


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate geographic distance in kilometers using the Haversine formula.
    Multiplied by a 1.25 road winding factor for realistic terrestrial transit estimate.
    """
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    crow_distance = R * c
    # Approximate terrestrial road distance
    return round(crow_distance * 1.25, 1)


def get_provider_booked_capacity(conn, provider_id: str, target_date: str) -> float:
    """Calculate already booked tonnage for a provider on a specific date."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(r.estimated_tonnage), 0.0)
        FROM jobs j
        JOIN requests r ON j.request_id = r.id
        WHERE j.provider_id = ? 
          AND j.scheduled_date = ? 
          AND j.status NOT IN ('CANCELLED', 'COMPLETED')
    """, (provider_id, target_date))
    row = cursor.fetchone()
    return float(row[0]) if row else 0.0


def check_provider_feasibility(
    provider: Dict[str, Any],
    request: Dict[str, Any],
    target_date: str,
    booked_capacity_today: float
) -> Tuple[bool, List[str]]:
    """
    Hard feasibility check for a service provider against a farmer's request.
    Returns (is_feasible, list_of_reasons).
    """
    reasons = []

    # 1. Active status check
    if provider["status"].upper() != "ACTIVE":
        reasons.append(f"Provider status is '{provider['status']}' (not ACTIVE).")

    # 2. Equipment check (must have baling capability)
    equip_str = provider["equipment_types"].lower()
    if "baler" not in equip_str:
        reasons.append("Lacks required residue baling machinery (Super Baler / Round Baler).")

    # 3. Distance & Service Radius Check
    dist_to_farm = calculate_haversine_distance(
        provider["latitude"], provider["longitude"],
        request["latitude"], request["longitude"]
    )
    if dist_to_farm > provider["max_service_radius_km"]:
        reasons.append(
            f"Distance ({dist_to_farm} km) exceeds maximum service radius ({provider['max_service_radius_km']} km)."
        )

    # 4. Daily Capacity Check
    req_tonnage = float(request["estimated_tonnage"])
    daily_cap = float(provider["daily_capacity_tonnes"])
    available_today = daily_cap - booked_capacity_today

    if req_tonnage > daily_cap:
        reasons.append(
            f"Requested volume ({req_tonnage}t) exceeds provider's total daily capacity ({daily_cap}t/day)."
        )
    elif req_tonnage > available_today:
        reasons.append(
            f"Capacity conflict on {target_date}: requested {req_tonnage}t exceeds remaining daily capacity ({round(available_today, 1)}t available of {daily_cap}t)."
        )

    # 5. Deadline Check
    try:
        sched_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
        harvest_dt = datetime.strptime(request["harvest_date"], "%Y-%m-%d").date()
        deadline_dt = datetime.strptime(request["sowing_deadline"], "%Y-%m-%d").date()

        if sched_dt < harvest_dt:
            reasons.append(f"Scheduled date ({target_date}) is before harvest readiness ({request['harvest_date']}).")
        if sched_dt > deadline_dt:
            reasons.append(f"Scheduled date ({target_date}) breaches sowing deadline ({request['sowing_deadline']}).")
    except Exception as e:
        reasons.append(f"Invalid date format: {str(e)}")

    return (len(reasons) == 0, reasons)


def check_buyer_feasibility(
    buyer: Dict[str, Any],
    request: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Hard feasibility check for a biomass buyer / off-taker.
    Returns (is_feasible, list_of_reasons).
    """
    reasons = []

    # 1. Acceptance status
    if buyer["status"].upper() != "ACCEPTING":
        reasons.append(f"Buyer facility is currently '{buyer['status']}'.")

    # 2. Intake capacity
    remaining_quota = float(buyer["daily_intake_capacity_tonnes"]) - float(buyer["current_booked_intake_tonnes"])
    req_tonnage = float(request["estimated_tonnage"])
    if req_tonnage > remaining_quota:
        reasons.append(
            f"Intake quota exceeded: requires {req_tonnage}t, but plant only has {round(remaining_quota, 1)}t remaining."
        )

    # 3. Residue type compatibility (basic matching)
    req_crop = request["crop_residue_type"].lower()
    buyer_accepted = buyer["accepted_residue_types"].lower()
    # Check if either 'paddy' or 'straw' or specific type overlaps
    is_compatible = False
    for token in ["paddy", "straw", "basmati", "pusa"]:
        if token in req_crop and token in buyer_accepted:
            is_compatible = True
            break
    if not is_compatible and "all" not in buyer_accepted:
        reasons.append(f"Residue '{request['crop_residue_type']}' not in accepted types ({buyer['accepted_residue_types']}).")

    # 4. Economic transport distance from farm to buyer (max 80 km limit)
    dist_to_buyer = calculate_haversine_distance(
        request["latitude"], request["longitude"],
        buyer["latitude"], buyer["longitude"]
    )
    if dist_to_buyer > 80.0:
        reasons.append(f"Transport distance to buyer ({dist_to_buyer} km) exceeds economical radius (80 km).")

    return (len(reasons) == 0, reasons)


def evaluate_candidates_for_request(
    request_id: str,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the intelligent scheduling engine on a specific request.
    Returns:
    {
        'request': dict,
        'target_date': str,
        'feasible_matches': [ ... ranked by score ... ],
        'rejections': [ { 'type': 'Provider'|'Buyer', 'name': ..., 'reasons': [...] } ]
    }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
    req_row = cursor.fetchone()
    if not req_row:
        conn.close()
        return {"error": f"Request {request_id} not found."}

    request = dict(req_row)

    # Default target date to harvest date if not specified
    if not target_date:
        target_date = request["harvest_date"]

    cursor.execute("SELECT * FROM providers")
    providers = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM buyers")
    buyers = [dict(r) for r in cursor.fetchall()]

    feasible_matches = []
    rejections = []

    # 1. Filter Providers
    feasible_providers = []
    for prov in providers:
        booked_cap = get_provider_booked_capacity(conn, prov["id"], target_date)
        is_ok, reasons = check_provider_feasibility(prov, request, target_date, booked_cap)
        if is_ok:
            feasible_providers.append((prov, booked_cap))
        else:
            rejections.append({
                "type": "Provider",
                "name": f"{prov['name']} ({prov['district']})",
                "reasons": reasons
            })

    # 2. Filter Buyers
    feasible_buyers = []
    for b in buyers:
        is_ok, reasons = check_buyer_feasibility(b, request)
        if is_ok:
            feasible_buyers.append(b)
        else:
            rejections.append({
                "type": "Buyer",
                "name": f"{b['name']} ({b['facility_type']})",
                "reasons": reasons
            })

    conn.close()

    # 3. Combine feasible Provider & Buyer pairs and score them
    deadline_dt = datetime.strptime(request["sowing_deadline"], "%Y-%m-%d").date()
    target_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
    slack_days = max(0, (deadline_dt - target_dt).days)

    req_tonnage = float(request["estimated_tonnage"])

    for prov, booked_cap in feasible_providers:
        prov_dist = calculate_haversine_distance(
            prov["latitude"], prov["longitude"],
            request["latitude"], request["longitude"]
        )
        for buyer in feasible_buyers:
            farm_to_buyer_dist = calculate_haversine_distance(
                request["latitude"], request["longitude"],
                buyer["latitude"], buyer["longitude"]
            )
            total_est_distance = round(prov_dist + farm_to_buyer_dist, 1)

            # Transparent, explainable scoring:
            # 1. Proximity score (shorter total distance is better, normalized up to 100km): 50 pts
            dist_score = max(0.0, 50.0 * (1.0 - (total_est_distance / 120.0)))
            # 2. Urgency & deadline slack score (more buffer days before deadline = safer): 30 pts
            slack_score = min(30.0, slack_days * 6.0)
            # 3. Provider rate efficiency (cheaper per tonne = better): 20 pts
            rate_score = max(0.0, 20.0 * (1.0 - ((prov["base_rate_per_tonne"] - 400.0) / 200.0)))

            total_score = round(dist_score + slack_score + rate_score, 1)

            est_cost = round(req_tonnage * float(prov["base_rate_per_tonne"]), 2)
            est_revenue = round(req_tonnage * float(buyer["purchase_price_per_tonne"]), 2)

            feasible_matches.append({
                "provider_id": prov["id"],
                "provider_name": prov["name"],
                "provider_district": prov["district"],
                "buyer_id": buyer["id"],
                "buyer_name": buyer["name"],
                "buyer_type": buyer["facility_type"],
                "buyer_district": buyer["district"],
                "target_date": target_date,
                "distance_prov_km": prov_dist,
                "distance_buyer_km": farm_to_buyer_dist,
                "total_distance_km": total_est_distance,
                "estimated_service_cost_inr": est_cost,
                "estimated_buyer_payout_inr": est_revenue,
                "slack_days_before_deadline": slack_days,
                "score": total_score
            })

    # Sort descending by composite score
    feasible_matches.sort(key=lambda x: x["score"], reverse=True)

    return {
        "request": request,
        "target_date": target_date,
        "feasible_matches": feasible_matches,
        "rejections": rejections
    }


def assign_and_schedule_job(
    request_id: str,
    provider_id: str,
    buyer_id: str,
    scheduled_date: str,
    notes: str = ""
) -> Tuple[bool, str]:
    """
    Safely assign a provider and buyer to a request, updating SQLite state transactionally.
    Prevents double booking and capacity overruns.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Fetch request and verify not already scheduled/cancelled
        cursor.execute("SELECT * FROM requests WHERE id = ?", (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.close()
            return False, f"Request {request_id} does not exist."
        if req["status"] in ("SCHEDULED", "IN_COLLECTION", "IN_TRANSIT", "COMPLETED"):
            conn.close()
            return False, f"Request {request_id} is already in status '{req['status']}'."
        if req["status"] == "CANCELLED":
            conn.close()
            return False, f"Request {request_id} is CANCELLED and cannot be scheduled."

        # 2. Verify provider capacity
        cursor.execute("SELECT * FROM providers WHERE id = ?", (provider_id,))
        prov = cursor.fetchone()
        if not prov:
            conn.close()
            return False, f"Provider {provider_id} does not exist."

        booked_today = get_provider_booked_capacity(conn, provider_id, scheduled_date)
        req_tonnage = float(req["estimated_tonnage"])
        if booked_today + req_tonnage > float(prov["daily_capacity_tonnes"]):
            conn.close()
            return False, f"Provider capacity exceeded for {scheduled_date} ({booked_today + req_tonnage:.1f}t > {prov['daily_capacity_tonnes']}t)."

        # 3. Verify buyer capacity
        cursor.execute("SELECT * FROM buyers WHERE id = ?", (buyer_id,))
        buyer = cursor.fetchone()
        if not buyer:
            conn.close()
            return False, f"Buyer {buyer_id} does not exist."

        buyer_cap = float(buyer["daily_intake_capacity_tonnes"])
        buyer_booked = float(buyer["current_booked_intake_tonnes"])
        if buyer_booked + req_tonnage > buyer_cap:
            conn.close()
            return False, f"Buyer quota exceeded ({buyer_booked + req_tonnage:.1f}t > {buyer_cap}t)."

        # 4. Calculate distances and costs
        prov_dist = calculate_haversine_distance(prov["latitude"], prov["longitude"], req["latitude"], req["longitude"])
        buyer_dist = calculate_haversine_distance(req["latitude"], req["longitude"], buyer["latitude"], buyer["longitude"])
        total_dist = round(prov_dist + buyer_dist, 1)
        service_cost = round(req_tonnage * float(prov["base_rate_per_tonne"]), 2)

        # 5. Insert Job
        job_id = f"JOB-{datetime.now().strftime('%m%d%H%M%S')}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO jobs (id, request_id, provider_id, buyer_id, scheduled_date, estimated_distance_km, estimated_service_cost_inr, status, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'SCHEDULED', ?, ?, ?)
        """, (job_id, request_id, provider_id, buyer_id, scheduled_date, total_dist, service_cost, notes, now_str, now_str))

        # 6. Update Request Status
        cursor.execute("UPDATE requests SET status = 'SCHEDULED' WHERE id = ?", (request_id,))

        # 7. Update Buyer booked intake
        cursor.execute("""
            UPDATE buyers 
            SET current_booked_intake_tonnes = current_booked_intake_tonnes + ?
            WHERE id = ?
        """, (req_tonnage, buyer_id))

        # Check if buyer capacity is reached and update status
        if buyer_booked + req_tonnage >= buyer_cap:
            cursor.execute("UPDATE buyers SET status = 'QUOTA_FULL' WHERE id = ?", (buyer_id,))

        conn.commit()
        conn.close()

        log_action("SCHEDULE_ASSIGNMENT", f"Scheduled Job {job_id}: Req {request_id} -> Provider {provider_id}, Buyer {buyer_id} on {scheduled_date}")
        return True, f"Successfully created {job_id} and scheduled for {scheduled_date}."

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Database transaction failed: {str(e)}"


def update_job_status(job_id: str, new_status: str, notes: str = "") -> Tuple[bool, str]:
    """
    Transition job status with validation:
    Valid transitions:
    SCHEDULED -> IN_COLLECTION -> IN_TRANSIT -> COMPLETED
    Any non-completed -> CANCELLED
    """
    valid_transitions = {
        "SCHEDULED": ["IN_COLLECTION", "CANCELLED"],
        "IN_COLLECTION": ["IN_TRANSIT", "CANCELLED"],
        "IN_TRANSIT": ["COMPLETED", "CANCELLED"],
        "COMPLETED": [],
        "CANCELLED": []
    }

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        conn.close()
        return False, f"Job {job_id} not found."

    curr_status = job["status"]
    if new_status not in valid_transitions.get(curr_status, []):
        conn.close()
        return False, f"Invalid transition from '{curr_status}' to '{new_status}'."

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # If cancelling, release buyer intake quota and reset request status
    if new_status == "CANCELLED":
        cursor.execute("SELECT estimated_tonnage FROM requests WHERE id = ?", (job["request_id"],))
        req_tonnage = float(cursor.fetchone()[0])

        cursor.execute("""
            UPDATE buyers 
            SET current_booked_intake_tonnes = MAX(0.0, current_booked_intake_tonnes - ?)
            WHERE id = ?
        """, (req_tonnage, job["buyer_id"]))

        # Also reset request back to UNASSIGNED so it can be re-scheduled
        cursor.execute("UPDATE requests SET status = 'UNASSIGNED' WHERE id = ?", (job["request_id"],))

    else:
        # Sync request status to match job status
        cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, job["request_id"]))

    combined_notes = f"{job['notes'] or ''} | [{now_str}] {new_status}: {notes}".strip(" |")
    cursor.execute("""
        UPDATE jobs 
        SET status = ?, notes = ?, updated_at = ?
        WHERE id = ?
    """, (new_status, combined_notes, now_str, job_id))

    conn.commit()
    conn.close()

    log_action("JOB_STATUS_CHANGE", f"Job {job_id} transitioned from {curr_status} to {new_status}.")
    return True, f"Job {job_id} updated to {new_status}."
