export PATH="$PATH:$HOME/.local/bin"
export EDITOR="vi"
export HISTSIZE="1000000"
export NIXPKGS_ALLOW_UNFREE=1
nope() { nohup "$@" > /dev/null 2>&1 & }
shopt -s globstar

# FZF integration
if command -v fzf &> /dev/null; then
  eval "$(fzf --bash)"
fi

[ "$TERM" = "linux" ] && printf '\e]P489b4fa'

if command -v tmux &> /dev/null && command -v fzf &> /dev/null && [ -z "$TMUX" ] && [ -z "$SKIP_TMUX_START" ]; then
  if ! ([ "$XDG_VTNR" = 1 ] && [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]); then
    choice=$({ tmux ls -F "#{session_name}" 2>/dev/null; echo "(New)"; } | fzf --height=40% --reverse)
    [ "$choice" = "(New)" ] && exec tmux
    [ -n "$choice" ] && exec tmux attach -t "$choice"
  fi
fi
