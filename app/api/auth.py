"""
API Key Authentication for FastAPI endpoints.

Provides secure header-based API key validation for all endpoints.
"""
from fastapi import Header, HTTPException, status
import os


async def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")):
    """
    Validate API key from X-API-Key header.

    Args:
        x_api_key: API key provided in X-API-Key header

    Returns:
        bool: True if authentication succeeds

    Raises:
        HTTPException: 401 if API key is invalid or missing
        HTTPException: 500 if API key not configured on server
    """
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server. Please contact administrator."
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please provide a valid X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    return True
