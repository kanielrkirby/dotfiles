#!/usr/bin/env bash
export SUDO_ASKPASS="$HOME/.local/bin/sudo-askpass"
if systemctl is-active --quiet tailscaled; then
  sudo -A systemctl stop tailscaled
else
  sudo -A systemctl start tailscaled
fi
touch /tmp/panel_tailscale
