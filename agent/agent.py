"""
SupportRoute — HackathonAgent

Routes customer support messages to the right team using Strands Decider 2B
for policy classification, then creates a ticket and replies with the team
assignment and reference number.
"""

import time
from typing import Optional

from strands import Agent

from decider_kit.llm import agent_model
from agent.tools import classify_request, create_ticket, get_last_decisions

NAME = "SupportRoute"

_SYSTEM_PROMPT = """\
You are SupportRoute, a customer support routing assistant.

Your job:
1. Call classify_request with the customer's message.
2. If low_confidence is True: reply to the customer asking them to describe their
   issue in more detail — do NOT call create_ticket.
3. If low_confidence is False: call create_ticket with the category, urgent flag,
   and a short one-line summary of the issue (10 words max).
4. Reply to the customer with:
   - Which team will handle their request (team name from create_ticket)
   - Their ticket reference number
   - The estimated response time (eta)
   - If priority is urgent or critical: add a note that their case is flagged
     as high-priority and will be handled as soon as possible

Keep your reply friendly, concise, and reassuring. One short paragraph is enough.
Do not ask the customer anything further — just confirm the routing and ticket.
"""


class HackathonAgent:
    """
    SupportRoute agent.

    chat(message, session_id="default") -> dict with keys:
        reply        — the agent's response to the customer
        decisions    — list of dicts, one per Decider call:
                       {probabilities, verdict, decider_ms}
        model_id     — the model used
        latency_ms   — total time for the chat() call
    """

    def __init__(
        self,
        eager: Optional[bool] = None,
        decider=None,
        model_id: Optional[str] = None,
    ):
        self._model = agent_model(model_id=model_id)
        self._agent = Agent(
            model=self._model,
            system_prompt=_SYSTEM_PROMPT,
            tools=[classify_request, create_ticket],
        )
        # If a fake decider is injected (tests), swap the router's decider
        if decider is not None:
            import agent.tools as _tools
            _tools._router._decider = decider

    def chat(self, message: str, session_id: str = "default") -> dict:
        t0 = time.time()

        # Reset decision capture list before each turn
        import agent.tools as _tools
        _tools._decision_log.clear()

        response = self._agent(message)
        reply = str(response)

        latency_ms = round((time.time() - t0) * 1000)

        model_id = getattr(self._model, "model_id", None) or getattr(
            self._model, "_model_id", "unknown"
        )

        decisions = list(_tools._decision_log)

        return {
            "reply": reply,
            "decisions": decisions,
            "model_id": str(model_id),
            "latency_ms": latency_ms,
        }
