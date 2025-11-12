"""
Load search and matching service.
"""
import json
import os
from typing import List, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser


LOADS_FILE = os.path.join(os.path.dirname(__file__), "../data/loads.json")


def load_loads_database() -> List[Dict[str, Any]]:
    """Load all available loads from JSON file."""
    try:
        with open(LOADS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def normalize_location(location: str) -> str:
    """
    Normalize location string for comparison.
    'Los Angeles, CA' -> 'los angeles ca'
    """
    return location.lower().strip().replace(",", "")


def calculate_location_match(search_loc: str, load_loc: str) -> float:
    """
    Calculate how well two locations match.
    Returns score from 0.0 to 1.0

    Exact match: 1.0
    City match (different state): 0.7
    State match (different city): 0.5
    No match: 0.0
    """
    search_norm = normalize_location(search_loc)
    load_norm = normalize_location(load_loc)

    # Exact match
    if search_norm == load_norm:
        return 1.0

    # Check if one is contained in the other
    if search_norm in load_norm or load_norm in search_norm:
        return 0.8

    # Try to extract city and state
    search_parts = search_norm.split()
    load_parts = load_norm.split()

    # Check for state match (last part is usually state abbreviation)
    if len(search_parts) >= 2 and len(load_parts) >= 2:
        if search_parts[-1] == load_parts[-1]:  # State matches
            return 0.5

    # Check for partial city match
    for search_word in search_parts[:-1]:  # Exclude state
        for load_word in load_parts[:-1]:
            if len(search_word) > 3 and search_word in load_word:
                return 0.4

    return 0.0


def calculate_equipment_match(search_equip: str, load_equip: str) -> float:
    """
    Calculate equipment type match score.
    Returns score from 0.0 to 1.0
    """
    search_norm = search_equip.lower().strip()
    load_norm = load_equip.lower().strip()

    # Exact match
    if search_norm == load_norm:
        return 1.0

    # Check for key equipment types
    if "dry van" in search_norm and "dry van" in load_norm:
        return 1.0
    if "reefer" in search_norm and "reefer" in load_norm:
        return 1.0
    if "flatbed" in search_norm and "flatbed" in load_norm:
        return 1.0

    # Check for partial matches (e.g., "53ft" matches "53ft Dry Van")
    search_words = set(search_norm.split())
    load_words = set(load_norm.split())

    common_words = search_words.intersection(load_words)
    if common_words:
        match_ratio = len(common_words) / max(len(search_words), len(load_words))
        return match_ratio * 0.8  # Partial match gets lower score

    return 0.0


def calculate_date_match(search_date: str, load_pickup: str) -> float:
    """
    Calculate pickup date match score.
    Returns score from 0.0 to 1.0

    If no search date provided, return neutral score (0.7)
    """
    if not search_date:
        return 0.7  # Neutral score when date not specified

    try:
        search_dt = date_parser.parse(search_date)
        load_dt = date_parser.parse(load_pickup)

        # Calculate day difference
        day_diff = abs((load_dt - search_dt).days)

        if day_diff == 0:
            return 1.0  # Same day
        elif day_diff <= 1:
            return 0.9  # Within 1 day
        elif day_diff <= 3:
            return 0.7  # Within 3 days
        elif day_diff <= 7:
            return 0.5  # Within a week
        else:
            return 0.2  # More than a week

    except:
        return 0.7  # If parsing fails, return neutral score


def calculate_overall_match_score(
    origin_score: float,
    destination_score: float,
    equipment_score: float,
    date_score: float
) -> float:
    """
    Calculate weighted overall match score.

    Weights:
    - Origin: 30%
    - Destination: 30%
    - Equipment: 30%
    - Date: 10%
    """
    weights = {
        "origin": 0.3,
        "destination": 0.3,
        "equipment": 0.3,
        "date": 0.1
    }

    overall = (
        origin_score * weights["origin"] +
        destination_score * weights["destination"] +
        equipment_score * weights["equipment"] +
        date_score * weights["date"]
    )

    return round(overall, 2)


def search_loads(
    origin: str,
    destination: str,
    equipment_type: str,
    optional_pickup_date: str = None,
    max_results: int = 3
) -> List[Dict[str, Any]]:
    """
    Search for matching loads based on criteria.

    Returns top N loads ranked by match score.
    """
    all_loads = load_loads_database()

    if not all_loads:
        return []

    # Score each load
    scored_loads = []

    for load in all_loads:
        origin_score = calculate_location_match(origin, load["origin"])
        destination_score = calculate_location_match(destination, load["destination"])
        equipment_score = calculate_equipment_match(equipment_type, load["equipment_type"])
        date_score = calculate_date_match(optional_pickup_date, load["pickup_datetime"])

        overall_score = calculate_overall_match_score(
            origin_score,
            destination_score,
            equipment_score,
            date_score
        )

        # Only include loads with reasonable match (>0.3 overall score)
        if overall_score >= 0.3:
            load_with_score = load.copy()
            load_with_score["match_score"] = overall_score
            scored_loads.append(load_with_score)

    # Sort by match score (highest first)
    scored_loads.sort(key=lambda x: x["match_score"], reverse=True)

    # Return top N results
    return scored_loads[:max_results]
