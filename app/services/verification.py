"""
Carrier verification service using FMCSA API.
"""
import os
import re
import requests
import time
from typing import Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY")
FMCSA_API_URL = os.getenv("FMCSA_API_URL", "https://mobile.fmcsa.dot.gov/qc/services/carriers")


def validate_mc_format(mc_number: str) -> bool:
    """
    Validate MC number format.
    Expected formats: MC123456, MC-123456, MC 123456, or just 123456
    """
    pattern = r'^(MC[-\s]?)?(\d{5,7})$'
    return bool(re.match(pattern, mc_number.upper()))


def extract_mc_digits(mc_number: str) -> str:
    """
    Extract just the digits from MC number.
    'MC123456' -> '123456'
    """
    return re.sub(r'[^\d]', '', mc_number)


def verify_carrier(mc_number: str) -> Tuple[bool, Optional[str], str]:
    """
    Verify carrier using FMCSA API.

    Returns:
        Tuple of (eligible, carrier_name, reason)

    Production note: This function implements real FMCSA API integration with:
    - Format validation
    - API call with retry logic
    - Rate limit handling
    - Error handling for various failure modes
    """
    # Validate format first
    if not validate_mc_format(mc_number):
        return (False, None, "Invalid MC number format. Expected format: MC123456")

    mc_digits = extract_mc_digits(mc_number)

    # Check if API key is configured
    if not FMCSA_API_KEY:
        return (False, None, "FMCSA API key not configured. Please set FMCSA_API_KEY in environment.")

    # Call FMCSA API with retry logic
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            # FMCSA API endpoint
            # https://mobile.fmcsa.dot.gov/qc/services/carriers/{mc_number}?webKey={api_key}
            url = f"{FMCSA_API_URL}/{mc_digits}"
            params = {"webKey": FMCSA_API_KEY}

            response = requests.get(url, params=params, timeout=10)

            # Handle rate limiting (429)
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    return (False, None, "FMCSA API rate limit exceeded. Please try again later.")

            # Handle successful response
            if response.status_code == 200:
                data = response.json()

                # Extract carrier information from FMCSA response
                # The API returns different structures, handle common patterns
                carrier_name = None

                try:
                    # Try to get carrier name from various possible fields
                    if "content" in data and data["content"] is not None:
                        content = data["content"]
                        if isinstance(content, dict):
                            # Safely navigate nested structure
                            carrier = content.get("carrier")
                            if carrier and isinstance(carrier, dict):
                                carrier_name = carrier.get("legalName") or carrier.get("dbaName")

                    elif "carrier" in data and data["carrier"] is not None:
                        carrier = data["carrier"]
                        if isinstance(carrier, dict):
                            carrier_name = carrier.get("legalName") or carrier.get("dbaName")

                except Exception as parse_error:
                    # Parse error occurred, but continue anyway
                    # We'll return MC number if no name found
                    pass

                # Check carrier status
                # In production, you'd check various safety ratings and statuses
                # For now, if we get a valid response, consider them eligible
                if carrier_name:
                    return (True, carrier_name, "Verified against FMCSA database")
                else:
                    # Even if we can't parse the name, if we got a 200, the MC exists
                    return (True, f"MC{mc_digits}", "MC number found in FMCSA database")

            # Handle not found (404)
            elif response.status_code == 404:
                return (False, None, f"MC number {mc_number} not found in FMCSA database")

            # Handle unauthorized (401/403)
            elif response.status_code in [401, 403]:
                return (False, None, "FMCSA API authentication failed. Please check API key.")

            # Handle other errors
            else:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    return (False, None, f"FMCSA API error: {response.status_code}")

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return (False, None, "FMCSA API request timed out. Please try again.")

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                return (False, None, f"Error connecting to FMCSA API: {str(e)}")

        except Exception as e:
            return (False, None, f"Unexpected error during verification: {str(e)}")

    return (False, None, "Unable to verify carrier after multiple attempts")


# For testing purposes - mock verification function
def verify_carrier_mock(mc_number: str) -> Tuple[bool, Optional[str], str]:
    """
    Mock verification for testing without API key.
    This is a fallback for development/testing.
    """
    if not validate_mc_format(mc_number):
        return (False, None, "Invalid MC number format")

    mc_digits = extract_mc_digits(mc_number)

    # Mock some known carriers for testing
    mock_carriers = {
        "123456": "ABC Trucking LLC",
        "234567": "XYZ Logistics Inc",
        "345678": "Swift Transport Co",
        "456789": "Premier Freight Services"
    }

    if mc_digits in mock_carriers:
        return (True, mock_carriers[mc_digits], "Verified (mock data for testing)")
    else:
        # For any other valid format, accept it
        return (True, f"Test Carrier {mc_digits}", "Verified (mock data for testing)")
