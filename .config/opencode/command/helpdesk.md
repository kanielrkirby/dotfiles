---
name: helpdesk
description: Solve Helpdesk tickets by ticket number from start to finish.
---

ID=$1
CLIENT=!`pwd | cut -d/ -f8`
ADDITIONAL INSTRUCTIONS=```$ARGUMENTS```

### 0) Parallel Intake

- Immediately launch the `helpdesk-intake` subagent with the EXACT message containing EXCLUSIVELY `Conduct intake for ID=$1`. Every single time.

## Workflow

### 1) Client Selection

- Map ticket to client -> [!`~/dev/wrk/odoo-env/clients/*`]
- Confirm:
  - You are in the correct client directory (or intentionally outside clients while investigating).
  - The local URL should be `https://{client}.local/odoo`.
- Read: `{client}/workspace.code-workspace` and `ls {client}/addons}` if present.

### 2) Planning

- Decide path:
  - "Repro first" (UI-driven bugs)
  - "Traceback first" (server error already provided)
- Define success criteria (what exact click/path must work).
- Identify likely areas:
  - Custom addons vs shared Odoo core/enterprise.
  - Models/methods implicated by traceback.

### 3) Diagnosis

- Use traceback to locate the failing model/method.
- Search in client addons first (`{client}/addons/**`) for overrides/compute/onchange/context keys.
- Also consult the matching shared sources:
  - `shared/odoo-{version}`
  - `shared/enterprise-{version}`

### 4) Fix

- Implement minimal, atomic, safe change.
- Avoid unnecessary comments.
- Avoid refactors unrelated to the ticket.

### 5) Verification

- Ensure server reloads Python changes (restart container/service if applicable).

### 6) Git Hygiene + Commit

- If already on a non-main/master branch, use the question tool to decide whether to continue or branch fresh.
- If branching is needed:
  - Update local `main` from `origin/main`.
  - Create new branch `hd-{ticket id}/{what-we-are-doing}`.
- Stage only relevant files.
- Use question tool to pick commit message wording; include:
  - A "what"/"why" option
  - A "user impact" option
  - A "system invariants" option (if relevant)
- Commit.

### 7) Final Chat Write-Up (Required)

- Repro steps (bullet list)
- Observed error + traceback highlights
- Root cause (1-3 bullets)
- Fix description + file(s) touched
- Verification steps + results
- Any follow-ups (e.g., deploy notes, config checks)

### 8) PR

Draft a PR in /tmp/opencode/{branch name}/pr-v{version of pr}.md. Update this regularly with updates to this branch. When you user actually asks, you can push that PR, but it has to be user prompted.
