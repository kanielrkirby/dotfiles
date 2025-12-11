export PATH="$PATH:$HOME/.local/bin"
export EDITOR="hx"
export HISTSIZE="1000000"
alias ls="eza"
alias y="yazi"
nope() { nohup "$@" > /dev/null 2>&1 & }
eval "$(zoxide init bash)"
shopt -s globstar
. /usr/share/doc/fzf/examples/{key-bindings,completion}.bash

[ "$TERM" = "linux" ] && printf '\e]P489b4fa'

if command -v tmux &> /dev/null && command -v fzf &> /dev/null && [ -z "$TMUX" ] && [ -z "$SKIP_TMUX_START" ]; then
  if ! ([ "$XDG_VTNR" = 1 ] && [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]); then
    choice=$({ tmux ls -F "#{session_name}" 2>/dev/null; echo "(New)"; } | fzf --height=40% --reverse)
    [ "$choice" = "(New)" ] && exec tmux
    [ -n "$choice" ] && exec tmux attach -t "$choice"
  fi
fi
