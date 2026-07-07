---
name: dome-pr
description: Dome PR Structure. Load when making PRs for a Helpdesk Ticket from the Dome Portal
---

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

## Example

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
