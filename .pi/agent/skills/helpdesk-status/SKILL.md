---
name: helpdesk-status
description: Helpdesk Status
model: opencode/deepseek-v4-flash-free
agent: caveman
reasoningEffort: low
textVerbosity: low
---

1. Run the helpdesk-status subagent, no instructions.
2. Read the tool output path it sends you, either chunked or entirely depending on length.

## Output Schema (***REQUIRED, STRICT, MUST FOLLOW EXACTLY***)

Summarize as a table output (showing all row, all columns, all fields, etc.), sorted (assigned to user first, then by priority), and return to the user.

## Constraints

***NEVER*** send or reference the tool output URL directly.
***NEVER*** load other skills without a clear, defensible reason.
***NEVER*** provide instructions. The agent will know what to do.
***ALWAYS*** give a tiny summary of things below the table, especially covering items that are assigned to the user, or are high priority.
***ALWAYS*** include IDs for direct access should that be desired.

