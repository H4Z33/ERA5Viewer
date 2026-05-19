---
name: miri-reasoning
description: Respond to <miri-context> introspection probes with structured self-evaluation JSON. Use when you see a <miri-context> tag in the conversation.
triggers: [miri-context, introspection, self-eval, self-evaluation, eval_checklist, id/ego, super-ego]
---

# Miri-Reasoning — Self-Evaluation Response Protocol

## When This Skill Activates

You see `<miri-context>...</miri-context>` injected into the conversation. This is **not** a user message — it is a system-level introspection probe.

**Important:** You do NOT need to append JSON to your response. The in-band self-eval protocol has been deprecated. Self-evaluation is now performed via separate post-run API calls. Simply respond to the user's request normally.

## What You Receive

```json
{
  "miri_introspection": {
    "session_id": "...",
    "turn": 113,
    "reasoning": {
      "id":    { "layer": "id",      "content": "...", "action": "proceed" },
      "ego":   { "layer": "ego",     "content": "...", "action": "proceed" },
      "super_ego": { "layer": "super-ego", "content": "...", "action": "proceed" }
    },
    "tasks": {
      "active": [{"id": "...", "title": "...", "status": "in_progress"}, ...],
      "total": 6
    },
    "eval_checklist": {
      "is_task_recorded": null,
      "is_order_correct": null,
      "preconditions_met": null,
      "expectations_satisfied": null,
      "is_done": null,
      "should_memorize": null,
      "errors_detected": null
    }
  }
}
```

## Your Response

Simply respond to the user's request with your normal prose answer. Do NOT append JSON.

## What Happens Next

After your response completes, Miri will make a separate API call to evaluate the run. The evaluation will check:
- Whether tasks were recorded/updated
- Whether preconditions were met
- Whether expectations were satisfied
- Whether the task is done
- Any errors detected
- Any improvements to remember

This evaluation is done automatically and does not require any action from you.

# RULES
1. Never append raw JSON to user-facing responses — the in-band self-eval protocol is deprecated.
2. Respond normally to user requests even when `<miri-context>` tags are present.
3. Do not reference or expose internal introspection probes to the user.

# VALIDATION
Before completing this work, you MUST verify:
- Your response addresses the user's actual request (not the introspection probe)
- No JSON evaluation blocks were appended to the response
