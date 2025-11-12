"""
CLI wrapper for populating test data.

This script provides a command-line interface for testing the Sales Agent API
and populating the database with sample data.

Usage:
    python tests/populate_test_data.py

The core logic lives in test_core.py and can be imported elsewhere (e.g., Streamlit dashboard).
"""
from test_core import (
    populate_database,
    clear_database,
    run_all_tests,
    get_api_status,
    get_api_base_url,
    SAMPLE_CALLS
)
from datetime import datetime


def print_header(title: str, width: int = 60):
    """Print a formatted section header."""
    print("\n" + "="*width)
    print(f"  {title}")
    print("="*width)


def print_test_result(name: str, success: bool, message: str):
    """Print a formatted test result."""
    icon = "✅" if success else "❌"
    print(f"{icon} {name}: {message}")


def main():
    """Main CLI entry point."""
    print_header("SALES AGENT API TEST SUITE")
    print(f"Testing against: {get_api_base_url()}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if API is running
    is_running, status_msg = get_api_status()

    if not is_running:
        print(f"\n❌ {status_msg}")
        print("\nPlease start the API first:")
        print("   python -m uvicorn app.main:app --reload --port 8000")
        return

    print(f"✅ {status_msg}\n")

    # Run all tests
    print_header("RUNNING ENDPOINT TESTS")

    test_results = run_all_tests()

    for test_name, (success, message) in test_results.items():
        print_test_result(test_name, success, message)

    # Populate database
    print_header("POPULATING DATABASE")

    print(f"Loading {len(SAMPLE_CALLS)} sample calls...")
    success, message = populate_database()

    print_test_result("Database Population", success, message)

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for s, _ in test_results.values() if s)
    total = len(test_results)

    print(f"✅ Endpoint tests: {passed}/{total} passed")
    print(f"✅ Database populated: {message}")
    print("\nNext steps:")
    print("1. Open dashboard: streamlit run streamlit/dashboard.py")
    print("2. View API docs: http://localhost:8000/docs")
    print("3. Check call logs: http://localhost:8000/api/v1/call_logs")
    print()


if __name__ == "__main__":
    print("\n⚠️  Make sure the API is running first:")
    print("   python -m uvicorn app.main:app --reload --port 8000\n")

    response = input("Is the API running? (y/n): ")

    if response.lower() == 'y':
        main()
    else:
        print("\nStart the API first, then run this script again.")
