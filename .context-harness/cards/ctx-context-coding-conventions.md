---
id: ctx-context-coding-conventions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#coding-conventions
chunk: null
tokens_est: 165
tags: [context, coding-conventions]
---

# CONTEXT.md: Coding Conventions

## Summary
Templates: Jinja2 + htmx for interactivity, no JS frameworks

## Use when
- working on coding conventions

## Key facts
- Templates: Jinja2 + htmx for interactivity, no JS frameworks
- CSS: Custom properties (CSS variables), dark theme only, Inter font
- JavaScript: Vanilla JS inline in templates, no build step
- Python: Type annotations on public functions, async/await throughout
- Categorization: Keyword-based in config.py — use space-padded keywords to avoid substring false positives (e.g., " used " not "used")

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#coding-conventions`
