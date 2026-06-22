---
name: github-explore
description: Explore and read files from remote GitHub repositories without cloning or using API keys
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: github
---

## What I do

I help you explore and read files from remote GitHub repositories without:
- Cloning the entire repository
- Using the GitHub API (no API key required)
- Dealing with rate limits

## When to use me

Use this skill when you need to:
- Browse a remote GitHub repository's file structure
- Read specific files from a GitHub repository
- Explore code without downloading the entire repo
- Work with public GitHub repositories

## How to browse repository structure

To see the file tree and repository structure, use `webfetch`:

```bash
webfetch https://github.com/owner/repo
```

This shows you:
- The full file and directory listing
- Available branches and tags
- Repository metadata

**Example:**
```bash
webfetch https://github.com/anomalyco/opencode
```

## How to read individual files

To read the raw content of a specific file, use `curl` with `raw.githubusercontent.com`:

**Format:**
```bash
curl -s "https://raw.githubusercontent.com/OWNER/REPO/BRANCH/PATH"
```

**Examples:**

Read README from main branch:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/main/README.md"
```

Read from dev branch:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/README.md"
```

Read a nested file:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/web/src/content/docs/index.mdx"
```

Read configuration file:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/package.json"
```

## Important notes

- **Always specify the branch**: main, dev, master, etc.
- **Use the full path**: Path from repository root to the file
- **Domain**: Use `raw.githubusercontent.com`, NOT `github.com`
- **Silent mode**: Use `-s` flag with curl for cleaner output
- **Public repos only**: This method works for public repositories without authentication

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

## Common mistakes to avoid

- ❌ Don't use `github.com` for file content - it returns HTML
- ❌ Don't forget to specify the branch
- ❌ Don't use relative paths - always use full path from repo root
- ✅ Do use `raw.githubusercontent.com` for file content
- ✅ Do use `webfetch github.com/owner/repo` for browsing structure
- ✅ Do specify the branch (main, dev, master, etc.)

## Example: Complete exploration

Let's explore the OpenCode repository:

1. Browse structure:
```bash
webfetch https://github.com/anomalyco/opencode
```

2. Read the main README:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/README.md"
```

3. Read package.json:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/package.json"
```

4. Read a nested file:
```bash
curl -s "https://raw.githubusercontent.com/anomalyco/opencode/dev/packages/console/package.json"
```
