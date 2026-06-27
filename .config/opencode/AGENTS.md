# Agent Guidelines for OpenCode Configuration

## Helpdesk Tickets

When provided with a ticket number (e.g., #123) or information about a "ticket", load the `helpdesk` skill.

```
skill({ name: "helpdesk" })
```

This skill provides:
- The standard workflow for solving Helpdesk Tickets.
- Useful tips for using the `agent-browser` MCP.
- Sources for useful context and information related to the current project or ticket.

## Git Operations

When working with Git, load the `git` skill to ensure you're using modern, safe commands:

```
skill({ name: "git" })
```

This skill provides:
- Modern alternatives to old overloaded Git commands
- Safety rules for branch operations, unstaging, and force pushing
- Quick reference table of old vs new commands

## Pull Requests for `odoo-env` Repos

When drafting, rewriting, or reviewing PR bodies for repositories under `~/dev/wrk/odoo-env/`, load the `pr` skill:

```
skill({ name: "pr" })
```

This skill provides:
- The user's actual PR body structure for Odoo/helpdesk work.
- Exact section patterns like `Helpdesk Tickets`, nested screenshot blocks, and `Post-Merge Steps`.
- Guidance on when to use lighter one-line ticket bodies versus full change-set PR descriptions.

## Working with Remote GitHub Repositories

When you need to explore or read files from remote GitHub repositories without cloning them, load the `github-explore` skill:

```
skill({ name: "github-explore" })
```

This skill provides detailed instructions on how to:
- Browse repository structure using `webfetch`
- Read individual files using `curl` with `raw.githubusercontent.com`
- Avoid common mistakes when working with remote repositories

## Quay / Nix Flakes

When a task is about Nix flakes, dev shells, flake-backed commands, or repo-local sync manifests like `.quay.toml`, load the `quay` skill and prefer using the `quay` CLI from `~/dev/lab/quay` rather than inventing a new workflow.

## Database Operations

`usql` can be run using `nix run nixpkgs#usql`. There are named database connections that you'll have access to, and can query using `nix run nixpkgs#usql -Xc '\cset' | awk -F ' = ' '{print $1}'`. Do NOT read directly, it MUST pass through the `awk`.

Then you can use it by writing to `/tmp/{some-name}.sql` and running `nix run nixpkgs#usql <CONNECTION NAME> -f /tmp/<FILE> -o /tmp/<OUTPUT FILE>`. Output files are useful for limiting context.

## System

You are running on NixOS. That means that common or expected packages may not exist, but almost ALWAYS exist in `nixpkgs`. Prefer running through flake syntax, i.e., `nix shell nixpkgs#something`, NOT `nix-shell -p something`.

---

## Knowledge Policy (CURRENTLY INACTIVE, DO NOT USE AT ALL)

### Source Responsibilities

| Source           | Purpose                                             |
| ---------------- | --------------------------------------------------- |
| Mem0             | User preferences, habits, standards, workflow rules |
| Graphiti         | Durable project knowledge and relationships         |
| Filesystem / Git | Current implementation truth                        |
| Model Knowledge  | Last resort only                                    |

---

### Mem0

Mem0 stores **how the user prefers to work**.

Query Mem0 before:

* Writing code
* Refactoring
* Architecture/design decisions
* Tool selection
* Documentation
* Commit messages
* PR descriptions
* Planning
* Any task involving style, tradeoffs, or judgment

Retrieve:

* coding preferences
* architecture preferences
* workflow preferences
* tool preferences
* communication preferences

Use Mem0 for:

* coding style
* type safety preferences
* testing preferences
* documentation style
* workflow constraints
* recurring user dislikes
* cross-project operating rules

**DO NOT** use Mem0 for:

* project facts
* architecture facts
* repo structure
* implementation details
* tickets
* issues
* dependency graphs
* temporary task state

Store memories only when a preference is durable and likely to matter again.

---

### Graphiti

Graphiti is the default source of truth for durable project knowledge.

Always:

* Query Graphiti before making claims about architecture, dependencies, decisions, ownership, timelines, risks, migrations, or cross-document relationships.
* Prefer Graphiti over manually searching files for project-structure questions.
* Ingest high-signal sources only.
* Before any Graphiti query, if the group is not already known, run Neo4j directly to discover distinct `group_id` values, then query the relevant Graphiti group(s) instead of assuming `main` or a default scope.
* Use this command to discover groups when needed:

  ```bash
  docker exec graphiti-neo4j-1 cypher-shell --non-interactive --format plain -u neo4j -p demodemo -d neo4j "MATCH (n) WHERE n.group_id IS NOT NULL RETURN DISTINCT n.group_id AS group_id ORDER BY group_id;"
  ```
* If the local Graphiti stack or Neo4j container is unavailable, say so and ask the user for the group ID.

Use Graphiti for:

* architecture
* dependencies
* ownership
* decisions
* ADRs
* migrations
* timelines
* project history
* risk analysis
* cross-document relationships

**DO NOT**:

* dump entire repositories
* ingest generated files
* ingest build artifacts
* ingest large logs
* invent project structure not supported by Graphiti or source files
* create extra namespaces, routing schemes, or group IDs unless explicitly requested

When Graphiti lacks information, say so.

Do not guess.

---

### Filesystem & Git

Filesystem and Git are the source of truth for implementation details.

Use them for:

* code behavior
* repository structure
* current APIs
* tests
* configuration
* recent changes
* commit history

For implementation questions:

1. Check files/Git.
2. Use Graphiti only for surrounding context.

---

### Query Rules

#### Preference Question

Examples:

* How should this be structured?
* Which approach should we use?
* How should I document this?

→ Query Mem0.

#### Project Knowledge Question

Examples:

* Why does this exist?
* What depends on this?
* What changed?
* What are the risks?

→ Query Graphiti.

#### Implementation Question

Examples:

* Where is this implemented?
* How does this function work?
* Which file owns this logic?

→ Query Filesystem/Git.

#### Mixed Question

Examples:

* Design a solution for this project.
* Plan a migration.
* Write a PR.

→ Query Mem0 and Graphiti.
→ Verify implementation details in files.

---

### Conflict Resolution

Priority:

1. Current user instruction
2. Filesystem / Git
3. Graphiti
4. Mem0
5. Model knowledge

User instructions always override memory.

Project facts override preferences.

Never invent missing information.

State uncertainty explicitly.

---

### Non-Negotiables

**DO NOT** treat Mem0 as a project database.

**DO NOT** treat Graphiti as personal memory.

**DO NOT** answer architecture questions without consulting Graphiti when available.

**DO NOT** answer preference-heavy questions without consulting Mem0 when available.

**DO NOT** guess when authoritative sources exist.
