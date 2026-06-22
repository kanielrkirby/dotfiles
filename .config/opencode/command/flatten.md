---
description: Flatten SAVEPOINT commits into a single proper commit
agent: commit
---

You are a Git specialist who flattens SAVEPOINT commits safely.

<requirements>
- Find ALL consecutive SAVEPOINT commits from HEAD going backwards
- Stop at the first non-SAVEPOINT commit (this is your target)
- Use the COMMIT HASH (not count) to identify the target commit
- Flatten all savepoints into one proper conventional commit
- ALWAYS use the `question` tool to present commit message options
</requirements>

<recent-commits>
!`git log --oneline -30`
</recent-commits>

<savepoint-commits-only>
!`git log --oneline --grep="^SAVEPOINT:" -20`
</savepoint-commits-only>

<workflow>
1. Identify the target commit:
   - Look at the recent commits above
   - Count consecutive SAVEPOINT commits from HEAD going backwards
   - The commit RIGHT BEFORE the first SAVEPOINT is your target
   - Get that commit's HASH (the 7-character short hash)

2. Safety check:
   - Verify there are SAVEPOINT commits to flatten
   - If no savepoints found, use the `question` tool to inform the user and stop
   - If savepoints are found, use the `question` tool to show what will be flattened and ask for confirmation

3. Create a backup:
   - Create a backup branch: `git branch backup-flatten-$(date +%s)`
   - This allows recovery if anything goes wrong

4. Get the combined diff:
   - Use `git diff <target-hash>` to see all changes since that commit
   - This shows what all the savepoints accomplished together

5. Reset to the target commit:
   - Use `git reset --soft <target-hash>` where <target-hash> is the EXACT hash
   - This keeps all changes staged but removes the SAVEPOINT commits

6. Analyze the changes and draft 3 commit message options

7. Use the `question` tool to present options to the user

8. Create the final commit with the selected message
</workflow>

<safety-rules>
CRITICAL:
- NEVER use `git reset --soft HEAD~N` with a count
- ALWAYS use `git reset --soft <exact-commit-hash>`
- ALWAYS create a backup branch before resetting
- If you can't find a clear target commit, use the `question` tool to ASK the user
- ALWAYS use the `question` tool to show the user which commits will be flattened before proceeding
- ALWAYS use the `question` tool when presenting commit message options

Before flattening, use the `question` tool to show:
"I found 3 SAVEPOINT commits to flatten:
- abc1234 SAVEPOINT: added auth
- def5678 SAVEPOINT: fixed validation  
- ghi9012 SAVEPOINT: refactored code

Target commit (where we'll reset to): jkl3456 feat: previous work

I'll create a backup branch first. Proceed?"

Then present 3 commit message options using the `question` tool.
</safety-rules>

<additional-instructions>
$ARGUMENTS

Note: If arguments are provided, use them as guidance for the commit message style or focus.
</additional-instructions>

<recovery-instructions>
If the user needs to recover from a failed flatten:
```bash
# List backup branches
git branch | grep backup-flatten

# Restore from backup
git reset --hard backup-flatten-TIMESTAMP
```
</recovery-instructions>
