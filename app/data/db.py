"""
PostgreSQL database operations for call logs using Supabase.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable not set. "
        "Please set it to your Supabase PostgreSQL connection string."
    )


def get_connection():
    """Get a database connection to Supabase PostgreSQL."""
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor  # Return rows as dictionaries
        )
        return conn
    except psycopg2.OperationalError as e:
        raise ConnectionError(f"Failed to connect to database: {str(e)}")


def init_database():
    """
    Check database connectivity.
    Table creation is handled in Supabase SQL Editor.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verify table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'call_logs'
            )
        """)
        table_exists = cursor.fetchone()['exists']

        conn.close()

        if not table_exists:
            raise RuntimeError(
                "Table 'call_logs' does not exist in database. "
                "Please create it using the SQL schema in Supabase."
            )

    except Exception as e:
        print(f"Warning: Database initialization check failed: {str(e)}")


def insert_call_log(
    carrier_mc: str,
    carrier_name: Optional[str] = None,
    load_id: Optional[str] = None,
    loadboard_rate: Optional[float] = None,
    agreed_rate: Optional[float] = None,
    negotiation_rounds: int = 0,
    outcome: str = "negotiated",
    sentiment: str = "neutral",
    notes: Optional[str] = None,
    call_duration_seconds: int = 0
) -> str:
    """
    Insert a new call log entry.

    Returns:
        call_id of the inserted record
    """
    conn = get_connection()
    cursor = conn.cursor()

    call_id = f"CALL_{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now()

    try:
        cursor.execute("""
            INSERT INTO call_logs (
                call_id, carrier_mc, carrier_name, timestamp, load_id,
                loadboard_rate, agreed_rate, negotiation_rounds, outcome,
                sentiment, notes, call_duration_seconds
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            call_id, carrier_mc, carrier_name, timestamp, load_id,
            loadboard_rate, agreed_rate, negotiation_rounds, outcome,
            sentiment, notes, call_duration_seconds
        ))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return call_id


def get_call_logs(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Retrieve call logs with optional filtering.

    Args:
        start_date: ISO format date string (e.g., "2025-11-01")
        end_date: ISO format date string
        outcome: Filter by outcome (booked, negotiated, rejected)
        limit: Maximum number of records to return

    Returns:
        List of call log dictionaries
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build query with filters
    query = "SELECT * FROM call_logs WHERE 1=1"
    params = []

    if start_date:
        query += " AND timestamp >= %s"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= %s"
        params.append(end_date)

    if outcome:
        query += " AND outcome = %s"
        params.append(outcome)

    query += " ORDER BY timestamp DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    # Convert to list of dictionaries (RealDictCursor already returns dicts)
    return [dict(row) for row in rows]


def get_call_stats() -> Dict[str, Any]:
    """
    Get aggregate statistics about calls.

    Returns:
        Dictionary with call statistics
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total calls
    cursor.execute("SELECT COUNT(*) as total FROM call_logs")
    total_calls = cursor.fetchone()["total"]

    # Calls by outcome
    cursor.execute("""
        SELECT outcome, COUNT(*) as count
        FROM call_logs
        GROUP BY outcome
    """)
    outcome_counts = {row["outcome"]: row["count"] for row in cursor.fetchall()}

    # Calls by sentiment
    cursor.execute("""
        SELECT sentiment, COUNT(*) as count
        FROM call_logs
        GROUP BY sentiment
    """)
    sentiment_counts = {row["sentiment"]: row["count"] for row in cursor.fetchall()}

    # Average rates
    cursor.execute("""
        SELECT
            AVG(loadboard_rate) as avg_loadboard_rate,
            AVG(agreed_rate) as avg_agreed_rate,
            AVG(negotiation_rounds) as avg_negotiation_rounds,
            AVG(call_duration_seconds) as avg_call_duration
        FROM call_logs
        WHERE loadboard_rate IS NOT NULL AND agreed_rate IS NOT NULL
    """)
    averages_row = cursor.fetchone()
    averages = dict(averages_row) if averages_row else {}

    # Margin analysis (difference between board rate and agreed rate)
    cursor.execute("""
        SELECT
            AVG(loadboard_rate - agreed_rate) as avg_discount,
            MIN(agreed_rate) as min_agreed_rate,
            MAX(agreed_rate) as max_agreed_rate
        FROM call_logs
        WHERE loadboard_rate IS NOT NULL AND agreed_rate IS NOT NULL
    """)
    margin_row = cursor.fetchone()
    margin_data = dict(margin_row) if margin_row else {}

    conn.close()

    return {
        "total_calls": total_calls,
        "outcome_counts": outcome_counts,
        "sentiment_counts": sentiment_counts,
        "averages": averages,
        "margin_analysis": margin_data
    }


def delete_all_calls():
    """
    Delete all call logs. Use with caution!
    Useful for testing and demo resets.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM call_logs")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# Initialize database check on module import
init_database()
