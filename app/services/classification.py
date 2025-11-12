"""
Rule-based call classification service.

Classifies calls by outcome and sentiment using keyword analysis.
"""
import re
from typing import Tuple


# Keyword patterns for outcome classification
BOOKED_KEYWORDS = [
    r"\b(deal|booked|confirmed|agreed|accept|I'll take it|let's do it|sounds good|perfect|you got it)\b",
    r"\b(sign me up|count me in|works for me)\b",
]

REJECTED_KEYWORDS = [
    r"\b(no thanks|not interested|pass|can't do it|won't work|too (low|high|far))\b",
    r"\b(decline|reject|no deal)\b",
]

NEGOTIATED_KEYWORDS = [
    r"\b(think about it|call you back|let me check|need to discuss|get back to you)\b",
    r"\b(partial|maybe|considering|will review)\b",
]


# Keyword patterns for sentiment classification
POSITIVE_KEYWORDS = [
    r"\b(great|excellent|perfect|wonderful|fantastic|happy|pleased|excited)\b",
    r"\b(appreciate|thank you|thanks|love|best)\b",
    r"\b(easy|smooth|quick|simple)\b",
]

NEGATIVE_KEYWORDS = [
    r"\b(frustrated|upset|angry|disappointed|terrible|awful|horrible)\b",
    r"\b(waste|problem|issue|concern|difficult|complicated)\b",
    r"\b(not happy|unhappy|dissatisfied)\b",
]

NEUTRAL_KEYWORDS = [
    r"\b(okay|fine|alright|understood|noted)\b",
    r"\b(standard|normal|typical|regular)\b",
]


def classify_outcome(transcript: str, declared_outcome: str = None) -> Tuple[str, float]:
    """
    Classify call outcome: booked, negotiated, or rejected.

    If declared_outcome is provided, use it as a hint but verify against transcript.

    Returns:
        Tuple of (outcome, confidence)
    """
    transcript_lower = transcript.lower()

    # Count keyword matches for each outcome
    booked_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in BOOKED_KEYWORDS
    )

    rejected_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in REJECTED_KEYWORDS
    )

    negotiated_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in NEGOTIATED_KEYWORDS
    )

    # Determine outcome based on scores
    scores = {
        "booked": booked_score,
        "rejected": rejected_score,
        "negotiated": negotiated_score
    }

    # If declared outcome is provided and has some support, use it
    if declared_outcome and declared_outcome in scores and scores[declared_outcome] > 0:
        outcome = declared_outcome
        confidence = min(0.95, 0.6 + (scores[declared_outcome] * 0.1))
    else:
        # Use the highest scoring outcome
        if max(scores.values()) == 0:
            # No clear signals, default to negotiated with low confidence
            outcome = "negotiated"
            confidence = 0.3
        else:
            outcome = max(scores, key=scores.get)
            max_score = scores[outcome]
            total_score = sum(scores.values())

            # Calculate confidence based on score dominance
            if total_score > 0:
                confidence = min(0.95, 0.5 + (max_score / (total_score + 1)) * 0.4)
            else:
                confidence = 0.5

    return (outcome, round(confidence, 2))


def classify_sentiment(transcript: str) -> Tuple[str, float]:
    """
    Classify sentiment: positive, neutral, or negative.

    Returns:
        Tuple of (sentiment, confidence)
    """
    transcript_lower = transcript.lower()

    # Count keyword matches for each sentiment
    positive_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in POSITIVE_KEYWORDS
    )

    negative_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in NEGATIVE_KEYWORDS
    )

    neutral_score = sum(
        len(re.findall(pattern, transcript_lower, re.IGNORECASE))
        for pattern in NEUTRAL_KEYWORDS
    )

    # Look for additional sentiment signals
    # Exclamation marks often indicate positive sentiment
    exclamation_count = transcript.count('!')
    positive_score += exclamation_count * 0.5

    # Question marks can indicate confusion or concern
    question_count = transcript.count('?')
    if question_count > 5:  # Many questions might indicate issues
        negative_score += 0.5

    # All caps words might indicate strong emotion (could be positive or negative)
    caps_words = len(re.findall(r'\b[A-Z]{2,}\b', transcript))
    if caps_words > 2:
        # Check context - if negative keywords present, boost negative
        if negative_score > 0:
            negative_score += caps_words * 0.3

    # Determine sentiment based on scores
    scores = {
        "positive": positive_score,
        "negative": negative_score,
        "neutral": neutral_score
    }

    # Special case: if positive and negative are both high, lean neutral
    if positive_score > 0 and negative_score > 0:
        ratio = min(positive_score, negative_score) / max(positive_score, negative_score)
        if ratio > 0.6:  # Similar amounts of positive and negative
            sentiment = "neutral"
            confidence = 0.7
            return (sentiment, confidence)

    # Use the highest scoring sentiment
    if max(scores.values()) == 0:
        # No clear signals, default to neutral
        sentiment = "neutral"
        confidence = 0.6
    else:
        sentiment = max(scores, key=scores.get)
        max_score = scores[sentiment]
        total_score = sum(scores.values())

        # Calculate confidence based on score dominance
        if total_score > 0:
            confidence = min(0.95, 0.5 + (max_score / (total_score + 1)) * 0.4)
        else:
            confidence = 0.5

    return (sentiment, round(confidence, 2))


def classify_call(transcript: str, declared_outcome: str = None) -> dict:
    """
    Full classification: outcome and sentiment.

    Returns:
        Dict with outcome, sentiment, and confidence scores
    """
    outcome, outcome_confidence = classify_outcome(transcript, declared_outcome)
    sentiment, sentiment_confidence = classify_sentiment(transcript)

    # Overall confidence is average of both
    overall_confidence = (outcome_confidence + sentiment_confidence) / 2

    return {
        "outcome": outcome,
        "sentiment": sentiment,
        "confidence": round(overall_confidence, 2),
        "outcome_confidence": outcome_confidence,
        "sentiment_confidence": sentiment_confidence
    }
