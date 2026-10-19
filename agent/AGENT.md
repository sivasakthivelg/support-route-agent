# SupportRoute

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
