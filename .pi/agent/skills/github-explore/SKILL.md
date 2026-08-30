---
name: github-explore
description: Explore and read files from remote GitHub repositories. Use anytime you need remote information without cloning.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: github
---

## How to browse repository structure

To see the file tree and repository structure, use `webfetch`:

```bash
webfetch https://github.com/owner/repo
```

This shows you:
- The full file and directory listing
- Available branches and tags
- Repository metadata

## How to read individual files

To read the raw content of a specific file, use `curl` with `raw.githubusercontent.com`:

**Format:**
```bash
curl -s "https://raw.githubusercontent.com/OWNER/REPO/BRANCH/FILEPATH"
```

## Recommended workflow

1. **First, browse the repository structure** to understand the layout:
   ```bash
   webfetch https://github.com/owner/repo
   ```

2. **Identify the files you need** from the file tree

3. **Read specific files** using curl:
   ```bash
   curl -s "https://raw.githubusercontent.com/owner/repo/branch/path/to/file"
   ```
