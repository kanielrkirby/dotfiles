---
name: odoo-mcp
description: Odoo MCP Knowledge.article read/write examples. Use when reading or editing Knowledge documents through Odoo MCP tools, especially `knowledge.article` records.
---

# Odoo MCP

Use this skill for Odoo Knowledge documents exposed through Odoo MCP.

## Read Knowledge

Read a single article:

```json
{
  "model": "knowledge.article",
  "record_id": 99,
  "fields": ["id", "name", "body", "last_edition_uid", "last_edition_date"]
}
```

Search for articles:

```json
{
  "model": "knowledge.article",
  "domain": [["root_article_id", "=", 47]],
  "fields": ["id", "name", "body"],
  "limit": 10,
  "offset": 0,
  "order": "write_date desc"
}
```

## Write Knowledge

Prefer a small, explicit body update. Typical Odoo Knowledge content is HTML, not Markdown.

When editing an existing article, read the current `body` first, then rewrite the full HTML body with your change inserted in the right place. Do not assume a partial patch will preserve formatting.

Preview first:

```json
{
  "model": "knowledge.article",
  "operation": "write",
  "record_ids": [99],
  "values": {
    "body": "<h1>Test doc</h1><p>Knowledge write test.</p>"
  }
}
```

Validate, then execute the approved write:

```json
{
  "approval": {
    "model": "knowledge.article",
    "operation": "write",
    "record_ids": [99],
    "values": {
      "body": "<h1>Test doc</h1><p>Knowledge write test.</p>"
    },
    "context": {},
    "token": "odoo-write:..."
  },
  "confirm": true
}
```

## Notes

- Knowledge bodies are usually stored as HTML fragments.
- Common tags include `h1`, `p`, `ul`, `ol`, `li`, `table`, and `pre`.
- Newlines are usually represented by HTML structure, not Markdown.
