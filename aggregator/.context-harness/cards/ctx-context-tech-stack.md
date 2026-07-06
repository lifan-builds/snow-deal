---
id: ctx-context-tech-stack
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#tech-stack
chunk: null
tokens_est: 220
tags: [context, tech-stack]
---

# CONTEXT.md: Tech Stack

## Summary
Language: Python 3.11+

## Use when
- working on tech stack

## Key facts
- Language: Python 3.11+
- Web framework: FastAPI >= 0.110, uvicorn >= 0.29
- Templating: Jinja2 >= 3.1, htmx 2.x (CDN, no build step)
- Database: SQLite via aiosqlite >= 0.20 for deals/reviews (path configurable via DATABASEPATH env var)
- Auth database: Turso cloud SQLite via libsql >= 0.1 (invite codes, events) — falls back to local SQLite for dev

## Open next
- `CONTEXT.md#tech-stack`
