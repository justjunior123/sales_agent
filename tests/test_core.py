"""
Core testing logic for Sales Agent API.

This module contains pure business logic without I/O operations.
Can be imported and used by CLI scripts, Streamlit dashboards, or other tools.

No print statements, no user prompts - just clean, reusable functions.
"""
import os
import requests
from typing import Tuple, Dict, List, Optional


# Sample call data for database population
SAMPLE_CALLS = [
    {
        "carrier_mc": "MC123456",
        "carrier_name": "ABC Trucking",
        "load_id": "LD001",
        "loadboard_rate": 2500,
        "agreed_rate": 2400,
        "negotiation_rounds": 1,
        "outcome": "booked",
        "sentiment": "positive",
        "notes": "Quick decision, very professional",
        "call_duration_seconds": 180
    },
    {
        "carrier_mc": "MC234567",
        "carrier_name": "XYZ Logistics",
        "load_id": "LD002",
        "loadboard_rate": 2200,
        "agreed_rate": 2200,
        "negotiation_rounds": 0,
        "outcome": "booked",
        "sentiment": "positive",
        "notes": "Accepted immediately",
        "call_duration_seconds": 120
    },
    {
        "carrier_mc": "MC345678",
        "carrier_name": "Fast Freight",
        "load_id": "LD003",
        "loadboard_rate": 1800,
        "agreed_rate": 1750,
        "negotiation_rounds": 2,
        "outcome": "negotiated",
        "sentiment": "neutral",
        "notes": "Wanted to think about it",
        "call_duration_seconds": 240
    },
    {
        "carrier_mc": "MC456789",
        "carrier_name": "Slow Haul Inc",
        "load_id": "LD004",
        "loadboard_rate": 1600,
        "agreed_rate": None,
        "negotiation_rounds": 1,
        "outcome": "rejected",
        "sentiment": "negative",
        "notes": "Rate too low, not interested",
        "call_duration_seconds": 90
    },
    {
        "carrier_mc": "MC567890",
        "carrier_name": "Prime Transport",
        "load_id": "LD005",
        "loadboard_rate": 2800,
        "agreed_rate": 2700,
        "negotiation_rounds": 1,
        "outcome": "booked",
        "sentiment": "positive",
        "notes": "Minimal negotiation, booked quickly",
        "call_duration_seconds": 200
    },
    {
        "carrier_mc": "MC678901",
        "carrier_name": "Elite Carriers",
        "load_id": "LD006",
        "loadboard_rate": 1200,
        "agreed_rate": 1200,
        "negotiation_rounds": 0,
        "outcome": "booked",
        "sentiment": "positive",
        "notes": "Backhaul opportunity, accepted immediately",
        "call_duration_seconds": 100
    },
    {
        "carrier_mc": "MC789012",
        "carrier_name": "National Freight",
        "load_id": "LD007",
        "loadboard_rate": 1950,
        "agreed_rate": 1900,
        "negotiation_rounds": 2,
        "outcome": "negotiated",
        "sentiment": "neutral",
        "notes": "Will call back after checking schedule",
        "call_duration_seconds": 280
    },
    {
        "carrier_mc": "MC890123",
        "carrier_name": "Budget Trucking",
        "load_id": "LD008",
        "loadboard_rate": 1400,
        "agreed_rate": None,
        "negotiation_rounds": 3,
        "outcome": "rejected",
        "sentiment": "negative",
        "notes": "Too far from their base, declined",
        "call_duration_seconds": 320
    },
]


def get_api_base_url() -> str:
    """
    Get API base URL from environment variable.

    Supports multiple environments:
    - Local: http://localhost:8000/api/v1
    - Docker: http://api:8000/api/v1 (service name)
    - Deployed: https://your-app.onrender.com/api/v1

    Returns:
        API base URL string
    """
    return os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def make_api_call(method: str, endpoint: str, **kwargs) -> Tuple[bool, Optional[Dict]]:
    """
    Make an API call and return success status + data.

    Args:
        method: HTTP method ("GET" or "POST")
        endpoint: API endpoint path (without base URL)
        **kwargs: Additional arguments to pass to requests

    Returns:
        (success, data) tuple
    """
    base_url = get_api_base_url()

    # Handle special cases for health endpoint
    if endpoint == "/health":
        url = base_url.replace('/api/v1', '/health')
    else:
        url = f"{base_url}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        else:
            return (False, {"error": f"Unsupported method: {method}"})

        if response.ok:
            return (True, response.json())
        else:
            return (False, {"error": f"HTTP {response.status_code}: {response.text}"})

    except Exception as e:
        return (False, {"error": str(e)})


def populate_database() -> Tuple[bool, str]:
    """
    Populate database with sample call data.

    Calls the /log_call endpoint for each sample call in SAMPLE_CALLS.

    Returns:
        (success, message) tuple
        - success: True if all calls logged successfully
        - message: Human-readable result message
    """
    logged_count = 0
    failed_calls = []

    for call_data in SAMPLE_CALLS:
        # Build query params (exclude None values)
        params = {k: v for k, v in call_data.items() if v is not None}

        success, result = make_api_call("POST", "/log_call", params=params)

        if success:
            logged_count += 1
        else:
            failed_calls.append(call_data['carrier_name'])

    # Build result message
    if logged_count == len(SAMPLE_CALLS):
        return (True, f"Successfully loaded {logged_count} sample calls")
    elif logged_count > 0:
        return (True, f"Loaded {logged_count}/{len(SAMPLE_CALLS)} calls (some failed)")
    else:
        return (False, "Failed to load sample calls. Check API connection.")


def clear_database() -> Tuple[bool, str]:
    """
    Clear all calls from the database.

    Uses direct database import to delete all records.

    Returns:
        (success, message) tuple
    """
    try:
        # Import here to avoid circular dependencies
        import sys
        import os
        # Add parent directory to path
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        from app.data.db import delete_all_calls

        delete_all_calls()
        return (True, "Database cleared successfully")

    except Exception as e:
        return (False, f"Failed to clear database: {str(e)}")


def test_health_endpoint() -> Tuple[bool, str]:
    """Test the health check endpoint."""
    success, data = make_api_call("GET", "/health")

    if success:
        return (True, "Health check passed")
    else:
        return (False, f"Health check failed: {data.get('error', 'Unknown error')}")


def test_carrier_verification() -> Tuple[bool, str]:
    """Test carrier verification endpoint with sample MC number."""
    test_data = {"mc_number": "MC139512"}
    success, data = make_api_call("POST", "/verify_carrier", json=test_data)

    if success and data.get("eligible"):
        return (True, f"Carrier verified: {data.get('carrier_name')}")
    elif success:
        return (True, f"Verification returned ineligible: {data.get('reason')}")
    else:
        return (False, f"Verification failed: {data.get('error')}")


def test_load_search() -> Tuple[bool, str]:
    """Test load search endpoint."""
    test_data = {
        "origin": "Los Angeles, CA",
        "destination": "Houston, TX",
        "equipment_type": "53ft Dry Van"
    }
    success, data = make_api_call("POST", "/search_loads", json=test_data)

    if success:
        load_count = data.get("total_matches", 0)
        return (True, f"Found {load_count} matching loads")
    else:
        return (False, f"Load search failed: {data.get('error')}")


def test_negotiation() -> Tuple[bool, str]:
    """Test negotiation evaluation endpoint."""
    test_data = {
        "original_rate": 2500,
        "counter_rate": 2400,
        "load_id": "LD001"
    }
    success, data = make_api_call("POST", "/evaluate_offer", json=test_data)

    if success:
        decision = data.get("decision", "unknown")
        return (True, f"Negotiation evaluated: {decision}")
    else:
        return (False, f"Negotiation test failed: {data.get('error')}")


def run_all_tests() -> Dict[str, Tuple[bool, str]]:
    """
    Run all endpoint tests.

    Returns:
        Dictionary mapping test names to (success, message) tuples
    """
    tests = {
        "Health Check": test_health_endpoint(),
        "Carrier Verification": test_carrier_verification(),
        "Load Search": test_load_search(),
        "Negotiation Evaluation": test_negotiation(),
    }

    return tests


def get_api_status() -> Tuple[bool, str]:
    """
    Check if API is reachable and responding.

    Returns:
        (is_running, message) tuple
    """
    success, data = make_api_call("GET", "/health")

    if success:
        return (True, "API is running and healthy")
    else:
        error_msg = data.get('error', 'Unknown error')
        return (False, f"API not reachable: {error_msg}")
