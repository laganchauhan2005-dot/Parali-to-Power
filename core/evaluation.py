"""
Simulation and comparative benchmark between:
1. Proposed Intelligent Coordination System (Multi-factor: Urgency + Proximity + Capacity)
2. First-Come-First-Served (FCFS) Heuristic Baseline

Operational metrics are calculated strictly from simulated demonstration records.
No speculative CO2 or burning claims are made.
"""
from typing import Dict, Any, List
from core.db import get_db_connection
from core.scheduler import (
    calculate_haversine_distance,
    check_provider_feasibility,
    check_buyer_feasibility
)


def run_benchmark_comparison() -> Dict[str, Any]:
    """
    Run both scheduling approaches over all demonstration requests in a sandbox simulation
    (without altering the actual database state).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM requests")
    all_requests = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM providers")
    all_providers = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM buyers")
    all_buyers = [dict(r) for r in cursor.fetchall()]

    conn.close()

    total_submitted = len(all_requests)

    # -------------------------------------------------------------
    # 1. BASELINE: First-Come-First-Served (FCFS)
    # Process in strict submission order; assign first provider/buyer found.
    # -------------------------------------------------------------
    fcfs_requests = sorted(all_requests, key=lambda x: x["created_at"])
    fcfs_scheduled = 0
    fcfs_ontime = 0
    fcfs_unassigned = 0
    fcfs_total_distance = 0.0
    fcfs_total_cost = 0.0
    fcfs_rejection_reasons = {}

    # Track simulated capacity
    fcfs_prov_usage = {p["id"]: 0.0 for p in all_providers}
    fcfs_buyer_usage = {b["id"]: 0.0 for b in all_buyers}

    for req in fcfs_requests:
        assigned = False
        target_date = req["harvest_date"]
        req_tonnage = float(req["estimated_tonnage"])

        # Baseline picks the first provider with baler regardless of distance optimization
        for prov in all_providers:
            # Check availability
            if prov["status"] != "ACTIVE":
                continue
            if "baler" not in prov["equipment_types"].lower():
                continue
            # Capacity check
            rem_cap = float(prov["daily_capacity_tonnes"]) - fcfs_prov_usage[prov["id"]]
            if req_tonnage > rem_cap:
                continue
            # Distance check (hard physical limit)
            dist_p = calculate_haversine_distance(prov["latitude"], prov["longitude"], req["latitude"], req["longitude"])
            if dist_p > prov["max_service_radius_km"]:
                continue

            # Find first available buyer with quota
            for buyer in all_buyers:
                if buyer["status"] != "ACCEPTING":
                    continue
                rem_b_cap = float(buyer["daily_intake_capacity_tonnes"]) - fcfs_buyer_usage[buyer["id"]]
                if req_tonnage > rem_b_cap:
                    continue
                dist_b = calculate_haversine_distance(req["latitude"], req["longitude"], buyer["latitude"], buyer["longitude"])
                if dist_b > 85.0:
                    continue

                # FCFS Assignment made
                assigned = True
                fcfs_scheduled += 1
                fcfs_prov_usage[prov["id"]] += req_tonnage
                fcfs_buyer_usage[buyer["id"]] += req_tonnage
                tot_dist = dist_p + dist_b
                fcfs_total_distance += tot_dist
                fcfs_total_cost += req_tonnage * float(prov["base_rate_per_tonne"])

                # Check if deadline met
                if target_date <= req["sowing_deadline"]:
                    fcfs_ontime += 1
                break

            if assigned:
                break

        if not assigned:
            fcfs_unassigned += 1
            reason = "No available provider/buyer within radius or capacity limits under arrival sequence"
            fcfs_rejection_reasons[req["id"]] = reason

    # -------------------------------------------------------------
    # 2. PROPOSED: Intelligent Multi-Factor Coordination
    # Prioritizes tightest sowing deadline first, minimizes transit distance,
    # and balances provider & buyer capacity.
    # -------------------------------------------------------------
    # Sort by urgency: sowing_deadline ascending, then tonnage
    prop_requests = sorted(all_requests, key=lambda x: (x["sowing_deadline"], -x["estimated_tonnage"]))
    prop_scheduled = 0
    prop_ontime = 0
    prop_unassigned = 0
    prop_total_distance = 0.0
    prop_total_cost = 0.0
    prop_rejection_reasons = {}

    prop_prov_usage = {p["id"]: 0.0 for p in all_providers}
    prop_buyer_usage = {b["id"]: 0.0 for b in all_buyers}

    for req in prop_requests:
        target_date = req["harvest_date"]
        req_tonnage = float(req["estimated_tonnage"])

        best_candidate = None
        best_score = -1.0

        for prov in all_providers:
            if prov["status"] != "ACTIVE":
                continue
            if "baler" not in prov["equipment_types"].lower():
                continue
            rem_cap = float(prov["daily_capacity_tonnes"]) - prop_prov_usage[prov["id"]]
            if req_tonnage > rem_cap:
                continue
            dist_p = calculate_haversine_distance(prov["latitude"], prov["longitude"], req["latitude"], req["longitude"])
            if dist_p > prov["max_service_radius_km"]:
                continue

            for buyer in all_buyers:
                if buyer["status"] != "ACCEPTING":
                    continue
                rem_b_cap = float(buyer["daily_intake_capacity_tonnes"]) - prop_buyer_usage[buyer["id"]]
                if req_tonnage > rem_b_cap:
                    continue
                dist_b = calculate_haversine_distance(req["latitude"], req["longitude"], buyer["latitude"], buyer["longitude"])
                if dist_b > 80.0:
                    continue

                tot_dist = dist_p + dist_b
                # Multi-factor score favoring proximity and cost efficiency
                score = (120.0 - tot_dist) * 0.7 + (600.0 - float(prov["base_rate_per_tonne"])) * 0.3
                if score > best_score:
                    best_score = score
                    best_candidate = (prov, buyer, tot_dist, float(prov["base_rate_per_tonne"]))

        if best_candidate:
            prov, buyer, tot_dist, rate = best_candidate
            prop_scheduled += 1
            prop_prov_usage[prov["id"]] += req_tonnage
            prop_buyer_usage[buyer["id"]] += req_tonnage
            prop_total_distance += tot_dist
            prop_total_cost += req_tonnage * rate

            if target_date <= req["sowing_deadline"]:
                prop_ontime += 1
        else:
            prop_unassigned += 1
            # Check why
            dist_min = min([calculate_haversine_distance(p["latitude"], p["longitude"], req["latitude"], req["longitude"]) for p in all_providers])
            if dist_min > 45.0:
                reason = f"Geographically remote: nearest provider is {dist_min:.1f} km away (exceeds 45 km radius)."
            elif req_tonnage > 60.0:
                reason = f"High batch volume ({req_tonnage:.1f}t) exceeds available single-day aggregator capacities."
            else:
                reason = "All suitable providers/buyers at maximum capacity for requested date window."
            prop_rejection_reasons[req["id"]] = reason

    # Calculate provider utilization
    total_prov_capacity = sum(float(p["daily_capacity_tonnes"]) for p in all_providers if p["status"] == "ACTIVE")
    fcfs_utilization = round((sum(fcfs_prov_usage.values()) / max(1.0, total_prov_capacity)) * 100, 1)
    prop_utilization = round((sum(prop_prov_usage.values()) / max(1.0, total_prov_capacity)) * 100, 1)

    return {
        "total_requests": total_submitted,
        "fcfs": {
            "name": "First-Come-First-Served (FCFS Baseline)",
            "scheduled_count": fcfs_scheduled,
            "scheduled_pct": round((fcfs_scheduled / max(1, total_submitted)) * 100, 1),
            "ontime_count": fcfs_ontime,
            "ontime_pct": round((fcfs_ontime / max(1, fcfs_scheduled)) * 100, 1) if fcfs_scheduled > 0 else 0.0,
            "unassigned_count": fcfs_unassigned,
            "total_estimated_distance_km": round(fcfs_total_distance, 1),
            "avg_distance_per_job_km": round(fcfs_total_distance / max(1, fcfs_scheduled), 1),
            "total_estimated_cost_inr": round(fcfs_total_cost, 2),
            "provider_capacity_utilization_pct": fcfs_utilization,
            "rejections": fcfs_rejection_reasons
        },
        "proposed": {
            "name": "Intelligent Multi-Factor Coordination",
            "scheduled_count": prop_scheduled,
            "scheduled_pct": round((prop_scheduled / max(1, total_submitted)) * 100, 1),
            "ontime_count": prop_ontime,
            "ontime_pct": round((prop_ontime / max(1, prop_scheduled)) * 100, 1) if prop_scheduled > 0 else 0.0,
            "unassigned_count": prop_unassigned,
            "total_estimated_distance_km": round(prop_total_distance, 1),
            "avg_distance_per_job_km": round(prop_total_distance / max(1, prop_scheduled), 1),
            "total_estimated_cost_inr": round(prop_total_cost, 2),
            "provider_capacity_utilization_pct": prop_utilization,
            "rejections": prop_rejection_reasons
        }
    }
