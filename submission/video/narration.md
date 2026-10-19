0. SupportRoute reads a customer message and uses Strands Decider to classify it into the right support category, then creates a ticket and tells the customer which team will handle their request.


1. AI-powered customer support routing with Strands Decider. What it does: Routes customer messages to the right team automatically. Detects urgency and escalates critical cases immediately. Low-confidence fallback asks for clarification instead of misrouting. Every request gets a unique ticket reference and response-time estimate.

2. A billing message. Watch how the decider classifies the category and the agent creates a ticket for the Billing team.
 No decision was needed on this turn.

3. A technical issue. The decider picks technical support and the agent routes to the Technical Support team.
 No decision was needed on this turn.

4. An escalation. The decider detects both the escalation category and the urgent flag. The agent creates a critical-priority ticket for Senior Support.
 No decision was needed on this turn.

5. A low-confidence case. The decider is uncertain, so the agent asks the customer to clarify rather than misrouting.
 No decision was needed on this turn.

6. On 32 labelled decisions, with the decider on the AWS User Group Madurai hosted API, Strands Decider was 50% accurate at a median of 3333 milliseconds, against 50% and 16489 milliseconds for a hosted open LLM asked the same questions.

7. SupportRoute routes every customer message to the right team quickly, with calibrated confidence so it knows when to ask rather than guess.
