---
name: pr
description: Pull request bodies, PR descriptions, Helpdesk Tickets sections, screenshots, and unrelated-change callouts. Use when drafting or rewriting a PR body so it matches the user's exact house style instead of a generic summary.
---

# PR Skill

Use this when the user asks for a PR body, PR description, or PR rewrite.

This skill exists because the user has a real PR style already. Follow that style instead of inventing one.

Observed patterns from the user's PRs:

- Usually start with `## Change Set`
- Then `### Helpdesk Tickets` or sometimes `### Helpdesk Issues`
- Each ticket is a top-level bullet with the ticket title linked directly
- Screenshots are not a standalone section; they live inside the ticket bullet as a collapsed `<details>` block
- `### Post-Merge Steps` is used for manual work like module upgrades, syncs, params, cron setup, and other manual deployment actions
- Some very small PRs use only a ticket link and nothing else

## Preferred Structure

```md
## Change Set

### Helpdesk Tickets

- [Ticket title](https://portal.dome.software/odoo/all-tickets/TICKET_ID)
  <details><summary><strong>Screenshots</strong></summary>
    <img width="1600" alt="image" src="https://github.com/user-attachments/assets/..." />
    <img width="1600" alt="image" src="https://github.com/user-attachments/assets/..." />
  </details>

  - Concrete change 1.
  - Concrete change 2.
  - Concrete change 3.

### Other Changes

- Short note about adjacent or unrelated cleanup that should not be mixed into the ticket bullets.

### Post-Merge Steps

- Update `some_module`.
- Run sync job X.
- Set config parameter Y.
```

## Exact Example

This matches the user's recent remittance PR style.

```md
### Helpdesk Tickets

- [Remittances aren't sending on production](https://portal.dome.software/odoo/all-tickets/1212)
  <details><summary><strong>Screenshots</strong></summary>
    <img width="1406" height="938" alt="image" src="https://github.com/user-attachments/assets/82fc397c-9383-4b07-8940-ad8c12abdc1b" />
    <img width="1883" height="1093" alt="image" src="https://github.com/user-attachments/assets/9cfce70d-5008-4bd9-8185-1b4f2ec542fd" />
  </details>

  - Mark `dome_remittance_email_sent` only from `mail.mail._postprocess_sent_message()` after Odoo finishes a successful send, not a successful "queue".
  - Set the vendor remittance template to `auto_delete = False` so successful remittance emails and their related message history remain inspectable in production.
  - Tag remittance-generated `mail.mail` records with internal fields so grouped remittances can mark every payment in the group after delivery.

### Post-Merge Steps

- Update `logic_core`.
```

## Other Real Variants

Small PRs can be much lighter:

```md
Ticket: https://portal.dome.software/odoo/helpdesk/5/tickets/1211
```

Some older PRs use `### Helpdesk Issues` instead of `### Helpdesk Tickets`.
Do not normalize this automatically if the user asks to match an older PR or existing wording.

## Rules

1. Prefer `## Change Set` unless the user asks for the shortest possible body.
2. Prefer `### Helpdesk Tickets` for current-style PRs.
3. Use `### Helpdesk Issues` only when matching an older style or existing PR wording.
4. Put screenshots inside the related ticket bullet, not in their own section.
5. Use the ticket title as the linked bullet text whenever possible.
6. Link directly to the actual ticket URL. Match whether it is `all-tickets`, `my-tickets`, or `helpdesk/5/tickets` if the user is intentionally mirroring an existing link style.
7. Keep the actual code changes as indented bullets under the ticket.
8. Use `### Other Changes` when there are supporting changes that should not be mixed into the helpdesk ticket bullets.
9. Use `### Post-Merge Steps` for anything manual after merge, including:
   - modules to upgrade
   - syncs to run
   - params to set
   - cron actions to enable or trigger
   - data fixes
   - user/admin actions
10. Omit `### Other Changes` if there are no such changes.
11. Omit `### Post-Merge Steps` if there are no manual steps.
12. Omit the screenshot `<details>` block if there are no screenshots.
13. Keep bullets concrete and close to the diff. Avoid vague lines like "Fix email issue".
14. Do not add generic sections like Summary, Testing, Risks, or Deployment Notes unless the user explicitly asks for them.

## Multiple Tickets

If more than one helpdesk ticket is involved, keep them as separate top-level bullets under the helpdesk section.

```md
## Change Set

### Helpdesk Tickets

- [First ticket title](https://portal.dome.software/odoo/all-tickets/1111)

  - Change 1.
  - Change 2.

- [Second ticket title](https://portal.dome.software/odoo/all-tickets/2222)

  - Change 1.
  - Change 2.

### Post-Merge Steps

- Update `first_module`.
- Update `second_module`.
```

## Tone

- Be plain.
- Be concrete.
- Prefer actual changed behavior over summary language.
- Match the user's existing PR bodies rather than trying to improve them stylistically.

## Checklist Before Returning a PR Body

1. Section names match the style the user wants for this repo and this PR.
2. Ticket URLs are correct.
3. Ticket titles match the real tickets.
4. Screenshot blocks are nested under tickets, not separated out.
5. Manual follow-up work is listed under `### Post-Merge Steps` when needed.
6. `Other Changes` only exists if there are truly non-ticket bullets worth separating.
7. Bullets describe the actual diff, not guesses.
