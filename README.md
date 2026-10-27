# Parali-to-Power: Intelligent Biomass Supply & Energy Coordination System
**TPPC-2026 Technical Poster Presentation Competition Entry**

A prototype for coordinating crop residue (parali) collection between farmers, custom hiring machinery centers (CHCs), and industrial biomass energy off-takers (Bio-CNG, Pelletization, and Thermal Power Co-Firing plants).

> **⚠️ ACADEMIC INTEGRITY NOTICE — SIMULATED DEMO DATA**  
> All records (farmers, machinery aggregators, off-taker depots, and prices) are fictional scenarios representing Punjab and Haryana supply clusters. Operational metrics are calculated directly from simulation decisions and database records. No unverified empirical or environmental claims are made.

---

## 🌾 Key System Components

1. **Operations Overview Dashboard (`views/dashboard.py`)**
   - Live operational KPI metrics computed dynamically from SQLite.
   - Urgent "Needs Attention" alert panel for impending sowing deadlines.
   - Geospatial supply cluster coordination map (Punjab & Haryana coordinate clusters).
   - Status pipeline distribution chart.

2. **Farmer Requests Portal (`views/farmer_requests.py`)**
   - Submit new crop-residue collection requests with field area, residue variety, harvest date, and hard wheat-sowing deadline.
   - Direct validation prevents invalid deadlines or zero-tonnage entries.
   - Filterable requests table.

3. **Service Providers & Intelligent Scheduling (`views/scheduling.py`, `core/scheduler.py`)**
   - Hard feasibility checks: active status, required baling machinery, max service radius (km), daily throughput capacity (t/day), scheduling conflicts, and buyer receiving quota.
   - Transparent multi-factor ranking: Proximity (50%) + Deadline Slack (30%) + Rate Efficiency (20%).
   - Transparent Rejection Audit: Lists explicit causes when candidates fail (e.g. radius exceeded, maintenance, insufficient remaining capacity).
   - Single-click transactional job assignment.

4. **Biomass Buyers & Off-Take Depots (`views/buyers.py`)**
   - Track intake quotas and receiving capacities across Bio-CNG, Power Co-Firing, and Pellet plants.
   - Interactive status controls (ACCEPTING, QUOTA_FULL, MAINTENANCE).
   - Incoming delivery tracking.

5. **Field Job Tracking Pipeline (`views/job_tracking.py`)**
   - Validated state machine: `SCHEDULED` ➔ `IN_COLLECTION` ➔ `IN_TRANSIT` ➔ `COMPLETED` (or `CANCELLED`).
   - Prevents illegal status skipping.
   - Automatic quota release and request reopening upon cancellation.

6. **Algorithmic Evaluation Benchmark (`views/algorithm_eval.py`, `core/evaluation.py`)**
   - Side-by-side comparison of the Proposed Multi-Factor Coordination against a First-Come-First-Served (FCFS) heuristic baseline.
   - Real operational metrics: on-time deadline rate, average transit road distance (km/job), total service cost, fleet capacity utilization, and rejection reasons breakdown.

---

## 🚀 Quickstart & Commands

### 1. Run Automated Unit Tests
```bash
python -m pytest tests/ -v
```

### 2. Launch Streamlit Application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Architecture Overview
```text
parali-to-power/
├── app.py                      # Main application entry point & page navigation router
├── styles.py                   # Agri-sustainability visual design system (CSS & Plotly themes)
├── conftest.py                 # Pytest environment path configuration
├── core/
│   ├── db.py                   # SQLite database schema, connections, and transactional logs
│   ├── seed_data.py            # Fictional demonstration clusters (Punjab/Haryana)
│   ├── scheduler.py            # Feasibility rules, candidate scoring & state progression
│   └── evaluation.py           # Simulation benchmark comparing Proposed vs. FCFS
├── views/
│   ├── dashboard.py            # Operational overview & urgent alerts
│   ├── farmer_requests.py      # Request logging & roster
│   ├── scheduling.py           # Candidate matching & rejection audit
│   ├── buyers.py               # Energy off-taker intake quota monitoring
│   ├── job_tracking.py         # Sequential job lifecycle management
│   └── algorithm_eval.py       # Comparative evaluation metrics & visual charts
└── tests/
    └── test_scheduler.py       # Pytest suite validating feasibility, radius, & capacity
```
