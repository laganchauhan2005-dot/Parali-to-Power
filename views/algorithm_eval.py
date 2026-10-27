"""
Algorithm Evaluation View for Parali-to-Power.
Compares Proposed Intelligent Multi-Factor Coordination against
First-Come-First-Served (FCFS) heuristic baseline on identical scenarios.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from core.evaluation import run_benchmark_comparison
from styles import (
    apply_plotly_theme,
    PRIMARY_FOREST,
    SECONDARY_SAGE,
    ACCENT_BEIGE,
    TEXT_MAIN,
    TEXT_SECONDARY,
    BORDER_LIGHT
)


def render_evaluation():
    st.markdown('<div class="sim-banner">Simulated Demo Data — Algorithmic Benchmark</div>', unsafe_allow_html=True)
    st.title("⚖️ Coordination Algorithm Evaluation")
    st.caption("Benchmark: Intelligent Multi-Factor Coordination vs. Standard First-Come-First-Served (FCFS) Baseline.")

    st.markdown("""
    > **Note on Evaluation Methodology:**  
    > All metrics below are **operational outcomes computed directly from the simulated Punjab/Haryana demonstration dataset**.  
    > In accordance with academic presentation integrity standards for TPPC-2026, metrics reflect actual algorithmic assignment decisions (deadlines met, transport distance, capacity utilization, and explicit rejection causes) rather than unsupported environmental or empirical claims.
    """)

    # Run comparative benchmark
    results = run_benchmark_comparison()
    fcfs = results["fcfs"]
    prop = results["proposed"]

    # 1. High-level Comparison Cards
    with st.container(border=True):
        st.subheader("📊 Side-by-Side Operational Performance Summary")

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div style="font-size:0.82rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">SCHEDULED RATE</div>
            <div style="font-size:1.6rem; font-weight:800; color:{PRIMARY_FOREST}; margin: 4px 0;">
                {prop['scheduled_pct']}% <span style="font-size:0.85rem; color:#2D6A4F;">({prop['scheduled_count']}/{results['total_requests']})</span>
            </div>
            <div style="font-size:0.80rem; color:{TEXT_SECONDARY};">FCFS Baseline: {fcfs['scheduled_pct']}% ({fcfs['scheduled_count']}/{results['total_requests']})</div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div style="font-size:0.82rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">ON-TIME TO DEADLINE</div>
            <div style="font-size:1.6rem; font-weight:800; color:{PRIMARY_FOREST}; margin: 4px 0;">
                {prop['ontime_pct']}%
            </div>
            <div style="font-size:0.80rem; color:{TEXT_SECONDARY};">FCFS Baseline: {fcfs['ontime_pct']}%</div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div style="font-size:0.82rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">AVG TRANSIT DISTANCE</div>
            <div style="font-size:1.6rem; font-weight:800; color:{PRIMARY_FOREST}; margin: 4px 0;">
                {prop['avg_distance_per_job_km']} <span style="font-size:0.85rem;">km / job</span>
            </div>
            <div style="font-size:0.80rem; color:{TEXT_SECONDARY};">FCFS Baseline: {fcfs['avg_distance_per_job_km']} km</div>
            """, unsafe_allow_html=True)

        with c4:
            st.markdown(f"""
            <div style="font-size:0.82rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;">FLEET UTILIZATION</div>
            <div style="font-size:1.6rem; font-weight:800; color:{PRIMARY_FOREST}; margin: 4px 0;">
                {prop['provider_capacity_utilization_pct']}%
            </div>
            <div style="font-size:0.80rem; color:{TEXT_SECONDARY};">FCFS Baseline: {fcfs['provider_capacity_utilization_pct']}%</div>
            """, unsafe_allow_html=True)

    # 2. Detailed Metric Comparison Table
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("📑 Detailed Comparative Metrics Matrix")

        comp_table = [
            {"Operational Metric": "Total Demonstration Requests Evaluated", "FCFS Baseline": f"{results['total_requests']}", "Proposed Intelligent System": f"{results['total_requests']}", "Difference / Impact": "Equal Scenario Batch"},
            {"Operational Metric": "Requests Successfully Scheduled", "FCFS Baseline": f"{fcfs['scheduled_count']} ({fcfs['scheduled_pct']}%)", "Proposed Intelligent System": f"{prop['scheduled_count']} ({prop['scheduled_pct']}%)", "Difference / Impact": f"+{prop['scheduled_count'] - fcfs['scheduled_count']} requests coordinated"},
            {"Operational Metric": "On-Time Deadline Compliance Rate", "FCFS Baseline": f"{fcfs['ontime_pct']}%", "Proposed Intelligent System": f"{prop['ontime_pct']}%", "Difference / Impact": f"{prop['ontime_pct'] - fcfs['ontime_pct']:+.1f}% improved compliance"},
            {"Operational Metric": "Total Estimated Road Mileage (km)", "FCFS Baseline": f"{fcfs['total_estimated_distance_km']} km", "Proposed Intelligent System": f"{prop['total_estimated_distance_km']} km", "Difference / Impact": f"{prop['total_estimated_distance_km'] - fcfs['total_estimated_distance_km']:+.1f} km (Proximity routing)"},
            {"Operational Metric": "Average Distance per Dispatched Job", "FCFS Baseline": f"{fcfs['avg_distance_per_job_km']} km", "Proposed Intelligent System": f"{prop['avg_distance_per_job_km']} km", "Difference / Impact": f"{prop['avg_distance_per_job_km'] - fcfs['avg_distance_per_job_km']:+.1f} km / job"},
            {"Operational Metric": "Estimated Total Service Cost", "FCFS Baseline": f"₹{fcfs['total_estimated_cost_inr']:,.2f}", "Proposed Intelligent System": f"₹{prop['total_estimated_cost_inr']:,.2f}", "Difference / Impact": "Rate-weighted allocation"},
            {"Operational Metric": "Active Provider Fleet Capacity Utilized", "FCFS Baseline": f"{fcfs['provider_capacity_utilization_pct']}%", "Proposed Intelligent System": f"{prop['provider_capacity_utilization_pct']}%", "Difference / Impact": "Balanced cluster utilization"},
            {"Operational Metric": "Unassigned Requests Remaining", "FCFS Baseline": f"{fcfs['unassigned_count']}", "Proposed Intelligent System": f"{prop['unassigned_count']}", "Difference / Impact": f"{prop['unassigned_count'] - fcfs['unassigned_count']:+d} unassigned"}
        ]

        st.dataframe(pd.DataFrame(comp_table), use_container_width=True, hide_index=True)

    # 3. Visual Charts
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("📈 Visual Comparison: Efficiency & Transit Road Mileage")

        c_c1, c_c2 = st.columns(2)

        with c_c1:
            categories = ["Scheduled On-Time", "Unassigned / Rejected"]
            fig1 = go.Figure(data=[
                go.Bar(name="FCFS Baseline", x=categories, y=[fcfs["ontime_count"], fcfs["unassigned_count"]], marker_color="#E76F51"),
                go.Bar(name="Proposed Intelligent", x=categories, y=[prop["ontime_count"], prop["unassigned_count"]], marker_color=PRIMARY_FOREST)
            ])
            fig1.update_layout(
                barmode="group",
                title=dict(text="Requests Serviced vs. Unassigned", y=0.96),
                height=300,
                margin=dict(t=50, b=20, l=20, r=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig1 = apply_plotly_theme(fig1)
            st.plotly_chart(fig1, use_container_width=True)

        with c_c2:
            fig2 = go.Figure(data=[
                go.Bar(
                    x=["FCFS Baseline", "Proposed System"],
                    y=[fcfs["avg_distance_per_job_km"], prop["avg_distance_per_job_km"]],
                    marker_color=["#E76F51", SECONDARY_SAGE]
                )
            ])
            fig2.update_layout(
                title=dict(text="Average Transport Transit Distance (km/job)", y=0.96),
                height=300,
                margin=dict(t=50, b=20, l=20, r=20)
            )
            fig2 = apply_plotly_theme(fig2)
            st.plotly_chart(fig2, use_container_width=True)

    # 4. Transparent Rejection Breakdown
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("🔍 Analysis of Infeasible / Unassigned Requests")
        st.caption("Why certain requests could not be matched under rigorous physical constraints.")

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("**Proposed Intelligent Scheduler Unassigned Audit:**")
            if not prop["rejections"]:
                st.info("No requests were rejected.")
            else:
                for req_id, reason in prop["rejections"].items():
                    st.markdown(f"• **Request {req_id}**: <span style='color:#BC4749;'>{reason}</span>", unsafe_allow_html=True)

        with col_r2:
            st.markdown("**FCFS Baseline Unassigned Audit:**")
            if not fcfs["rejections"]:
                st.info("No requests were rejected.")
            else:
                for req_id, reason in fcfs["rejections"].items():
                    st.markdown(f"• **Request {req_id}**: <span style='color:#BC4749;'>{reason}</span>", unsafe_allow_html=True)
