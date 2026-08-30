---
name: git
description: Modern Git command best practices and safety rules. Use anytime you need to use the local `git` CLI.
---

## Critical Safety Rules

### Branch Operations

**NEVER use `git checkout`** - This command is explicitly forbidden. Always use `git switch` instead.

### Unstaging Changes

**NEVER use `git reset` for unstaging** - Use `git restore --staged` instead.

**Note:** `git reset` is still valid for moving HEAD (like `git reset --hard` or `git reset HEAD~1`), but should never be used for simple unstaging operations.

### Force Pushing

**NEVER use `git push --force`** - Use `git push --force-with-lease` instead.
