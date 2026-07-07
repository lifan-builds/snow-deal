---
id: ctx-context-learned-patterns
kind: lesson
importance: 0.78
confidence: confirmed
source: CONTEXT.md#learned-patterns
chunk: null
tokens_est: 290
tags: [context, learned-patterns, lesson]
---

# CONTEXT.md: Learned Patterns

## Summary
Exclusion keyword design: space-padded " used " prevents matching "unused"/"refused". Prepend space to search string so keywords match at start: f" {name} {url}".lower().

## Use when
- avoiding repeated mistakes or applying prior corrections
- update context with durable lessons

## Key facts
- Exclusion keyword design: space-padded " used " prevents matching "unused"/"refused". Prepend space to search string so keywords match at start: f" {name} {u...
- Model name ambiguity: Single-word names like "frontier", "ultra", "hera" are too ambiguous. Must use brand-qualified multi-word entries.
- Brand fallback categorization catches accessories as hardgoods — NOTHARDGOODSKEYWORDS must be aggressively expanded.
- htmx load-more pattern: hx-target="this" on the button leaves the wrapper div. Must use hx-target="closest .load-more-wrap" with hx-swap="outerHTML".
- Headless Shopify (Hydrogen/Oxygen) stores return 404 on JSON API endpoints — must use Playwright browser scraping.

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#learned-patterns`
