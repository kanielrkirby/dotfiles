---
name: helpdesk
description: Solve Helpdesk tickets by ticket number from start to finish.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: odoo
---

# Skill: helpdesk

Solve Odoo helpdesk tickets end-to-end from a ticket number, with strict client selection, reliable repro, and clean Git hygiene.

## Scope

- Ticket intake and reproduction using agent-browser.
- Mapping ticket to the correct client under `~/dev/wrk/odoo-env/clients/*`.
- Debugging + implementing fixes in the correct client addons + shared Odoo source.
- Verification in local instance.
- Branching + committing (no PR creation).

## Canonical URLs

- Ticket: `https://portal.dome.software/odoo/all-tickets/<id>`
- Local Odoo: `https://<client>.local/odoo`

## Hard Rules

- **Client correctness gate:** Always confirm the correct client repo before touching code.
  - If current working directory is inside a client repo but it is the wrong client: **hard interrupt** and ask the user to switch/confirm.
  - If current working directory is not inside any client repo yet: locate and select the right client first.
- **Intake is exhaustive:** Copy/collect everything useful from the ticket page (title, description, chatter, attachments, tracebacks, timestamps, affected customer/records).
- **Use the right Odoo sources:** Determine Odoo version from the client `workspace.code-workspace`, then consult:
  - `shared/odoo-<version>`
  - `shared/enterprise-<version>`
- **Avoid "massive explainer blocks" in code:** Only add comments that remain valuable long-term at the file/method scope.
- **Branching:** Only create a clean branch off `main` when needed. If already on a branch, ask user what to do.
- **Commit messages:** Use the question tool to propose 2-4 message options from different perspectives.
- **Finish with a strong chat write-up:** In chat (not a file), include repro steps, root cause, fix, verification, and any follow-up checks.

## Agent-Browser Reliability

- **Single base URL:** Pick one base URL and stick to it for the whole repro. Do not silently switch between `https://<client>.local/...` and `http://127.0.0.1:PORT/...` mid-run; it breaks session/cookies and makes the run non-deterministic.
- **If `<client>.local` does not resolve:** Apply the standard local recovery workflow automatically (do not ask the user to do it):
  - Run: `mise ssl <client>`
  - Run: `mise restart <client>`
  - Wait ~10s
  - Re-check `https://<client>.local/odoo`
  - If still broken: run `mullvad disconnect` and repeat
  - Only proceed once `https://<client>.local/odoo` loads
- **Use a fresh browser window (not just a new tab):** Start ticket reproduction in a new window to avoid interference from other tabs and reduce console noise/ambiguity.
- **Wait strategy:** Prefer `waitUntil=domcontentloaded` + short explicit timeouts. Odoo often never reaches `networkidle` due to long-polling/background requests.
- **Credentials:** Default to trying `admin` / `admin` for local `.local` environments login. Only ask the user for credentials if that fails. DO NO USE LOGIN WITH ODOO.COM.
- **Routing differences across Odoo versions:**
  - v17 and earlier: `/web#action=...` navigation
  - v18+: `/odoo/...` routes (examples: `/odoo/apps`, `/odoo/sales/<id>`)

## Workflow

### 1) Intake (Ticket Read)

- Use the `odoo` MCP to:
  - Get the user profile (no modules).
  <!-- - Get all tickets (if requested): `{ "model": "helpdesk.ticket", "domain": [["user_id", "=", MY_USER], ["stage_id.fold", "=", False]], "fields": ["id", "name", "description", "stage_id", "user_id", "partner_id", "team_id", "priority", "create_date", "write_date"], "limit": 100, "offset": 0, "order": "write_date desc" }` -->
  - Get ticket: `{ "model": "helpdesk.ticket", "domain": [["id", "=", <ticket number>]], "fields": ["id", "name", "description", "stage_id", "user_id", "partner_id", "team_id", "priority", "create_date", "write_date"], "limit": 100, "offset": 0, "order": "write_date desc" }`
  - Get comments: `{ "model": "mail.message", "domain": [ ["model", "=", "helpdesk.ticket"], ["res_id", "in", [<list of those ticket IDs>]], ["message_type", "!=", "user_notification"] ], "fields": ["id", "res_id", "body", "author_id", "create_date"], "limit": 1000, "order": "create_date desc" }`
  - Get attachments: `{ "model": "ir.attachment", "method": "search_read", "args": [ [["res_model", "=", "helpdesk.ticket"], ["res_id", "in", [TICKET_IDs]]], ["id", "name", "datas_fname", "mimetype", "res_model", "res_id", "url", "create_date"] ], "kwargs": { "order": "create_date desc" } }`
- If, for some reason, that doesn't work, or you've run into a blocker, open `https://portal.dome.software/odoo/all-tickets/<id>` in agent-browser.
- Capture:
  - Title + ticket number
  - Customer / Helpdesk Team
  - Full description
  - Full chatter timeline (relevant entries)
  - Any tracebacks/log snippets verbatim
  - Any attachments/screenshots references
- Extract:
  - Minimal repro steps
  - Expected vs actual behavior
  - Frequency + scope (one customer vs many)

### 2) Client Selection Gate (Must Happen Before Coding)

- Enumerate available clients: `~/dev/wrk/odoo-env/clients/*`.
- Map ticket -> client using customer/helpdesk team naming.
- Confirm:
  - You are in the correct client directory (or intentionally outside clients while investigating).
  - The local URL should be `https://<client>.local/odoo`.
- Optional quick context:
  - Review the client's addons list: `<client>/addons/*` (what custom modules exist).
  - Determine Odoo version from `<client>/workspace.code-workspace`.

### 3) Planning (After Intake + Client Confirmed)

- Decide path:
  - "Repro first" (UI-driven bugs)
  - "Traceback first" (server error already provided)
- Define success criteria (what exact click/path must work).
- Identify likely areas:
  - Custom addons vs shared Odoo core/enterprise.
  - Models/methods implicated by traceback.

### 4) Reproduction (Local)

- Go to `https://<client>.local/odoo`.
- Login if needed (ask user for creds if not provided).

- Reproduce with the same customer/record when possible.
- If it fails:
  - Open technical details and capture full traceback.
  - Stop and ask user if the environment differs from production assumptions.

### 5) Diagnosis

- Use traceback to locate the failing model/method.
- Search in client addons first (`<client>/addons/**`) for overrides/compute/onchange/context keys.
- Also consult the matching shared sources:
  - `shared/odoo-<version>`
  - `shared/enterprise-<version>`
- Confirm the hypothesis by tying it back to the repro.

### 6) Fix

- Implement minimal, safe change.
- Keep comments tight and durable.
- Avoid refactors unrelated to the ticket.

### 7) Verification

- Ensure server reloads Python changes (restart container/service if applicable).
- Repeat original repro steps.
- Add 1-2 adjacent sanity checks (nearby flows / another similar record).

### 8) Git Hygiene + Commit (No PR)

- If already on a branch, use the question tool to decide whether to continue or branch fresh.
- If branching is needed:
  - Update local `main` from `origin/main`.
  - Create new branch `kanielrkirby/YYYY-MM-DD`.
- Stage only relevant files.
- Use question tool to pick commit message wording; include:
  - A "what"/"why" option
  - A "user impact" option
  - A "system invariants" option (if relevant)
- Commit.

### 9) Final Chat Write-Up (Required)

- Repro steps (bullet list)
- Observed error + traceback highlights
- Root cause (1-3 bullets)
- Fix description + file(s) touched
- Verification steps + results
- Any follow-ups (e.g., deploy notes, config checks)

### If Requested To Make a Comment on a Ticket:

It will look something like this:

```json
model: "helpdesk.ticket"
method: "message_post"
kwargs: {
    "ids": [834],
    "body": "<p><strong>Bold</strong> and <em>italic</em></p><ul><li>Item</li></ul>",
    "body_is_html": true,
    "message_type": "comment",
    "subtype_xmlid": "mail.mt_note"
}
```
