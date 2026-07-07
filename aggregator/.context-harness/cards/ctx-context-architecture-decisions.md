---
id: ctx-context-architecture-decisions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#architecture-decisions
chunk: null
tokens_est: 671
tags: [context, architecture-decisions, known-data-quality-issues-as-of-2026-04-06]
---

# CONTEXT.md: Architecture Decisions

## Summary
SQLite + htmx: SQLite via aiosqlite for persistence (no re-scraping per page load). Server-rendered HTML with htmx partials for dynamic filtering — no build step.

## Use when
- working on architecture decisions

## Key facts
- SQLite + htmx: SQLite via aiosqlite for persistence (no re-scraping per page load). Server-rendered HTML with htmx partials for dynamic filtering — no build...
- Scraping: asyncio.gather with per-domain semaphores. Playwright for JS-rendered stores (anti-bot stealth). Shopify/BlueZone parsers reused from parent snowde...
- Review matching: OGL (26 categories, 0-100 scores) + TGR (7 sitemaps, qualitative→numeric). Two-pass fuzzy matching: exact (0.78 threshold) then family fallb...
- Data quality: Multi-layer pipeline — EXCLUDEKEYWORDS → URL domain stripping → keyword categorization → boot disambiguation (disambiguateboot()) → brand/model...
- Deployment: GitHub Actions scrapes every 6h, uploads deals.db as release asset. Vercel bundles the DB during deployment and serves the FastAPI app as Python...

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#architecture-decisions`
