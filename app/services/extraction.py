"""
Rule-based call data extraction service.

Extracts structured information from call transcripts using pattern matching.
"""
import re
from typing import Optional, Dict, Any


def extract_load_id(transcript: str) -> Optional[str]:
    """
    Extract load ID from transcript.
    Patterns: LD001, LD-001, Load 001, Load ID 001, etc.
    """
    patterns = [
        r'LD[-\s]?(\d{3,4})',  # LD001, LD-001, LD 001
        r'[Ll]oad\s+[ID#]*\s*(\d{3,4})',  # Load 001, Load ID 001
        r'[Ll]oad\s+[Nn]umber\s*[:]*\s*(\d{3,4})',  # Load number: 001
    ]

    for pattern in patterns:
        match = re.search(pattern, transcript)
        if match:
            load_num = match.group(1)
            return f"LD{load_num.zfill(3)}"  # Standardize to LD001 format

    return None


def extract_rates(transcript: str) -> Dict[str, Optional[float]]:
    """
    Extract rates from transcript.
    Returns dict with 'original_rate', 'agreed_rate', 'counter_offers'
    """
    # Pattern for currency amounts: $2500, $2,500, 2500 dollars, etc.
    rate_patterns = [
        r'\$\s*([\d,]+\.?\d*)',  # $2500, $2,500.00
        r'([\d,]+)\s*dollars?',  # 2500 dollars
        r'rate\s+of\s+\$?\s*([\d,]+\.?\d*)',  # rate of $2500
    ]

    all_rates = []

    for pattern in rate_patterns:
        matches = re.findall(pattern, transcript, re.IGNORECASE)
        for match in matches:
            # Clean up the match (remove commas)
            rate_str = match.replace(',', '')
            try:
                rate = float(rate_str)
                # Only include rates that look reasonable for freight (200-10000)
                if 200 <= rate <= 10000:
                    all_rates.append(rate)
            except ValueError:
                continue

    # Remove duplicates while preserving order
    unique_rates = []
    for rate in all_rates:
        if rate not in unique_rates:
            unique_rates.append(rate)

    result = {
        "original_rate": unique_rates[0] if len(unique_rates) > 0 else None,
        "agreed_rate": unique_rates[-1] if len(unique_rates) > 0 else None,
        "counter_offers": unique_rates[1:-1] if len(unique_rates) > 2 else []
    }

    return result


def extract_mc_number(transcript: str) -> Optional[str]:
    """
    Extract MC number from transcript.
    """
    patterns = [
        r'MC[-\s]?(\d{5,7})',  # MC123456, MC-123456, MC 123456
        r'[Mm]otor\s+[Cc]arrier\s+[Nn]umber\s*[:]*\s*(\d{5,7})',
    ]

    for pattern in patterns:
        match = re.search(pattern, transcript)
        if match:
            return f"MC{match.group(1)}"

    return None


def count_negotiation_rounds(transcript: str) -> int:
    """
    Count the number of negotiation back-and-forths in the transcript.
    Look for patterns like: "what about", "can you do", "how about", "counter offer"
    """
    negotiation_phrases = [
        r'[Ww]hat\s+about',
        r'[Cc]an\s+you\s+do',
        r'[Hh]ow\s+about',
        r'[Cc]ounter',
        r'[Bb]est\s+(price|rate)',
        r'[Mm]eet\s+(me\s+)?in\s+the\s+middle',
        r'[Ll]ower',
        r'[Hh]igher',
    ]

    count = 0
    for phrase in negotiation_phrases:
        matches = re.findall(phrase, transcript, re.IGNORECASE)
        count += len(matches)

    # Each pair of back-and-forth counts as one round
    # Estimate: every 2 negotiation phrases = 1 round
    rounds = max(1, count // 2) if count > 0 else 0

    return rounds


def extract_carrier_notes(transcript: str, max_length: int = 500) -> str:
    """
    Extract key notes and summary from the call.
    Focus on carrier's requirements, concerns, and agreements.
    """
    notes_patterns = [
        # Look for agreement patterns
        (r"(I'll take it|[Aa]gree|[Dd]eal|[Ss]ounds good|[Ww]orks for me)", "Carrier agreed."),
        (r"([Nn]ot interested|[Nn]o thanks|[Pp]ass|[Cc]an't do it)", "Carrier declined."),
        (r"([Ll]et me\s+(think|check)|[Cc]all\s+back)", "Carrier needs time to decide."),

        # Look for requirements
        (r"([Nn]eed\s+by|[Dd]eadline|[Mm]ust\s+deliver)", "Has specific delivery requirements."),
        (r"([Ee]quipment|[Tt]ruck|[Tt]railer)", "Discussed equipment needs."),

        # Look for concerns
        (r"([Tt]oo\s+(low|high|far|heavy))", "Had concerns about load details."),
        (r"([Dd]etours|[Dd]ead\s*head|[Rr]eturn\s+load)", "Concerned about backhaul/deadhead."),
    ]

    notes = []

    for pattern, note in notes_patterns:
        if re.search(pattern, transcript, re.IGNORECASE):
            notes.append(note)

    # If no specific patterns found, create a generic note
    if not notes:
        # Try to extract any quoted text as notes
        quotes = re.findall(r'"([^"]+)"', transcript)
        if quotes:
            notes.append(f"Carrier said: {quotes[0][:100]}")

    # Combine notes
    combined_notes = " ".join(notes)

    # Truncate if too long
    if len(combined_notes) > max_length:
        combined_notes = combined_notes[:max_length - 3] + "..."

    return combined_notes if combined_notes else "No specific notes captured."


def estimate_call_duration(transcript: str) -> int:
    """
    Estimate call duration in seconds based on transcript length.
    Rough estimate: ~150 words per minute of speech, ~3 chars per word
    """
    char_count = len(transcript)
    words_estimate = char_count / 5  # Rough estimate: 5 chars per word on average
    minutes = words_estimate / 150
    seconds = int(minutes * 60)

    # Reasonable bounds: 60 seconds minimum, 1800 seconds (30 min) maximum
    return max(60, min(seconds, 1800))


def extract_call_data(transcript: str) -> Dict[str, Any]:
    """
    Main extraction function that pulls all structured data from transcript.
    """
    rates = extract_rates(transcript)

    return {
        "load_id": extract_load_id(transcript),
        "agreed_rate": rates["agreed_rate"],
        "original_rate": rates["original_rate"],
        "carrier_notes": extract_carrier_notes(transcript),
        "negotiation_rounds": count_negotiation_rounds(transcript),
        "call_duration_seconds": estimate_call_duration(transcript),
        "mc_number": extract_mc_number(transcript)
    }
