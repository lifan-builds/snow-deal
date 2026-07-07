---
id: ctx-plan-findings
kind: plan
importance: 0.85
confidence: confirmed
source: PLAN.md#findings
chunk: null
tokens_est: 299
tags: [plan, findings]
---

# PLAN.md: Findings

## Summary
BlueZone Sports pagination shows "1 / 5" but actually has 9 pages (2026-03-13)

## Use when
- continuing the active task
- checking done criteria or decisions
- update context with task-local progress

## Key facts
- BlueZone Sports pagination shows "1 / 5" but actually has 9 pages (2026-03-13)
- " used " keyword with space padding avoids matching "unused"/"refused" — critical for exclusion keywords (2026-04-07)
- Single-word model names like "frontier", "ultra", "hera" are too ambiguous. Must use brand-qualified multi-word entries. (2026-04-07)
- Brand fallback categorization catches accessories as hardgoods — NOTHARDGOODSKEYWORDS must be aggressively expanded. (2026-04-07)
- htmx hx-target="this" on load-more button leaves the wrapper div. Must use hx-target="closest .load-more-wrap" with hx-swap="outerHTML". (2026-04-07)

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `PLAN.md#findings`
