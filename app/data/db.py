"""
SQLite database setup and operations for call logs.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import uuid


DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "sales_agent.db"))


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_database():
    """
    Initialize the database with required schema.
    Safe to call multiple times (uses IF NOT EXISTS).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Create call_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS call_logs (
            call_id TEXT PRIMARY KEY,
            carrier_mc TEXT NOT NULL,
            carrier_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            load_id TEXT,
            loadboard_rate REAL,
            agreed_rate REAL,
            negotiation_rounds INTEGER DEFAULT 0,
            outcome TEXT CHECK(outcome IN ('booked', 'negotiated', 'rejected')),
            sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative')),
            notes TEXT,
            call_duration_seconds INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index on timestamp for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON call_logs(timestamp)
    """)

    # Create index on outcome for filtering
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_outcome ON call_logs(outcome)
    """)

    conn.commit()
    conn.close()


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
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO call_logs (
            call_id, carrier_mc, carrier_name, timestamp, load_id,
            loadboard_rate, agreed_rate, negotiation_rounds, outcome,
            sentiment, notes, call_duration_seconds
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        call_id, carrier_mc, carrier_name, timestamp, load_id,
        loadboard_rate, agreed_rate, negotiation_rounds, outcome,
        sentiment, notes, call_duration_seconds
    ))

    conn.commit()
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
        query += " AND timestamp >= ?"
        params.append(start_date)

    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date)

    if outcome:
        query += " AND outcome = ?"
        params.append(outcome)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    # Convert to list of dictionaries
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
    averages = dict(cursor.fetchone())

    # Margin analysis (difference between board rate and agreed rate)
    cursor.execute("""
        SELECT
            AVG(loadboard_rate - agreed_rate) as avg_discount,
            MIN(agreed_rate) as min_agreed_rate,
            MAX(agreed_rate) as max_agreed_rate
        FROM call_logs
        WHERE loadboard_rate IS NOT NULL AND agreed_rate IS NOT NULL
    """)
    margin_data = dict(cursor.fetchone())

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
    cursor.execute("DELETE FROM call_logs")
    conn.commit()
    conn.close()


# Initialize database on module import
init_database()
