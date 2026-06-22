---
name: git
description: Modern Git command best practices and safety rules
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: git
---

## What I do

I provide modern, safer Git command alternatives to replace old overloaded commands that do too many things.

## When to use me

Load this skill when you need to work with Git operations to ensure you're using the safest, most explicit commands.

## Critical Safety Rules

### Branch Operations

**NEVER use `git checkout`** - This command is explicitly forbidden. Always use `git switch` instead.

- ✅ `git switch <branch>` - Use this to switch branches
- ✅ `git switch -c <branch>` - Use this to create and switch to a new branch
- ❌ `git checkout` - NEVER use this command

**Why?** `git checkout` is overloaded - it switches branches, restores files, and does other things. `git switch` is explicit and only switches branches.

### Unstaging Changes

**NEVER use `git reset` for unstaging** - Use `git restore --staged` instead.

- ✅ `git restore --staged <file>` - Unstage a specific file
- ✅ `git restore --staged .` - Unstage all changes
- ❌ `git reset` - Do NOT use for unstaging files

**Why?** `git reset` can do many dangerous things (move HEAD, unstage files, discard changes). `git restore --staged` is explicit and only unstages.

**Note:** `git reset` is still valid for moving HEAD (like `git reset --hard` or `git reset HEAD~1`), but should never be used for simple unstaging operations.

### Force Pushing

**NEVER use `git push --force`** - Use `git push --force-with-lease` instead.

- ✅ `git push --force-with-lease` - Safely force push (checks remote hasn't changed)
- ❌ `git push --force` or `git push -f` - Unsafe, can overwrite others' work

**Why?** `git push --force-with-lease` checks that the remote branch is in the expected state before force-pushing. If someone else has pushed changes since you last fetched, it will reject the push instead of silently overwriting their work.

## Quick Reference

| Old Command | New Command | Purpose |
|-------------|-------------|---------|
| `git checkout <branch>` | `git switch <branch>` | Switch branches |
| `git checkout -b <branch>` | `git switch -c <branch>` | Create and switch to new branch |
| `git checkout <file>` | `git restore <file>` | Restore file from HEAD |
| `git reset HEAD <file>` | `git restore --staged <file>` | Unstage a file |
| `git reset HEAD` | `git restore --staged .` | Unstage all files |
| `git push --force` | `git push --force-with-lease` | Force push safely |

## When the old commands are still valid

- `git reset --hard HEAD~1` - Moving HEAD is a valid use of reset
- `git reset --soft HEAD~1` - Undoing commits while keeping changes staged
- `git checkout <commit-hash>` - Detached HEAD state (though `git switch --detach` is clearer)

The key is to use the more explicit modern commands when they exist for the specific operation you're performing.
