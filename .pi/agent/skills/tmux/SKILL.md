---
name: tmux
description: Control interactive terminal work through tmux using the single isolated socket /tmp/opencode/tmux.sock. Use for any task that benefits from persistent terminal sessions, interactive CLIs, long-running commands, REPLs, debuggers, or revisiting command output. Create and manage namespaced tmux sessions and windows, send commands and control keys, capture pane contents, and preserve sessions for later review. Never use the default tmux socket, another socket path, or additional panes.
---

# tmux

Use tmux as the persistent terminal interface for interactive or long-running command-line work.

## Non-negotiable isolation

- Always use exactly this socket:
  ```bash
  /tmp/opencode/tmux.sock
  ```
- Include `-S /tmp/opencode/tmux.sock` in every tmux command.
- Never use the default tmux socket.
- Never use `-L`, a different `-S` path, or an environment-selected socket.
- Create `/tmp/opencode` before the first tmux command when necessary:
  ```bash
  mkdir -p /tmp/opencode
  ```
- Before creating a session, inspect existing sessions on this socket and reuse the relevant namespace when continuing related work:
  ```bash
  tmux -S /tmp/opencode/tmux.sock list-sessions
  ```
  Treat “no server running” as an empty socket, not an error requiring a different socket.

## Session namespaces and names

Create one random namespace for a related body of work:

```text
<random-animal>-<random-numbers>
```

Examples:

```text
otter-4821
ibis-90735
```

Name each session in that body of work by appending a concise purpose slug:

```text
<namespace>-<purpose>
```

Examples:

```text
otter-4821-airtite
otter-4821-turnerseed
```

Rules:

- Choose a simple lowercase animal name and a random numeric string.
- Keep the same namespace for sessions belonging to the same user task or project.
- Use a short lowercase purpose slug containing only letters, digits, and hyphens.
- Check existing session names before creation and avoid collisions.
- Do not use vendor, model, or agent names in session names.
- Do not rename an existing session unless the user requests it.

Create a session with one initial window:

```bash
tmux -S /tmp/opencode/tmux.sock new-session -d -s "$SESSION"
```

## Windows only; never create panes

- Use tmux windows as separate work areas.
- Never run `split-window`, `select-pane`, `break-pane`, `join-pane`, or any command that creates or rearranges multiple panes.
- Keep exactly one pane per window.
- Create a new window when another independent terminal context is useful:
  ```bash
  tmux -S /tmp/opencode/tmux.sock new-window -t "$SESSION"
  ```
- Do not assign custom window names by default. Let tmux reflect the foreground process or shell.
- Target windows as `<session>:<window-index>.0`.
- List windows before targeting when the index is uncertain:
  ```bash
  tmux -S /tmp/opencode/tmux.sock list-windows -t "$SESSION"
  ```
- Close an unnecessary window when it no longer helps review, but keep the session itself open:
  ```bash
  tmux -S /tmp/opencode/tmux.sock kill-window -t "$SESSION:<window-index>"
  ```
- Never close the final window merely to tidy up, because that destroys the session.

## Run commands

Prefer literal input so shell metacharacters are delivered exactly:

```bash
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" -l -- "$COMMAND"
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" Enter
```

Use tmux key names for control input:

```bash
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" C-c
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" C-d
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" Escape
```

For a fresh shell command, capture the pane first when state matters. Avoid blindly sending input into an unknown interactive program.

When starting Python interactively, set `PYTHON_BASIC_REPL=1`:

```bash
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" -l -- 'PYTHON_BASIC_REPL=1 python3 -q'
tmux -S /tmp/opencode/tmux.sock send-keys -t "$TARGET" Enter
```

When debugging native programs, prefer LLDB unless the user requests another debugger.

## Read terminal contents

Capture joined pane output to reduce line-wrap artifacts:

```bash
tmux -S /tmp/opencode/tmux.sock capture-pane -p -J -t "$TARGET" -S -200
```

Adjust `-S` to retrieve more history when needed. Use `-S -` only when the complete history is genuinely necessary.

For interactive tools, synchronize by polling captured output for a recognizable prompt or completion marker. Use a short sleep between polls and a bounded number of attempts. Do not switch sockets when output is delayed.

## Preserve state

- Leave sessions open by default for later inspection and continued work.
- Do not kill a session or the tmux server unless the user explicitly requests cleanup.
- Closing an unnecessary non-final window is allowed.
- Before ending work, capture the relevant output and report the session name and useful window index to the user.
- Provide an attach or capture command only when it would help the user inspect or continue the work, or when the user asks. Do not print monitoring instructions mechanically after every session creation.

Useful inspection commands:

```bash
tmux -S /tmp/opencode/tmux.sock attach-session -t "$SESSION"
tmux -S /tmp/opencode/tmux.sock capture-pane -p -J -t "$SESSION:<window-index>.0" -S -200
```

Detach from an attached session with `Ctrl-b d`.

## Cleanup on explicit request only

Kill one session:

```bash
tmux -S /tmp/opencode/tmux.sock kill-session -t "$SESSION"
```

Kill all sessions and the isolated server only when the user clearly requests complete cleanup:

```bash
tmux -S /tmp/opencode/tmux.sock kill-server
```

Never use cleanup commands against the default socket or any socket other than `/tmp/opencode/tmux.sock`.

## Operational checklist

Before acting:

1. Ensure `/tmp/opencode` exists.
2. Use only `/tmp/opencode/tmux.sock`.
3. Inspect existing sessions and choose or reuse a namespace.
4. Select the correct session and window; assume pane `.0` only.

While acting:

1. Use windows, never additional panes.
2. Send literal commands, then send `Enter` separately.
3. Capture output before making state-dependent decisions.
4. Preserve sessions unless cleanup was explicitly requested.

After acting:

1. Capture the useful result.
2. Keep the session open.
3. Report the exact session and window used.
4. Include a user inspection command only when useful.
