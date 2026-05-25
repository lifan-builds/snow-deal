---
name: project-init-iterate
description: >
  Initialize and maintain project context documents (AGENTS.md, PLANS.md, README.md)
  following OpenAI Agents SDK conventions. Use when starting a new project, scaffolding
  a codebase, or when the user asks to update project documentation to reflect recent
  changes, decisions, or conversation context.
---

# Project Documentation Manager

A skill that generates and maintains three core project context files, giving AI agents
and human contributors the context they need to work effectively in any codebase.

| Document    | Audience           | Purpose                                      |
| ----------- | ------------------ | -------------------------------------------- |
| `AGENTS.md` | AI coding agents   | Compact instruction file for agent context   |
| `PLANS.md`  | Agents & humans    | Living execution plan tracking ongoing work  |
| `README.md` | Human contributors | Standard project README for onboarding       |

---

## 1 — Determine the Mode

Before generating anything, check for an existing `AGENTS.md` at the project root.

| Condition                        | Mode       |
| -------------------------------- | ---------- |
| No `AGENTS.md` at project root   | **Init**   |
| `AGENTS.md` already exists       | **Update** |

---

## 2 — Init Mode

Use when the user asks to **start**, **scaffold**, or **initialize** a new project.

### Step 1: Gather project context

Extract the following from the user's message and any prior conversation:

1. **Project name & purpose** — one-sentence summary
2. **Tech stack** — languages, frameworks, key libraries (with versions if known)
3. **Architecture style** — monolith, microservices, CLI tool, library, etc.
4. **Key modules / directory structure** — planned or already created
5. **Build / run / test commands** — if known
6. **Coding conventions** — style, formatting, naming, patterns

> **When to ask vs. proceed:** If items 1–3 are missing, ask the user before generating.
> If items 4–6 are missing, make reasonable assumptions and note them in the output.

### Step 2: Generate the three documents

Create all files at the **project root** (the workspace directory).

---

#### 2a — `AGENTS.md`

The primary instruction file for AI coding agents. Keep it **focused and actionable** —
agents consume this with limited context windows.

```markdown
# Agent Guide

## Project Overview
[One-paragraph description: what the project does, who it's for, core value prop.]

## Tech Stack
[List languages, frameworks, key libraries with versions if known.]

## Project Structure
[Directory tree or table of key paths with one-line descriptions.]

## Development Workflow
[Setup commands, how to run, how to test, how to build.]

## Coding Conventions
[Style rules, naming conventions, patterns to follow, things to avoid.]

## Architecture Decisions
[Key design choices and their rationale — kept as a running log.]
```

---

#### 2b — `PLANS.md`

A living execution plan document using the **ExecPlan** format from the OpenAI Agents
SDK. For a new project, create an initial plan capturing the bootstrap work.

See [templates.md](templates.md) for the full ExecPlan skeleton with
section-by-section commentary.

```markdown
# [Project Name] — Initial Bootstrap

This is a living document. Keep Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective up to date as work proceeds.

## Purpose / Big Picture
[What the user will be able to do after this bootstrap is complete.]

## Progress
- [ ] Step 1 description
- [ ] Step 2 description

## Surprises & Discoveries
(None yet.)

## Decision Log
(None yet.)

## Outcomes & Retrospective
(To be filled upon completion.)

## Context and Orientation
[Current state of the project for someone with zero prior context.]

## Plan of Work
[Prose description of what needs to happen, in sequence.]

## Validation and Acceptance
[How to verify the bootstrap succeeded.]
```

---

#### 2c — `README.md`

Standard project README for human contributors.

```markdown
# [Project Name]

[One-paragraph description.]

## Getting Started

### Prerequisites
[Runtime, tools, accounts needed.]

### Installation
[Step-by-step setup commands.]

### Usage
[How to run the project.]

## Development
[How to contribute, run tests, lint, format.]

## Project Structure
[Brief directory overview.]

## License
[License info if known, otherwise a placeholder.]
```

### Step 3: Confirm creation

After writing all three files, print a brief summary listing:
- What was created
- Any assumptions that were made
- Suggested next steps

---

## 3 — Update Mode

Use when the user asks to **update docs**, **sync docs**, or whenever significant
project changes have occurred during the conversation.

### Step 1: Read existing documents

Read all three files (`AGENTS.md`, `PLANS.md`, `README.md`) from the project root.

### Step 2: Identify what changed

Analyze the conversation history and current codebase for:

- New or removed files / directories
- New dependencies or tools
- Architectural decisions made during the conversation
- Completed or new tasks
- Changed build / run / test commands
- New conventions or patterns established

### Step 3: Update each document

| Document    | What to update                                                                                        |
| ----------- | ----------------------------------------------------------------------------------------------------- |
| `AGENTS.md` | Project Structure (new modules), Tech Stack (new deps), Architecture Decisions, Coding Conventions, Development Workflow |
| `PLANS.md`  | Check off completed Progress items, add new tasks, record Surprises & Decisions, update Outcomes if a phase completed, start a new plan section if entering a new phase |
| `README.md` | Getting Started (setup changes), Usage (new features), Project Structure (layout changes), dependency/version references |

### Step 4: Show a diff summary

After updating, briefly list what changed in each file so the user can review.

---

## 4 — Guidelines

| Guideline | Rationale |
| --------- | --------- |
| Keep `AGENTS.md` focused and actionable | AI agents have limited context windows |
| Keep `PLANS.md` as a living document | Always update Progress before ending a session |
| Keep `README.md` user-friendly | Assume the reader is a brand-new contributor |
| No speculative content | Only document what exists or has been decided |
| Consistent terminology | Use the same terms across all three documents |

## Additional Resources

- Full ExecPlan skeleton with section commentary → [templates.md](templates.md)
