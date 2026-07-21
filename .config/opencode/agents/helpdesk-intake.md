---
description: Dome Portal Helpdesk Ticket Intake
mode: subagent
model: opencode/deepseek-v4-flash-free
agent: caveman
permission:
  edit: deny
---

- On the `dome` connection of `odoo` MCP:
`odoo_get_odoo_profile [include_modules=false, module_limit=1]`
`{ "model": "helpdesk.ticket", "domain": [["id", "=", {ticket number}]], "fields": ["id", "name", "description", "stage_id", "user_id", "partner_id", "team_id", "priority", "create_date", "write_date"], "limit": 100, "offset": 0, "order": "write_date desc" }`
`{ "model": "mail.message", "domain": [ ["model", "=", "helpdesk.ticket"], ["res_id", "in", [{list of those ticket IDs}]], ["message_type", "!=", "user_notification"] ], "fields": ["id", "res_id", "body", "author_id", "create_date"], "limit": 1000, "order": "create_date desc" }`
`{ "model": "ir.attachment", "method": "search_read", "args": [ [["res_model", "=", "helpdesk.ticket"], ["res_id", "in", [TICKET_IDs]]], ["id", "name", "mimetype", "res_model", "res_id", "url", "create_date"] ], "kwargs": { "order": "create_date desc" } }`

Then return ONLY an intake summary.
