# SupportRoute — Requirements

## Overview
SupportRoute is an AI-powered customer support routing agent. It reads a customer's message,
uses Strands Decider 2B to classify it into the correct support category, creates a ticket,
and tells the customer which team will handle them along with a reference number.

## Users
Customer-facing support teams at any business. Customers type their issue in natural language.

## Functional Requirements

1. The agent accepts a free-text customer message.
2. The agent uses Strands Decider 2B (`#policy` pattern) to classify the message into one of:
   - **billing** — invoices, charges, payments, subscriptions
   - **technical** — bugs, crashes, errors, performance issues
   - **account-access** — login problems, password resets, 2FA, locked accounts
   - **general** — product questions, how-to, feedback, other
   - **escalation** — angry/frustrated customers, threats to leave, urgent issues
3. The decider also determines urgency (yes/no noul question).
4. The agent creates a support ticket with: category, priority (urgent/normal), and a reference ID.
5. The agent replies to the customer with: the team they've been routed to, their ticket reference,
   and an estimated response time per category.
6. When decider confidence is below 0.65, the agent asks the customer to clarify their issue.
7. Escalation-category or urgent tickets get a higher-priority note in the response.

## Non-Functional Requirements

- Every LLM call goes through the Strands Agents SDK (`decider_kit.llm`).
- The decision uses exactly one `Decider.ask()` call with two questions.
- Data is synthetic (no real APIs required).
- The agent must pass `./kit test` and `./kit run`.
