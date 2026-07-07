---
id: ctx-context-workflow
kind: workflow
importance: 0.9
confidence: confirmed
source: CONTEXT.md#workflow
chunk: null
tokens_est: 95
tags: [context, workflow, verification]
---

# CONTEXT.md: Workflow

## Summary
Setup: cd aggregator && pip install -e .

## Use when
- running, testing, linting, deploying, deployment, or verifying changes

## Key facts
- Setup: cd aggregator && pip install -e .
- Run: uvicorn aggregator.web.app:createapp --factory --reload
- Test: python -m pytest aggregator/tests/ -x -q
- Run Scrape: python -m aggregator.cli scrape
- All tests pass (python -m pytest aggregator/tests/ -x -q exits 0)

## Retrieval order
- Read `NOW.md` and concise `CONTEXT.md` as the always-read layer.
- Use this card before opening bulky `PLAN.md`, chunks, or raw source sections for this topic.
- Open raw detail only when this summary is insufficient for the task.

## Open next only if needed
- `CONTEXT.md#workflow`
