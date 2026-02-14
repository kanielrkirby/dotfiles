# Export environment variables for graphical session
export MENU_CUSTOM_OPTS="-l 10 -i"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

# Source bashrc if running bash interactively
[[ -f ~/.bashrc ]] && . ~/.bashrc
