---
name: odoo-env-tasks
description: Get basic information about odoo-env directories. Auto-load when under odoo-env/ directory.
---

## Valuable Information

- Project information (version): `odoo-env/clients/{client}/workspace.code-workspace`
- Odoo source: `odoo-env/shared/odoo-{version}`
- Enterprise source: `odoo-env/shared/enterprise-{version}`
  - Note: Odoo and Enterprise source _is_ editable, but this should _not_ be used as a final solution, only an occasional debugging step when inheritance is difficult.
- Business logic often goes in `logic_core`. Only rule is never put data (CSVs, not sync logic) in logic_core.

