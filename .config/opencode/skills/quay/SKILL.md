---
name: quay
description: Use ONLY when asked to manage Nix flakes, quay manifests, dev shells, or repo-local file syncs like .quay.toml.
---

# Quay

Use `quay` for the global declarative registry workflow.

## Default flow

- `quay <name>` resolves the named flake entry.
- Bare `quay` with no name resolves the closest configured directory under the current working directory.
- Resolution order is `develop`, then `shell`, then `run`.
- `quay develop <name>` uses the `develop` field directly.
- `quay shell <name>` uses the `shell` field directly.
- `quay run <name> [args...]` uses the `run` field directly.

## Editing

- `quay add <name>` opens `$EDITOR` with a template in `~/.config/quay/quay.toml`.
- `quay update <name>` opens `$EDITOR` with the existing entry in `~/.config/quay/quay.toml`.
- `--file <path>` can seed the entry from a TOML file.
- `--stdin` can seed the entry from standard input.

## Sync

- `quay sync <name>` applies the named sync profile.
- Sync profiles live in `~/.config/quay/quay.toml`.
- Each sync profile should declare a `source = "/path/to/project"` field.
- Flake entries can set `sync = "profile-name"` to run that sync automatically before `quay <name>` launches.
- Flake entries should set `directories = ["/path/to/project"]` so bare `quay` can resolve by directory, and can list more than one directory.
- `QUAY_SYNC_DIR` points at the synced output directory.
- Prefer copying sensitive files like `.env` unless the user explicitly wants symlinks.

## Expectations

- Use the CLI in `~/dev/lab/quay` when the user asks for Quay work.
- Do not invent a separate MCP or slash command layer.
- Keep changes declarative and minimal.
