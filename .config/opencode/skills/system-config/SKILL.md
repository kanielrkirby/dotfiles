---
name: system-config
description: Basic information on understanding and updating the NixOS system running on a P14s.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: github
---

Tailscale is configured with headscale against https://ts.gum.cx. Available devices are:
- p14: this device, primary dev machine
- p50: home laptop, mostly for stable IP exit node for whitelists and whatnot
- harbor: hetzner server running all gum.cx and kanielrkirby.com services. More info in the harbor skill when needed
- moto, mac: Phone and MacOS, used much less

P14 system runs NixOS, with primary configuration surfaces described below:
- /etc/nixos/: All custom derivations, general system configuration, flakes, etc.
- ~/dev/lab/dotfiles: GitHub-tracked dotfiles, manually copied from here to ~/ in a script that runs in /etc/nixos/flake.nix.
  - This sometimes complicates things, as the copy script is sensitive about differences in ~/ that aren't in ~/dev/lab/dotfiles. Standard practice is to review all directories copied in the script, run diffs, and ask user which should be copied from ~/ to ~/dev/lab/dotfiles, and which should be discarded.
- ~/dev/lab/dotfiles/.config/{sxhkd,bspwm}/ for custom bar, hotkeys, and window manager details.

Standard update flow is as follows:
- Needs update in ~/ dotfiles? Update in ~/dev/lab/dotfiles too.
  - Ensure dotfiles contains all changes in ~/
  - Add, commit, and push changes on ~/dev/lab/dotfiles repo.
  - Update dotfiles input in /etc/nixos/flake.nix with nix flake update dotfiles
- Has new or previously untracked differences?
  - Add, commit, and push changes on /etc/nixos.
- Run `sudo nixos-rebuild switch`
