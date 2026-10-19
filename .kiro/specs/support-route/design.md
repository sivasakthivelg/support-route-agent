# SupportRoute — Design

## Architecture

```
Customer message
      │
      ▼
 HackathonAgent.chat()
      │
      ├─► Strands Agent (qwen3.5-4b / Nova Pro on deploy)
      │         │
      │         ├─► classify_request tool   ← calls Decider.ask() [policy pattern]
      │         │       questions: category (choice), urgent (noul)
      │         │
      │         └─► create_ticket tool      ← returns ticket_id, team, eta
      │
      ▼
  reply to customer: "Your request has been routed to <team>. Ticket: <ref>. ETA: <eta>."
```

## Decision Pattern: `#policy`

File: `agent/decision.py`

```python
PATTERN_TAG = "#policy"

answers = decider.ask(state, {
    "category": Decider.choice("Which support category best matches this customer message?", {
        "billing":        "Invoice, charge, payment, subscription, refund question",
        "technical":      "Bug, crash, error, app not working, performance issue",
        "account-access": "Cannot log in, password reset, 2FA, locked account",
        "general":        "Product question, how-to, feedback, general inquiry",
        "escalation":     "Customer is angry, frustrated, threatening to leave, or demands urgent help",
    }),
    "urgent": Decider.noul("Is the customer expressing urgency or strong frustration?", {
        "true":  "Uses words like urgent, immediately, furious, unacceptable, or demands fast action",
        "false": "Tone is neutral or politely asking for help",
    }),
})
```

Low confidence (<0.65 on category): agent asks for clarification instead of routing.

## Tools

| Tool | Purpose |
|---|---|
| `classify_request(message)` | Calls the decider, returns category, confidence, urgent flag |
| `create_ticket(category, urgent, summary)` | Returns ticket_id, team name, ETA string |

## Data

`agent/data/tickets.json` — 30 synthetic past tickets (used by eval cases and demo)
`agent/data/teams.json`   — team names, ETAs, contact info per category

## Eval Cases

28+ cases in `agent/eval_cases.jsonl`:
- 16 test split, 12 tune split
- Covers all 5 categories + low-confidence edge cases + urgent flag

## Response Time Estimates (synthetic)

| Category | Team | ETA |
|---|---|---|
| billing | Billing & Payments | within 4 hours |
| technical | Technical Support | within 2 hours |
| account-access | Account Security | within 1 hour |
| general | Customer Success | within 24 hours |
| escalation | Senior Support | within 30 minutes |
