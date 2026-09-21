# jevkit — Python client for the Jev decision model

> ⚠️ **Disclaimer**: This is a third-party, unofficial wrapper around OpenRouter's
> Decisions API — not affiliated with, endorsed by, or maintained by OpenRouter or
> TypeSafe. The API is in alpha and may change without notice.

The first open-source third-party client for OpenRouter's **Decisions API**
(Jev, by TypeSafe) — a calibrated-probability decision model, not a chat model.

> Jev answers typed questions with calibrated probabilities — zero text generation.
> Three primitives: **noul** (yes/no calibrated probability), **choice** (pick one),
> **score** (scale rating). 70-500ms latency, output tokens free.

## Why

Chat models guess; Jev **calibrates**. If you need routing, classification, or
gating decisions ("is this worth doing?"), a chat model wrapped in JSON is
slower, uncalibrated, and costs more. Jev is the ultimate classifier:

- **Calibrated probabilities** — real confidence, not vibes
- **70-500ms** — System-1 speed for gating decisions
- **$0.042/M input, output free** — 14 questions ≈ $0.00004
- **Typed questions** — noul / choice / score, with explicit criteria

## Install

```bash
pip install jevkit   # (after publish — for now: copy the jevkit/ directory)
export OPENROUTER_API_KEY=<your key>   # free from openrouter.ai
```

## Quickstart

```python
from jevkit import Client, gate

client = Client()  # reads OPENROUTER_API_KEY

# noul — yes/no calibrated probability
p = client.noul(
    name="worth_outreach",
    instructions="Is this lead worth cold outreach?",
    criteria={
        "false": "No budget, or the poster is promoting themselves.",
        "true": "Explicit budget + concrete need, reachable for a pitch.",
    },
    state="HN post: [Hiring] N8n automation expert, $2k budget, urgent",
)
# → 0.63

# gate — confidence-gated decision (act / confirm / escalate)
action = gate(p)   # confirm (borderline — flips, don't auto-send)

# choice — pick one from options
r = client.decide({
    "category": {
        "type": "choice",
        "instructions": "What does the customer need?",
        "options": ["coding", "design", "content", "infra"],
    }
}, state="I need someone to build a checkout flow")
# → {"choice": "coding", "confidence": 0.8, ...}
```


# score — scale rating
r = client.decide({
    "urgency": {
        "type": "score",
        "instructions": "How urgent is this?",
        "legend": {
            "0": "Can wait",
            "1": "This week",
            "2": "Blocking revenue now",
        },
    }
}, state="Payments are failing for customers right now")
# → {"confidence": 0.99, "legend": {...}, ...}

## CLI

```bash
jevkit noul "worth outreach?" --state "lead: ..."      # → 0.61
jevkit gate 0.63                                        # → confirm
jevkit decide questions.json --state "..."              # → full answers
```

## Gotchas (learned the hard way)

1. `questions` expects a **record** (`{name: {...}}`), not an array
2. noul's `criteria` is `{"true": str, "false": str}` — descriptions, not options
3. The response is `answers.{name}.noul` — not a top-level probability
4. **Borderline probabilities flip** — never auto-act on 0.5-0.7, gate them
5. noul(false) + noul(true) don't have to sum to 1

## The gate pattern

```python
from jevkit import gate

p = client.noul(...)          # System 1: calibrated fast decision
action = gate(p)              # act(>=0.7) / confirm(0.5-0.7) / escalate(<0.5)
if action == "act":           # only auto-act on high confidence
    do_the_thing()
elif action == "confirm":
    queue_for_review()        # borderline → human or System 2 (LLM review)
```


Default thresholds: `act >= 0.7`, `confirm >= 0.5` — tuned for the "borderline
flips" property (never auto-act in 0.5-0.7). Override per use case:

```python
gate(p, act=0.8, confirm=0.6)   # stricter gate
```

System 1 (Jev) decides **who/what to act on**; System 2 (a chat model) handles
**the acting itself** (writing, reasoning). This division keeps costs low and
decisions calibrated.

## Status

- ✅ Client + CLI + gate pattern (validated with real API calls, R3 read-back)
- ✅ Error handling: RuntimeError on HTTP errors (fallback-friendly)
- 🚧 Tests + CI (in progress)

## License

MIT
