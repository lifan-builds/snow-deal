---
id: ctx-context-operating-constraints
kind: constraints
importance: 0.9
confidence: confirmed
source: CONTEXT.md#operating-constraints
chunk: null
tokens_est: 145
tags: [context, operating-constraints, constraints]
---

# CONTEXT.md: Operating Constraints

## Summary
Do not commit secrets (cookies.json, .env, Turso tokens) — they're in-tree and must stay untracked.

## Use when
- before planning or editing
- checking project constraints
- update context safely

## Key facts
- Do not commit secrets (cookies.json, .env, Turso tokens) — they're in-tree and must stay untracked.
- Do not scrape without testing categorization first — mis-categorized products pollute the feed.
- Do not skip the freshness/stock checks when adding a new parser.
- Space-pad exclusion keywords (" used " not "used") to avoid substring false positives.
- Run python -m pytest aggregator/tests/ -x -q before commit.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#operating-constraints`
