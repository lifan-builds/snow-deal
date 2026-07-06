---
id: ctx-context-development-workflow
kind: workflow
importance: 0.65
confidence: confirmed
source: CONTEXT.md#development-workflow
chunk: null
tokens_est: 290
tags: [context, development-workflow, workflow]
---

# CONTEXT.md: Development Workflow

## Summary
python -m venv .venv && source .venv/bin/activate

## Use when
- working on development workflow

## Key facts
- python -m venv .venv && source .venv/bin/activate
- pip install -e ..
- pip install -e ".[dev]"
- playwright install chromium
- pytest tests/ -v

## Open next
- `CONTEXT.md#development-workflow`
