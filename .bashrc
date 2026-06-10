export PATH="$PATH:$HOME/.local/bin"
export EDITOR="vi"
export HISTSIZE="1000000"
export NIXPKGS_ALLOW_UNFREE=1

shopt -s globstar
shopt -s huponexit

# FZF integration
if command -v fzf &> /dev/null; then
  eval "$(fzf --bash)"
fi

# Zoxide integration
if command -v zoxide &> /dev/null; then
  eval "$(zoxide init bash)"
fi

function nope() {
  ( set +m; bash -c "$*" >/dev/null 2>&1 </dev/null & )
}

[ "$TERM" = "linux" ] && printf '\e]P489b4fa'

if command -v tmux &> /dev/null && command -v fzf &> /dev/null && [ -z "$TMUX" ] && [ -z "$SKIP_TMUX_START" ]; then
  if ! ([ "$XDG_VTNR" = 1 ] && [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]); then
    mapfile -t picker < <({ tmux ls -F "#{session_name}" 2>/dev/null; echo "(New)"; } | fzf --height=40% --reverse --print-query)
    query="${picker[0]}"
    choice="${picker[1]}"
    if [ "$choice" = "(New)" ] || [ -z "$choice" ]; then
      [ -n "$query" ] && exec tmux new-session -A -s "$query" || exec tmux
    else
      exec tmux attach -t "$choice"
    fi
  fi
fi

# --- Gas Town Integration (managed by gt) ---
export GASTOWN_DISABLE_OFFER_ADD=1
[[ -f "/home/mx/.config/gastown/shell-hook.sh" ]] && source "/home/mx/.config/gastown/shell-hook.sh"
# --- End Gas Town ---
