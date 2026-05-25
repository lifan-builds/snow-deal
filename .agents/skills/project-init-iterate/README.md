# project-init-iterate

Generate and maintain three core project context documents — `AGENTS.md`, `PLANS.md`, and `README.md` — following [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) conventions.

## What It Generates

| Document    | Audience           | Purpose                                          |
| ----------- | ------------------ | ------------------------------------------------ |
| `AGENTS.md` | AI coding agents   | Compact project guide optimized for agent context |
| `PLANS.md`  | Agents & humans    | Living execution plan (ExecPlan format)           |
| `README.md` | Human contributors | Standard project README for onboarding            |

## Usage

Once installed, trigger the skill through your AI agent:

- **Init mode** — *"Initialize project docs"* — generates all three files from scratch
- **Update mode** — *"Update project docs"* — reads existing docs, analyzes recent changes, and updates

## Files

| File                             | Description                                       |
| -------------------------------- | ------------------------------------------------- |
| [`SKILL.md`](SKILL.md)          | Main skill instructions (read by the agent)       |
| [`templates.md`](templates.md)  | ExecPlan skeleton, filled example, and guidelines  |

## How It Works

```
User request
    │
    ▼
┌─────────────────┐
│ AGENTS.md exist? │
└────┬────────┬────┘
     │ No     │ Yes
     ▼        ▼
  Init      Update
  Mode       Mode
     │        │
     ▼        ▼
┌──────────────────────┐
│ Gather project info  │
│ from user + codebase │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ Generate / update    │
│ AGENTS.md            │
│ PLANS.md             │
│ README.md            │
└──────────┬───────────┘
           ▼
   Confirm & summarize
```
