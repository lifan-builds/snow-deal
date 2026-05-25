# ExecPlan Templates

Use these templates when generating or updating `PLANS.md`.

---

## Skeleton Template

Adapt the section content to your specific project, but **keep all section headings
present** — even if a section starts as "(None yet.)".

```markdown
# <Short, action-oriented title>

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must stay up to date as work proceeds.

## Purpose / Big Picture
<!-- WHY: Explain the user-visible behavior gained after this change and how to observe it. -->

## Progress
<!-- WHAT: Chronological log of completed and pending steps. -->
- [x] (YYYY-MM-DD HH:MMZ) Example completed step.
- [ ] Example incomplete step.

## Surprises & Discoveries
<!-- Anything unexpected encountered during work. -->
- Observation: …
  Evidence: …

## Decision Log
<!-- Record every non-trivial decision so future readers understand the reasoning. -->
- Decision: …
  Rationale: …
  Date/Author: …

## Outcomes & Retrospective
<!-- Fill in when the plan (or a phase of it) completes. -->
Summarize outcomes, gaps, and lessons learned; compare to the original purpose.

## Context and Orientation
<!-- WHO/WHERE: Describe the current state as if the reader has zero context.
     Name key files and modules by full path; define non-obvious terms. -->

## Plan of Work
<!-- HOW: Prose description of the sequence of edits and additions.
     For each edit, name the file, location, and what to change. -->

## Concrete Steps
<!-- Exact commands to run (with working directory).
     Include short expected outputs so the reader can verify each step. -->

## Validation and Acceptance
<!-- DONE-WHEN: Behavioral acceptance criteria plus test commands and expected results. -->

## Idempotence and Recovery
<!-- SAFETY: How to retry or roll back safely; ensure steps can be rerun without harm. -->

## Artifacts and Notes
<!-- Reference material: concise transcripts, diffs, or code snippets as indented examples. -->

## Interfaces and Dependencies
<!-- CONTRACT: Libraries, modules, and function signatures that must exist at the end.
     Use stable names and paths. -->
```

---

## Filled Example

Below is a condensed example of a completed ExecPlan for reference.

```markdown
# Add dark-mode toggle to settings page

This ExecPlan is a living document.

## Purpose / Big Picture
Users will be able to toggle between light and dark themes from Settings → Appearance.
The preference persists in localStorage and applies immediately without a page reload.

## Progress
- [x] (2025-01-10 14:30Z) Created ThemeContext provider in src/contexts/theme.tsx
- [x] (2025-01-10 15:00Z) Added DarkModeToggle component in src/components/settings/
- [x] (2025-01-10 16:20Z) Integrated toggle into SettingsPage
- [x] (2025-01-10 17:00Z) Added CSS custom properties for dark palette
- [x] (2025-01-10 17:30Z) Wrote unit tests for ThemeContext

## Surprises & Discoveries
- Observation: Safari requires `color-scheme: dark` on `<html>` for native form controls.
  Evidence: form inputs stayed light-themed without it.

## Decision Log
- Decision: Use CSS custom properties instead of a CSS-in-JS theme object.
  Rationale: Avoids runtime overhead; works with existing vanilla CSS codebase.
  Date/Author: 2025-01-10 / @dev

## Outcomes & Retrospective
All acceptance criteria met. Toggle works across Chrome, Firefox, and Safari.
Lesson: test native form controls separately when implementing dark mode.

## Context and Orientation
The app uses React 18 with vanilla CSS (no CSS-in-JS). Global styles live in
src/styles/globals.css. Settings page is at src/pages/SettingsPage.tsx.

## Plan of Work
1. Create a React context (ThemeContext) that reads/writes `theme` in localStorage.
2. Build a toggle switch component that consumes ThemeContext.
3. Add CSS custom properties scoped to `[data-theme="dark"]` on the root element.
4. Mount the toggle in the Settings page under a new "Appearance" section.

## Validation and Acceptance
- Toggle switches theme immediately — no reload required.
- Preference survives browser restart.
- `npm test -- --grep Theme` passes.
```

---

## Guidelines

| Guideline | Details |
| --------- | ------- |
| **Self-contained** | Define every term, include needed repo knowledge, avoid assuming external links are accessible |
| **Outcome-focused** | Describe what the user can *do* after the change, not just what code was written |
| **Living document** | Revise Progress, Surprises, Decision Log, and Outcomes as work proceeds — never leave them stale |
| **Milestones tell a story** | Each milestone covers: goal → work → result → proof, and is independently verifiable |
| **Formatting** | Use blank lines after headings; prefer prose over lists except in Progress |

### Do's and Don'ts

| ✅ Do | ❌ Don't |
| ----- | -------- |
| Update Progress after every meaningful step | Leave completed items unchecked |
| Record decisions immediately with rationale | Defer decision logging to "later" |
| Write Surprises as Observation + Evidence pairs | Write vague notes like "had issues" |
| Keep Concrete Steps copy-pasteable | Assume the reader knows the working directory |
| Fill Outcomes when a phase ends | Leave Outcomes blank after completion |
