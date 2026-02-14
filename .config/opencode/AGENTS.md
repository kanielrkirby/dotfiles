# Agent Guidelines for OpenCode Configuration

## Git Operations

When working with Git, load the `git` skill to ensure you're using modern, safe commands:

```
skill({ name: "git" })
```

This skill provides:
- Modern alternatives to old overloaded Git commands
- Safety rules for branch operations, unstaging, and force pushing
- Quick reference table of old vs new commands

## Working with Remote GitHub Repositories

When you need to explore or read files from remote GitHub repositories without cloning them, load the `github-explore` skill:

```
skill({ name: "github-explore" })
```

This skill provides detailed instructions on how to:
- Browse repository structure using `webfetch`
- Read individual files using `curl` with `raw.githubusercontent.com`
- Avoid common mistakes when working with remote repositories

## Database Operations

The database plugin provides tools for interacting with databases. Database credentials are stored locally and should NEVER be committed to Git.

### Configuration

Database connections are configured in `.opencode/plugins/database/config.json` with this format:

```json
{
  "defaultConnection": "local",
  "connections": {
    "local": "postgres://username:password@localhost:5432/database_name",
    "atlas": "mongodb+srv://username:password@cluster.mongodb.net/database_name"
  }
}
```

**IMPORTANT:** Always add this path to `.git/info/exclude` (NOT `.gitignore`):

```bash
echo ".opencode/plugins/database/config.json" >> .git/info/exclude
```

This keeps your database credentials local and prevents accidental commits.

### Available Tools

- `database_execute` - Execute SQL queries
- `database_list` - List available database connections
- `database_table` - Show detailed table schema
- `database_info` - Get overview of all tables

### Config Search

The plugin searches recursively upward from the current directory to the git worktree root, aggregating all found configs. Closer configs override settings from parent directories.
