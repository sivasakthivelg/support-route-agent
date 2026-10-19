# SupportRoute



An agent on AWS that hands one decision to **Strands Decider 2B** and the conversation to **Amazon Bedrock**. Decision pattern: `#policy`. Tags: `#strands-decider-2b` `#policy`.

- Video: (add the YouTube/Vimeo link)
- Article: (add the AWS Builder Center link)
- Deployed: run `./kit deploy`

## The project

**SupportRoute** is an AI-powered customer support routing agent. It reads a customer's
free-text message, uses Strands Decider 2B to classify it into the correct support category,
creates a ticket, and tells the customer which team will handle their request — along with a
reference number and estimated response time.

## Use case

Businesses receive support messages in plain language. Instead of making the customer pick a
department from a menu, SupportRoute reads the intent and routes automatically. This cuts
misroutes, speeds up first response, and reduces queue congestion in the wrong team's inbox.

## Who uses it

Customer support operations teams at any business that handles inbound support messages:
SaaS products, e-commerce, telecoms, banks, or any company with tiered support teams.

## The decision (Strands Decider 2B — #policy)

One `Decider.ask()` call with two typed questions:

1. **category** (choice) — billing, technical, account-access, general, or escalation
2. **urgent** (noul) — is the customer expressing urgency or strong frustration?

The decider reads the raw customer message as state. If confidence on `category` is below 0.65,
the agent asks the customer to clarify rather than misrouting.

## Features

- Natural-language routing — no menus, no dropdowns
- Five support categories with correct team names and ETAs
- Urgency detection — escalation and urgent tickets flagged immediately
- Low-confidence fallback — asks for clarification instead of guessing
- Ticket creation — every routed request gets a unique reference number
- Transparent routing — tells the customer exactly which team and when to expect a reply



## How it is built

Strands Agents with Amazon Bedrock for the generative part, the tools in `agent/tools.py`, deployed to Amazon Bedrock AgentCore Runtime, and one decision handed to Strands Decider 2B at a clear seam in the agent's path.

Every Amazon Bedrock model id is set in `.env` (`BEDROCK_MODEL_ID`, and `BEDROCK_SMALL/MEDIUM/LARGE_MODEL_ID` for routing), Amazon Nova by default.



## Reusable decision pattern: Customer Support Request Classification (#policy)

The pattern lives in [`agent/decision.py`](agent/decision.py), labelled `REUSABLE DECISION PATTERN`. It contains the typed questions and their options, the wiring that puts the decision in the agent's path, and a note on how to reuse it:

```text
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
```

Typed questions:

```python
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
```

## Measured

Decider: strands-decider-2b-hobson-v19 (ugmdu). 16 labelled cases, 32 decisions.

| | Strands Decider 2B | qwen3.5-4b |
|---|---|---|
| Accuracy | 50.0% | 50.0% |
| Latency p50 per decision | 3333 ms | 16489 ms |
| Latency p95 | 3459 ms | 16561 ms |
| Cost per 1,000 decisions | $0.0350 | $0.0000 |
| Answered alone at confidence >= 0.7 | 75% | 100% |
| Accuracy when confident | 37.5% | 50.0% |

At the median the decider was 5.0x faster than the LLM.

Reproduce with `./kit bench` (cases in `agent/eval_cases.jsonl`; charts in `submission/bench/`).

## Run it

```bash
./kit setup        # checks your machine and AWS, sets up Strands Decider 2B (local model or hosted API)
./kit demo         # web UI at http://localhost:8501
./kit bench        # the decision vs an Amazon Bedrock LLM
./kit deploy       # Amazon Bedrock AgentCore Runtime
```

Requirements: Python 3.10+, AWS credentials with Amazon Bedrock access, and for deploying, Node 20+ with the AgentCore CLI (`./kit agentcore-cli`).

## Credits

Built with the AWS User Group Madurai Strands Decider hackathon kit (https://github.com/awsugmdu). The kit's reusable library (`decider_kit/`, the demo UI, the video and article tooling, and the Kiro steering, skills and hooks) is the user group's; the agent in `agent/` is mine. Strands Decider: https://github.com/strands-labs/strands-decider (Apache-2.0).

Licence: Apache-2.0 (see LICENSE).
