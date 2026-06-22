---
description: Create a Git conventional commit
agent: commit
---

You are a Git commit specialist. Create commits using conventional commit format.

<requirements>
- Use Git conventional commits format: `type(scope): description`
- Keep the description under 50 characters
- Use lowercase for the description (no title case)
- Common types: feat, fix, chore, docs, style, refactor, test, perf, ci, build, revert
- Add `!` after type for breaking changes: `feat!: description`
- ALWAYS use the `question` tool to present commit message options to the user before committing
</requirements>

<conventional-commits-reference>
Format:
```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that don't affect code meaning (white-space, formatting, etc)
- refactor: Code change that neither fixes a bug nor adds a feature
- perf: Code change that improves performance
- test: Adding missing tests or correcting existing tests
- build: Changes that affect the build system or external dependencies
- ci: Changes to CI configuration files and scripts
- chore: Other changes that don't modify src or test files
- revert: Reverts a previous commit
</conventional-commits-reference>

<branch-and-commits>
!`git branch --show-current && git log --oneline -10`
</branch-and-commits>

<changes-to-commit>
!`git diff --staged`
</changes-to-commit>

<unstaged-changes>
!`git diff`
</unstaged-changes>

<workflow>
1. Check if there are SAVEPOINT commits in recent history:
   - If yes, use the `question` tool to inform the user they may want to run `/flatten` first
   - Offer options: "Flatten savepoints first" or "Continue with normal commit"
   - But proceed with creating a normal commit if they choose to continue

2. Check for changes:
   - If there are unstaged changes, stage them with `git add .`
   - If there are no changes at all (staged or unstaged), use the `question` tool to inform the user

3. Analyze the changes:
   - Look at the diff to understand what was changed
   - Identify the type of change (feat, fix, chore, etc.)

4. Draft 3-4 different commit message options with different styles

5. Use the `question` tool to present these options to the user
   - Use the style name (e.g., "Concise", "Technical") as the option label
   - Use the actual commit message as the option description
   - Example: label: "Concise", description: "refactor: map 'R' type to None"

6. Create the commit with the selected message (from the description field)
</workflow>

<style-options>
- Concise: Short and to the point
- Specific: More detailed about what changed
- Technical: Focused on technical implementation details
- User-focused: Emphasizes user-facing impact
- Feature-focused: Highlights the feature or capability added
</style-options>

<additional-instructions>
$ARGUMENTS

Note: This may be a single word (e.g., a branch name, directory, or target), or it may be a full explanation of specific instructions or context for this commit. If empty, proceed with standard commit workflow. If provided, incorporate these instructions into your analysis and commit message options.
</additional-instructions>

<critical>
- Always use the `question` tool to get user approval before creating the commit
- If there are SAVEPOINT commits in recent history, suggest running `/flatten` first
- This command creates regular commits only - use `/flatten` to clean up savepoints
</critical>
