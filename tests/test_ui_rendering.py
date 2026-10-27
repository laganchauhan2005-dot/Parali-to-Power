"""
Automated validation of all six Streamlit application views.
Verifies that database queries, calculations, layout components, and Plotly charts
render without throwing unhandled exceptions.
"""
import pytest
from core.db import init_db, reset_database
from views.dashboard import render_dashboard
from views.farmer_requests import render_farmer_requests
from views.scheduling import render_scheduling
from views.buyers import render_buyers
from views.job_tracking import render_job_tracking
from views.algorithm_eval import render_evaluation
from styles import apply_custom_styles


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    yield


def test_all_views_execute_without_runtime_errors():
    """Verify each page renders cleanly under the unified light theme."""
    apply_custom_styles()
    render_dashboard()
    render_farmer_requests()
    render_scheduling()
    render_buyers()
    render_job_tracking()
    render_evaluation()
