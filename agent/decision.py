"""
REUSABLE DECISION PATTERN: Customer Support Request Classification (#policy)

What it does:
    Reads a customer's free-text support message and classifies it into one of five
    support categories (billing, technical, account-access, general, escalation), while
    also detecting whether the customer is expressing urgency or frustration.

    This pattern routes inbound support requests to the correct team without requiring
    the customer to pick from a menu. It replaces fragile keyword matching with calibrated
    probability from Strands Decider 2B.

Typed questions and options:
    category (choice):
        "billing"        — Invoice, charge, payment, subscription, or refund question
        "technical"      — Bug, crash, error, app not working, or performance issue
        "account-access" — Cannot log in, password reset, 2FA, or locked account
        "general"        — Product question, how-to, feedback, or general inquiry
        "escalation"     — Customer is angry, frustrated, threatening to leave, or
                           demands urgent help

    urgent (noul):
        true  — Uses words like urgent, immediately, furious, unacceptable, or demands
                fast action
        false — Tone is neutral or politely asking for help

The wiring:
    1. Build state_text from the customer message (just the message text is enough).
    2. Call Decider.ask(state_text, QUESTIONS).
    3. Check answers["category"].confidence — if below LOW_CONFIDENCE_THRESHOLD, ask
       the customer to clarify rather than routing.
    4. Check answers["urgent"].yes for urgency flag.
    5. Route to the team and create a ticket.

How to reuse:
    Copy this file into your agent. Change the category options to match your business
    (e.g. swap "technical" for "shipping" in an e-commerce context). Keep the urgency
    noul — it works across most support domains. Adjust LOW_CONFIDENCE_THRESHOLD to suit
    your tolerance for misroutes vs. clarification requests.

    Import:
        from agent.decision import PATTERN_TAG, QUESTIONS, LOW_CONFIDENCE_THRESHOLD, SupportRouter
"""

from decider_kit import Decider

PATTERN_TAG = "#policy"

LOW_CONFIDENCE_THRESHOLD = 0.65

QUESTIONS = {
    "category": Decider.choice(
        "Which support category best matches this customer message?",
        {
            "billing":        "Customer is asking about an invoice, charge, payment, subscription cost, plan upgrade or downgrade, refund, or any question about what they are being billed for — even if they mention urgency or deadlines around the payment",
            "technical":      "Customer reports a bug, crash, error message, feature not working, data not syncing, API failure, or performance problem — even if the impact is severe or production-affecting",
            "account-access": "Customer cannot log in, needs a password reset, has 2FA problems, or their account is locked or blocked",
            "general":        "Customer has a general product question, how-to request, feature request, feedback, or the message is unclear and does not fit another category",
            "escalation":     "Customer is expressing anger, frustration, threatening to cancel or leave, demanding a manager, or saying the service is unacceptable — the primary signal is emotional tone, not the topic itself",
        },
    ),
    "urgent": Decider.noul(
        "Is the customer expressing urgency or strong frustration?",
        {
            "true":  "Customer uses words like urgent, immediately, now, furious, unacceptable, broken production, losing business, deadline today, or makes an explicit demand for immediate action",
            "false": "Customer's tone is neutral, patient, or politely asking for help without pressure",
        },
    ),
}


class SupportRouter:
    """
    Wires Strands Decider 2B into a support routing agent.

    Usage:
        router = SupportRouter()
        result = router.classify(customer_message)
        # result: {"category": str, "confidence": float, "urgent": bool,
        #          "low_confidence": bool, "decider_ms": float, "probabilities": dict}
    """

    def __init__(self):
        self._decider = Decider()

    def classify(self, message: str) -> dict:
        """
        Classify a customer message.

        Returns a dict with:
            category       — one of the five category keys
            confidence     — probability of the top category (0..1)
            urgent         — True if the customer seems urgent or frustrated
            low_confidence — True if confidence < LOW_CONFIDENCE_THRESHOLD
            decider_ms     — time the decider took in milliseconds
            probabilities  — full probability dict for all categories
        """
        state = f"Customer support message:\n{message}"
        answers = self._decider.ask(state, QUESTIONS)
        category = answers["category"].label
        confidence = answers["category"].confidence
        urgent = answers["urgent"].yes
        probabilities = {k: round(v, 3) for k, v in answers["category"].probabilities.items()}

        return {
            "category": category,
            "confidence": confidence,
            "urgent": urgent,
            "low_confidence": confidence < LOW_CONFIDENCE_THRESHOLD,
            "decider_ms": self._decider.last_latency_ms,
            "probabilities": probabilities,
        }
