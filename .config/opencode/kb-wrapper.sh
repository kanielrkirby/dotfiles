#!/usr/bin/env bash
# Run KB MCP server with Python3 from nix
# Filter out the HOME ownership warning but keep other stderr
exec 3>&2
exec 2> >(grep -v "warning: .HOME" >&3)
exec nix-shell -p python3 --run "python3 /home/mx/.config/opencode/kb-mcp-server.py"
