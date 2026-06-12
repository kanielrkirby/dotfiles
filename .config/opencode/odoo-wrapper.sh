#!/usr/bin/env bash
# Run the Odoo MCP server with Python3 from nix.
# The launcher reads project or global Odoo config files and caches a venv.
exec 3>&2
exec 2> >(grep -v "warning: .HOME" >&3)
exec nix-shell -p python3 python3Packages.pip --run "python3 /home/mx/.config/opencode/odoo-mcp-server.py"
