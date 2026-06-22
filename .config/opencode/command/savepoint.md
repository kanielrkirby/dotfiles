---
description: Create a savepoint commit for work in progress
agent: build
---

Create a quick savepoint commit to track the current state of work.

<requirements>
- ALWAYS prefix the commit message with `SAVEPOINT:`
- Keep the message brief and descriptive
- Stage all current changes before committing
- Do NOT use the question tool (savepoints are automatic)
</requirements>

<current-status>
!`git status --short`
</current-status>

<workflow>
1. Stage all changes: `git add .`
2. Create a commit with format: `SAVEPOINT: <brief description>`
3. Confirm the savepoint was created
</workflow>

<message-format>
The commit message should follow this format:
```
SAVEPOINT: <brief description of what changed>
```

Examples:
- `SAVEPOINT: added user authentication logic`
- `SAVEPOINT: fixed validation bug in form`
- `SAVEPOINT: refactored database queries`
</message-format>

<additional-instructions>
$ARGUMENTS

Note: If arguments are provided, use them as the savepoint description. Otherwise, analyze the changes and create an appropriate description.
</additional-instructions>
