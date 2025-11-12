"""
Pydantic models for API request and response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== Verification Endpoint ====================

class CarrierVerificationRequest(BaseModel):
    mc_number: str = Field(..., description="Motor Carrier number (e.g., MC123456)")


class CarrierVerificationResponse(BaseModel):
    eligible: bool = Field(..., description="Whether carrier is eligible")
    carrier_name: Optional[str] = Field(None, description="Carrier business name")
    reason: str = Field(..., description="Explanation of eligibility status")


# ==================== Load Search Endpoint ====================

class LoadSearchRequest(BaseModel):
    origin: str = Field(..., description="Origin city, state (e.g., 'Los Angeles, CA')")
    destination: str = Field(..., description="Destination city, state")
    equipment_type: str = Field(..., description="Equipment type (e.g., '53ft Dry Van')")
    optional_pickup_date: Optional[str] = Field(None, description="Preferred pickup date (ISO format)")


class LoadDetail(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: str
    delivery_datetime: str
    equipment_type: str
    loadboard_rate: float
    weight: int
    commodity_type: str
    notes: str
    miles: int
    match_score: float = Field(..., description="Match quality score (0-1)")


class LoadSearchResponse(BaseModel):
    status: str = Field(default="success")
    loads: List[LoadDetail] = Field(..., description="Top matching loads")
    total_matches: int = Field(..., description="Total number of matches found")


# ==================== Negotiation Evaluation Endpoint ====================

class OfferEvaluationRequest(BaseModel):
    original_rate: float = Field(..., description="Original loadboard rate")
    counter_rate: float = Field(..., description="Carrier's counter offer")
    load_id: str = Field(..., description="Load ID being negotiated")


class OfferEvaluationResponse(BaseModel):
    decision: str = Field(..., description="accept, counter, or reject")
    suggested_rate: Optional[float] = Field(None, description="Suggested counter rate if decision is 'counter'")
    reason: str = Field(..., description="Explanation of decision")


# ==================== Call Data Extraction Endpoint ====================

class CallExtractionRequest(BaseModel):
    call_transcript: str = Field(..., description="Full transcript of the call")


class CallExtractionResponse(BaseModel):
    load_id: Optional[str] = Field(None, description="Load ID discussed")
    agreed_rate: Optional[float] = Field(None, description="Final agreed rate")
    carrier_notes: str = Field(default="", description="Notes from the call")
    negotiation_rounds: int = Field(default=0, description="Number of negotiation rounds")
    call_duration_seconds: int = Field(default=0, description="Call duration")


# ==================== Call Classification Endpoint ====================

class CallClassificationRequest(BaseModel):
    call_transcript: str = Field(..., description="Full call transcript")
    outcome: str = Field(..., description="booked, negotiated, or rejected")


class CallClassificationResponse(BaseModel):
    outcome: str = Field(..., description="Call outcome classification")
    sentiment: str = Field(..., description="positive, neutral, or negative")
    confidence: float = Field(default=0.0, description="Classification confidence (0-1)")


# ==================== Call Logs Endpoint ====================

class CallLogEntry(BaseModel):
    call_id: str
    carrier_mc: str
    carrier_name: Optional[str]
    timestamp: str
    load_id: Optional[str]
    loadboard_rate: Optional[float]
    agreed_rate: Optional[float]
    negotiation_rounds: int
    outcome: str
    sentiment: str
    notes: Optional[str]
    call_duration_seconds: int


class CallLogsResponse(BaseModel):
    total_calls: int = Field(..., description="Total number of calls matching filter")
    status: str = Field(default="success")
    calls: List[CallLogEntry] = Field(..., description="List of call log entries")
