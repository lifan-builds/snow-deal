---
id: ctx-context-tech-stack
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#tech-stack
chunk: null
tokens_est: 186
tags: [context, tech-stack, web-aggregator-primary-aggregator, tampermonkey-userscript-secondary-tampermonkey, python-cli-secondary-snow-deals]
---

# CONTEXT.md: Tech Stack

## Summary
Backend: Python 3.12, FastAPI, aiosqlite

## Use when
- working on tech stack

## Key facts
- Backend: Python 3.12, FastAPI, aiosqlite
- Frontend: Jinja2 templates, htmx 2.0.4, vanilla JS, custom CSS (dark theme)
- Database: SQLite (deals), Turso cloud (auth/sessions/events)
- Auth: JWT-based invite codes, rate limiting
- Deployment: Vercel Python Functions for the primary site; Docker on Render retained as fallback

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#tech-stack`
