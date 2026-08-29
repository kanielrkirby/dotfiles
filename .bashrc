export EDITOR="hx"
export NIXPKGS_ALLOW_UNFREE=1

shopt -s histappend
export HISTSIZE="1000000"
export HISTFILESIZE="10000000"

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


if command -v tmux &> /dev/null && command -v fzf &> /dev/null && [ -z "$TMUX" ] && [ -z "$SKIP_TMUX_START" ]; then
  if ! ([ "$XDG_VTNR" = 1 ] && [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]); then
    query_file=$(mktemp)
    create_file=$(mktemp)
    choice=$({ tmux ls -F "#{session_name}" 2>/dev/null; echo "(New)"; } | fzf --height=40% --reverse --bind "change:execute-silent(printf %s {q} > '$query_file')" --bind "ctrl-o:execute-silent(printf 1 > '$create_file')+abort")
    status=$?
    if [ -s "$create_file" ]; then
      query=$(<"$query_file")
      rm -f "$query_file" "$create_file"
      [ -n "$query" ] && exec tmux new-session -A -s "$query" || exec tmux
    fi
    rm -f "$query_file" "$create_file"
    [ $status -ne 0 ] && return
    [ "$choice" = "(New)" ] && exec tmux
    [ -n "$choice" ] && exec tmux attach -t "$choice"
  fi
fi


