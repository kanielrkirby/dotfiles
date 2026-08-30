---
name: create-pr
description: Tips for creating PRs. Include any time you hear "PR" or "Pull Request"
---

0. Include other relevant skills files (e.g., `dome-pr`, or others if present). These describe expected structure.
1. Write into `/tmp/opencode/pr/<%Y%m%d>/<purpose>.md`.
2. Iterate with the `question` tool, followed by relevant patches to the file, until the user is happy if they need any changes.
3. Give 3 recommendations for the PR title with `question` tool.
4. Create the PR using `gh pr --draft -F <BODY FILE> --title <TITLE>`.
