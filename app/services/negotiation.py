"""
Negotiation evaluation service with pricing guardrails.
"""
from typing import Tuple


# Negotiation guardrails as percentages
FLOOR_PERCENTAGE = 0.10  # Can go 10% below loadboard rate
CEILING_PERCENTAGE = 0.05  # Can go 5% above loadboard rate


def evaluate_offer(
    original_rate: float,
    counter_rate: float,
    load_id: str
) -> Tuple[str, float, str]:
    """
    Evaluate a counter-offer and decide how to respond.

    Guardrails:
    - Floor: original_rate - 10% (company won't go below this)
    - Ceiling: original_rate + 5% (give carrier some negotiating room)

    Returns:
        Tuple of (decision, suggested_rate, reason)
        decision: "accept", "counter", or "reject"
    """
    # Calculate boundaries
    floor_rate = original_rate * (1 - FLOOR_PERCENTAGE)
    ceiling_rate = original_rate * (1 + CEILING_PERCENTAGE)

    # Case 1: Counter-offer is above original rate (carrier wants more)
    if counter_rate > original_rate:
        if counter_rate <= ceiling_rate:
            # Within acceptable range above original rate
            return (
                "accept",
                counter_rate,
                f"Your offer of ${counter_rate:.2f} is acceptable. We can work with that rate."
            )
        else:
            # Too high, above our ceiling
            return (
                "reject",
                original_rate,
                f"I understand you're looking for ${counter_rate:.2f}, but that's above our maximum budget. "
                f"Our best rate for this load is ${original_rate:.2f}. Can you work with that?"
            )

    # Case 2: Counter-offer equals original rate (carrier accepts)
    elif counter_rate == original_rate:
        return (
            "accept",
            counter_rate,
            f"Perfect! We have a deal at ${counter_rate:.2f}."
        )

    # Case 3: Counter-offer is below original rate (carrier wants less, or negotiating down)
    else:
        # Calculate how far below the original rate
        difference = original_rate - counter_rate
        percent_below = (difference / original_rate) * 100

        # If they're at or above our floor, accept immediately
        if counter_rate >= floor_rate:
            return (
                "accept",
                counter_rate,
                f"We can meet you at ${counter_rate:.2f}. That works for us."
            )

        # If they're below our floor, try to negotiate up
        else:
            # Calculate how far below the floor they are
            shortfall = floor_rate - counter_rate
            percent_below_floor = ((original_rate - floor_rate) / original_rate) * 100

            # Offer our floor rate as a counter
            return (
                "counter",
                floor_rate,
                f"I appreciate your offer of ${counter_rate:.2f}, but that's below our minimum for this load. "
                f"The best I can do is ${floor_rate:.2f}. That's {percent_below_floor:.0f}% off the board rate. "
                f"Can we make that work?"
            )


def check_negotiation_limit(negotiation_rounds: int, max_rounds: int = 3) -> Tuple[bool, str]:
    """
    Check if negotiation has reached the maximum number of rounds.

    Returns:
        Tuple of (should_end, message)
    """
    if negotiation_rounds >= max_rounds:
        return (
            True,
            "We've gone back and forth a few times. Let me connect you with my manager "
            "to see if we can find a solution that works for both of us."
        )

    return (False, "")


def get_negotiation_strategy(negotiation_round: int) -> str:
    """
    Get the appropriate negotiation strategy based on round number.

    Round 1: Be flexible, meet in the middle
    Round 2: Hold firmer, explain value
    Round 3: Final offer, escalate if needed
    """
    strategies = {
        1: "flexible",      # Be accommodating, build rapport
        2: "moderate",      # Hold ground, but show willingness
        3: "firm"          # Final offer, ready to escalate
    }

    return strategies.get(negotiation_round, "firm")
