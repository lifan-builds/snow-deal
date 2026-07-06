---
id: ctx-context-architecture-decisions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#architecture-decisions
chunk: null
tokens_est: 279
tags: [context, architecture-decisions]
---

# CONTEXT.md: Architecture Decisions

## Summary
Invite-gated access: Controlled growth via human-readable invite codes (POWDER-SUMMIT-42). Landing page is public for SEO/marketing, deal content requires authentication.

## Use when
- working on architecture decisions

## Key facts
- Invite-gated access: Controlled growth via human-readable invite codes (POWDER-SUMMIT-42). Landing page is public for SEO/marketing, deal content requires au...
- Server-rendered with htmx: No SPA framework. Jinja2 templates + htmx partials give fast interactivity with minimal JS complexity. Cards render server-side, f...
- SQLite + Turso split: Deal data in local SQLite (fast reads, scraped every 6h). Auth/session/event data in Turso cloud DB (persistent across deploys).
- Keyword-based categorization: Products categorized by keyword matching against name/URL, with brand fallback. Not ML-based — fast, deterministic, debuggable....
- GitHub Actions scraping: Runs on cron, not on the web server. Keeps the web app stateless and fast. Scrape results committed to DB.

## Open next
- `CONTEXT.md#architecture-decisions`
