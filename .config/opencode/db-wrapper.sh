#!/usr/bin/env bash
# Run DB MCP server with Python3 and usql from nix
# Filter out the HOME ownership warning but keep other stderr
exec 3>&2
exec 2> >(grep -v "warning: .HOME" >&3)
exec nix-shell -p python3 usql --run "python3 /home/mx/.config/opencode/db-mcp-server.py"
