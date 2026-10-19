"""
SupportRoute tools — classify_request and create_ticket.

These are the two Strands @tool functions the agent uses.
classify_request calls the decider; create_ticket creates a synthetic ticket.
_decision_log is populated by classify_request so agent.py can include
decider results in the chat() return value.
"""

import json
import random
import string
from pathlib import Path

from strands import tool

from agent.decision import SupportRouter

# Load synthetic team data once at import time
_DATA_DIR = Path(__file__).parent / "data"
with open(_DATA_DIR / "teams.json") as f:
    _TEAMS: dict = json.load(f)

_router = SupportRouter()

# Populated by classify_request on each call; cleared by agent.py before each turn
_decision_log: list[dict] = []


def get_last_decisions() -> list[dict]:
    """Return the decision log from the most recent agent turn."""
    return list(_decision_log)


def _random_ticket_id() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TKT-{suffix}"


@tool
def classify_request(message: str) -> dict:
    """
    Classify a customer support message using Strands Decider 2B.

    Reads the customer's free-text message and returns the support category
    (billing, technical, account-access, general, or escalation), a confidence
    score, and whether the message expresses urgency or frustration.

    Use this tool first for every new customer message before creating a ticket.

    Args:
        message: The customer's support message in plain text.

    Returns:
        A dict with keys: category, confidence, urgent, low_confidence,
        decider_ms, probabilities.
    """
    result = _router.classify(message)
    _decision_log.append({
        "probabilities": result["probabilities"],
        "verdict": result["category"],
        "decider_ms": result["decider_ms"],
    })
    return result


@tool
def create_ticket(category: str, urgent: bool, summary: str) -> dict:
    """
    Create a support ticket and return the team assignment and ticket reference.

    Use this tool after classify_request has returned a category with sufficient
    confidence (low_confidence is False). Pass the category and urgency from the
    classifier result.

    Args:
        category: One of billing, technical, account-access, general, escalation.
        urgent:   True if the customer is expressing urgency or frustration.
        summary:  A one-line summary of the customer's issue (10 words or less).

    Returns:
        A dict with: ticket_id, team, eta, priority.
    """
    # Treat urgent tickets in any category as escalation-priority
    if urgent and category != "escalation":
        priority = "urgent"
    elif category == "escalation":
        priority = "critical"
    else:
        priority = "normal"

    team_info = _TEAMS.get(category, _TEAMS["general"])
    ticket_id = _random_ticket_id()

    return {
        "ticket_id": ticket_id,
        "team": team_info["team"],
        "eta": team_info["eta"],
        "priority": priority,
        "category": category,
        "summary": summary,
    }
