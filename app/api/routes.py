"""
FastAPI routes for all endpoints.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.api.models import (
    CarrierVerificationRequest, CarrierVerificationResponse,
    LoadSearchRequest, LoadSearchResponse, LoadDetail,
    OfferEvaluationRequest, OfferEvaluationResponse,
    CallExtractionRequest, CallExtractionResponse,
    CallClassificationRequest, CallClassificationResponse,
    CallLogsResponse, CallLogEntry
)
from app.services.verification import verify_carrier
from app.services.search import search_loads
from app.services.negotiation import evaluate_offer as eval_offer
from app.services.extraction import extract_call_data
from app.services.classification import classify_call as classify_call_data
from app.data.db import get_call_logs, get_call_stats, insert_call_log


router = APIRouter()


@router.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "HappyRobot Inbound Carrier Sales Agent",
        "version": "1.0.0"
    }


@router.post("/verify_carrier", response_model=CarrierVerificationResponse)
async def verify_carrier_endpoint(request: CarrierVerificationRequest):
    """
    Verify carrier eligibility via MC number.

    This endpoint integrates with the FMCSA API to validate carrier credentials.
    """
    try:
        eligible, carrier_name, reason = verify_carrier(request.mc_number)

        return CarrierVerificationResponse(
            eligible=eligible,
            carrier_name=carrier_name,
            reason=reason
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error verifying carrier: {str(e)}"
        )


@router.post("/search_loads", response_model=LoadSearchResponse)
async def search_loads_endpoint(request: LoadSearchRequest):
    """
    Search for matching loads based on carrier requirements.

    Returns top 3 loads ranked by match quality.
    """
    try:
        loads = search_loads(
            origin=request.origin,
            destination=request.destination,
            equipment_type=request.equipment_type,
            optional_pickup_date=request.optional_pickup_date,
            max_results=3
        )

        # Convert to Pydantic models
        load_details = [LoadDetail(**load) for load in loads]

        return LoadSearchResponse(
            status="success",
            loads=load_details,
            total_matches=len(load_details)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching loads: {str(e)}"
        )


@router.post("/evaluate_offer", response_model=OfferEvaluationResponse)
async def evaluate_offer_endpoint(request: OfferEvaluationRequest):
    """
    Evaluate a counter-offer and determine response.

    Applies pricing guardrails:
    - Floor: original_rate - 10%
    - Ceiling: original_rate + 5%
    """
    try:
        decision, suggested_rate, reason = eval_offer(
            original_rate=request.original_rate,
            counter_rate=request.counter_rate,
            load_id=request.load_id
        )

        return OfferEvaluationResponse(
            decision=decision,
            suggested_rate=suggested_rate if decision == "counter" else None,
            reason=reason
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error evaluating offer: {str(e)}"
        )


@router.post("/extract_call_data", response_model=CallExtractionResponse)
async def extract_call_data_endpoint(request: CallExtractionRequest):
    """
    Extract structured data from call transcript.

    Uses rule-based pattern matching to identify:
    - Load IDs
    - Agreed rates
    - Negotiation rounds
    - Call notes
    """
    try:
        extracted_data = extract_call_data(request.call_transcript)

        return CallExtractionResponse(
            load_id=extracted_data.get("load_id"),
            agreed_rate=extracted_data.get("agreed_rate"),
            carrier_notes=extracted_data.get("carrier_notes", ""),
            negotiation_rounds=extracted_data.get("negotiation_rounds", 0),
            call_duration_seconds=extracted_data.get("call_duration_seconds", 0)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting call data: {str(e)}"
        )


@router.post("/classify_call", response_model=CallClassificationResponse)
async def classify_call_endpoint(request: CallClassificationRequest):
    """
    Classify call outcome and sentiment.

    Outcome: booked, negotiated, rejected
    Sentiment: positive, neutral, negative
    """
    try:
        classification = classify_call_data(
            transcript=request.call_transcript,
            declared_outcome=request.outcome
        )

        return CallClassificationResponse(
            outcome=classification["outcome"],
            sentiment=classification["sentiment"],
            confidence=classification["confidence"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error classifying call: {str(e)}"
        )


@router.get("/call_logs", response_model=CallLogsResponse)
async def get_call_logs_endpoint(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    outcome: Optional[str] = None,
    limit: int = 100
):
    """
    Retrieve call logs with optional filtering.

    Query parameters:
    - start_date: ISO format (e.g., 2025-11-01)
    - end_date: ISO format
    - outcome: booked, negotiated, or rejected
    - limit: Maximum number of records (default 100)
    """
    try:
        logs = get_call_logs(
            start_date=start_date,
            end_date=end_date,
            outcome=outcome,
            limit=limit
        )

        # Convert to Pydantic models
        call_entries = [CallLogEntry(**log) for log in logs]

        return CallLogsResponse(
            total_calls=len(call_entries),
            status="success",
            calls=call_entries
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving call logs: {str(e)}"
        )


@router.get("/call_stats")
async def get_call_stats_endpoint():
    """
    Get aggregate statistics about calls.

    Includes:
    - Total call counts
    - Outcome distribution
    - Sentiment distribution
    - Average rates and negotiation rounds
    - Margin analysis
    """
    try:
        stats = get_call_stats()
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving call stats: {str(e)}"
        )


@router.post("/log_call")
async def log_call_endpoint(
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
):
    """
    Manually log a call (useful for testing and HappyRobot integration).

    This endpoint allows the HappyRobot agent to log completed calls.
    """
    try:
        call_id = insert_call_log(
            carrier_mc=carrier_mc,
            carrier_name=carrier_name,
            load_id=load_id,
            loadboard_rate=loadboard_rate,
            agreed_rate=agreed_rate,
            negotiation_rounds=negotiation_rounds,
            outcome=outcome,
            sentiment=sentiment,
            notes=notes,
            call_duration_seconds=call_duration_seconds
        )

        return {
            "status": "success",
            "call_id": call_id,
            "message": "Call logged successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error logging call: {str(e)}"
        )
