---
id: ctx-context-development-workflow
kind: workflow
importance: 0.65
confidence: confirmed
source: CONTEXT.md#development-workflow
chunk: null
tokens_est: 76
tags: [context, development-workflow, workflow]
---

# CONTEXT.md: Development Workflow

## Summary
cd aggregator && pip install -e .

## Use when
- working on development workflow

## Key facts
- cd aggregator && pip install -e .
- uvicorn aggregator.web.app:createapp --factory --reload
- python -m pytest aggregator/tests/ -x -q
- python -m aggregator.cli scrape
- python -m aggregator.cli generate-codes --count 5

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#development-workflow`
