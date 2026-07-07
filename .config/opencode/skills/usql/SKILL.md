---
name: usql
description: usql tool for connecting to and executing SQL in database connections. Use when asked to look at a specific database
---

Run `usql -Xc '\cset' | awk -F ' = ' '{print $1}'` to get named connections. Do NOT read that output directly, as there is password-sensitive information output.

Traceability and context-friendly iteration are primary concerns when making **any and all** queries:

- **ALWAYS** write input script and output to /tmp, using `usql <CONNECTION NAME> -f /tmp/opencode/usql/<date>/<purpose>.sql -o /tmp/opencode/usql/result/<date>/<iteration>/<purpose>.sql`
- **ALWAYS** ensure SQL scripts are written in a diff-friendly and easily-editable manner, for context and iterability.
