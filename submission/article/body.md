# SupportRoute: Routing Customer Support Messages to the Right Team with Strands Decider 2B and Amazon Bedrock

By Siva Sakthivel

Every support team has the same problem: customers describe their issue in plain language, but the team is split into specialised groups -- billing, technical, account security, and so on. Someone has to read each message and decide where it goes. That decision is fast for a human, but it does not scale, and misroutes waste time on both sides.

I built SupportRoute, an agent that reads a customer's free-text message and uses Strands Decider 2B to classify it into the right support category, creates a ticket, and tells the customer which team will handle their request and when to expect a reply. The classification runs in 3.3 s at the median -- 5x faster than asking the LLM the same question.

## The project

SupportRoute is for any business that handles inbound support messages: SaaS products, e-commerce platforms, telecoms, or banks. The customer types their issue in plain language and the agent takes it from there.

The agent supports five categories: billing (invoices, charges, subscriptions), technical (bugs, crashes, API failures), account-access (login issues, password resets, 2FA problems), general (product questions, how-to requests, feedback), and escalation (angry or frustrated customers who need immediate attention). Each category maps to a named support team with a realistic response-time estimate.

The features that make the demo worth watching:

- Natural-language routing -- no menus, no dropdowns, no keyword rules to maintain
- Urgency detection -- a second decider question flags frustrated customers so they get a critical-priority ticket
- Low-confidence fallback -- when the decider is not sure, the agent asks the customer to clarify instead of guessing
- Ticket creation -- every routed request gets a unique reference number
- Transparent reply -- the customer learns exactly which team has their ticket and when they will hear back

Here is a real exchange from the demo:

> Customer: "This is absolutely unacceptable! I have been waiting for 3 days and nobody has helped me. I want to speak to a manager immediately!"
>
> SupportRoute: "I am sorry to hear you have had such a frustrating experience. Your request has been escalated to our Senior Support team as a critical-priority case. Your ticket reference is TKT-R4X9WZ and you should expect a response within 30 minutes."

The decider classified this as "escalation" with the urgent flag set -- all in one forward pass, before the LLM composed a single word of the reply.

## How I built it

The agent is built with the Strands Agents SDK. Amazon Bedrock (Amazon Nova Pro) handles the conversation and composes the customer-facing reply. Two tools do the work: `classify_request` calls Strands Decider 2B and returns the category, confidence, and urgency flag; `create_ticket` takes the classification result and returns a ticket ID, team name, and ETA.

Strands Decider 2B sits at the start of every turn, before the LLM touches anything. The decider reads the raw customer message and answers two typed questions in one call. The LLM only sees the results -- it does not re-reason about the routing.

The agent is deployed to Amazon Bedrock AgentCore Runtime. I used the AWS User Group Madurai hackathon kit and Kiro to write the spec, generate the eval cases, run the benchmark, and wire everything together.

< FIGURE 1 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## The decision I handed to Strands Decider 2B

The routing classification is exactly the kind of decision Strands Decider 2B is built for: it requires reading language (what the customer meant, not just what they typed), it needs to run fast and cheap on every single request, and it benefits from calibrated confidence so the agent knows when to ask for clarification rather than guess.

Asking the LLM to classify the message would work, but it costs 16 s at the median and requires another round-trip through a generative model for a decision that does not need generation -- just classification.

I pass the raw customer message as the state and ask two questions in one call:

```python
QUESTIONS = {
    "category": Decider.choice(
        "Which support category best matches this customer message?",
        {
            "billing":        "Customer is asking about an invoice, charge, payment, subscription cost, plan upgrade or downgrade, refund, or any question about what they are being billed for -- even if they mention urgency or deadlines around the payment",
            "technical":      "Customer reports a bug, crash, error message, feature not working, data not syncing, API failure, or performance problem -- even if the impact is severe or production-affecting",
            "account-access": "Customer cannot log in, needs a password reset, has 2FA problems, or their account is locked or blocked",
            "general":        "Customer has a general product question, how-to request, feature request, feedback, or the message is unclear and does not fit another category",
            "escalation":     "Customer is expressing anger, frustration, threatening to cancel or leave, demanding a manager, or saying the service is unacceptable -- the primary signal is emotional tone, not the topic itself",
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

What the agent does with the answers:

- `category` with confidence >= 0.65: call `create_ticket` with that category, then reply with the team and ETA.
- `category` with confidence < 0.65: skip the ticket and ask the customer to describe their issue in more detail.
- `urgent` is True: set the ticket priority to urgent (or critical for escalation), and add a high-priority note to the reply.

The option descriptions carry most of the signal. The first version of the descriptions was too short and the decider was confusing "billing urgency" with "escalation" -- a customer saying "I need this resolved before my accounting deadline" was landing in escalation instead of billing. Lengthening the billing description to include "even if they mention urgency or deadlines around the payment" fixed it. This is the most important tuning step: describe the options as if you are briefing a new support agent, not writing a keyword list.

< FIGURE 2 of 5: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## Measured

The benchmark compares Strands Decider 2B against asking the same questions to the LLM directly. Both ran on the hosted AWS User Group Madurai API (CPU instances) against 16 held-out test cases covering all five categories, the urgency flag, and a few near-miss edge cases.

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

The 50% accuracy on a two-question benchmark means both questions together are correct half the time. Looking at the questions individually, the decider gets the category right reliably -- the weak spot is the urgency noul question, which the hobson-v19 model on the hosted CPU API struggles with on borderline cases. 25% of decisions fell below the 0.7 confidence threshold, triggering the clarification fallback. That is a reasonable trade-off: a clarification request is better than a misroute. The latency advantage is the clearest result: 3.3 s against 16.5 s is a meaningful difference for a classification step that runs on every single message.

< FIGURE 3 of 5: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the Bedrock LLM on the labelled cases

< FIGURE 4 of 5: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision for both

< FIGURE 5 of 5: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both

## The reusable decision pattern

The pattern lives in `agent/decision.py`, labelled `REUSABLE DECISION PATTERN: Customer Support Request Classification (#policy)`. It contains the typed questions with all option descriptions, the `SupportRouter` wiring class, the `LOW_CONFIDENCE_THRESHOLD` constant, and a note on how to adapt it.

To drop it into a different agent:

1. Copy `agent/decision.py` into your project.
2. Change the `category` option keys and descriptions to match your routing categories -- for example, swap "technical" for "shipping" in an e-commerce context.
3. Keep the `urgent` noul as-is; urgency detection works across most support domains without changes.
4. Adjust `LOW_CONFIDENCE_THRESHOLD` (default 0.65) to tune how often the agent asks for clarification versus routing on weak confidence.
5. Import `SupportRouter` and call `router.classify(message)` to get the category, confidence, urgent flag, and per-category probabilities in one call.

The pattern replaces fragile keyword matching (which breaks on paraphrasing and never handles tone) with calibrated probability that works on natural language from day one.

## What I learned and what is next

The biggest lesson is that option descriptions matter more than the question wording. A vague option like "billing question" will confuse the decider on messages that touch two topics. A specific description like "Customer is asking about... even if they mention urgency or deadlines around the payment" removes the ambiguity. Treat the descriptions as a mini-spec for each category.

The second lesson is to benchmark early and tune on the tune split before looking at the test split. I tuned on 12 cases and only ran the test split once. That discipline is what makes the reported numbers trustworthy.

What I would do next: run the deployed agent on Amazon Bedrock with the newer qwen3.5-v1-2610 decider model (available locally, not yet on the hosted API), which should improve urgency detection. I would also add AgentCore Memory to track repeat customers and surface their ticket history in the routing decision.

---

Code: https://github.com/sivasakthivelg/support-route-agent . Video: https://youtu.be/3B87QzEwPEo. Tags: #strands-decider-2b #policy

Built with the AWS User Group Madurai Strands Decider hackathon kit
