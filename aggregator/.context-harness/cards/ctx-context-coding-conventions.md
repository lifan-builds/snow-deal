---
id: ctx-context-coding-conventions
kind: context
importance: 0.65
confidence: confirmed
source: CONTEXT.md#coding-conventions
chunk: null
tokens_est: 702
tags: [context, coding-conventions]
---

# CONTEXT.md: Coding Conventions

## Summary
Async throughout: All I/O (HTTP, SQLite, Playwright) uses async/await.

## Use when
- working on coding conventions

## Key facts
- Async throughout: All I/O (HTTP, SQLite, Playwright) uses async/await.
- Dataclasses for models: AggregatedDeal wraps snowdeals.Product with store/category/sizes metadata.
- Parser inheritance: New HTML parsers inherit BaseParser from snowdeals.parsers.base.
- Dynamic parser registry: scraper.py uses PARSERREGISTRY dict with lazy imports via importlib.
- Rate limiting: Per-domain semaphores in scraper.py to avoid hammering retailers.

## Open next
- `CONTEXT.md#coding-conventions`
