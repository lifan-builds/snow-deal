# Agent instructions

Use the repository-local Trellis workflow and specifications.

1. Run `python3 ./.trellis/scripts/get_context.py` at session start.
2. Follow `.trellis/workflow.md` and the active task artifacts.
3. Load `.trellis/spec/deal/index.md` before planning or editing product code.
4. Preserve `PLAN.md` and `aggregator/PLANS.md` as product planning/history records.
5. Never read, stage, mutate, or publish ignored credentials, browser state, deploy state, or database files during generic validation.

<!-- TRELLIS:START -->
# Trellis Instructions

These instructions are for AI assistants working in this project.

This project is managed by Trellis. The working knowledge you need lives under `.trellis/`:

- `.trellis/workflow.md` — development phases, when to create tasks, skill routing
- `.trellis/spec/` — package- and layer-scoped coding guidelines (read before writing code in a given layer)
- `.trellis/workspace/` — per-developer journals and session traces
- `.trellis/tasks/` — active and archived tasks (PRDs, research, jsonl context)

If a Trellis command is available on your platform (e.g. `/trellis:finish-work`, `/trellis:continue`), prefer it over manual steps. Not every platform exposes every command.

If you're using Codex or another agent-capable tool, additional project-scoped helpers may live in:
- `.agents/skills/` — reusable Trellis skills
- `.codex/agents/` — optional custom subagents

Managed by Trellis. Edits outside this block are preserved; edits inside may be overwritten by a future `trellis update`.

<!-- TRELLIS:END -->
