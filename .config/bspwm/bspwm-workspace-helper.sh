#!/usr/bin/env bash

# bspwm workspace helper
# Manages 3 workspaces of 9 desktops each (27 total)
# Workspace 1: desktops 1-9
# Workspace 2: desktops 10-18
# Workspace 3: desktops 19-27

WORKSPACE_FILE="/tmp/bspwm_current_workspace"

# Initialize workspace file if doesn't exist
if [ ! -f "$WORKSPACE_FILE" ]; then
    echo "1" > "$WORKSPACE_FILE"
fi

get_current_workspace() {
    cat "$WORKSPACE_FILE" 2>/dev/null || echo "1"
}

set_current_workspace() {
    echo "$1" > "$WORKSPACE_FILE"
}

# Calculate actual desktop number from workspace and local desktop
# Args: <workspace_number> <local_desktop_number>
calculate_desktop() {
    local workspace=$1
    local local_num=$2
    echo $(( (workspace - 1) * 9 + local_num ))
}

case "$1" in
    switch)
        # Switch to a different workspace
        # Usage: bspwm-workspace-helper.sh switch <workspace_number>
        workspace_num="$2"
        if [ "$workspace_num" -ge 1 ] && [ "$workspace_num" -le 3 ]; then
            set_current_workspace "$workspace_num"
            # Jump to first desktop of new workspace
            actual_desktop=$(calculate_desktop "$workspace_num" 1)
            bspc desktop -f "^$actual_desktop"
        fi
        ;;
    
    focus)
        # Focus desktop within current workspace
        # Usage: bspwm-workspace-helper.sh focus <local_desktop_number>
        current_workspace=$(get_current_workspace)
        local_num="$2"
        actual_desktop=$(calculate_desktop "$current_workspace" "$local_num")
        bspc desktop -f "^$actual_desktop"
        ;;
    
    move)
        # Move window to desktop within current workspace
        # Usage: bspwm-workspace-helper.sh move <local_desktop_number>
        current_workspace=$(get_current_workspace)
        local_num="$2"
        actual_desktop=$(calculate_desktop "$current_workspace" "$local_num")
        bspc node -d "^$actual_desktop"
        ;;
    
    move-to-workspace)
        # Move window to specific desktop in specific workspace
        # Usage: bspwm-workspace-helper.sh move-to-workspace <workspace_number> <local_desktop_number>
        workspace_num="$2"
        local_num="$3"
        if [ "$workspace_num" -ge 1 ] && [ "$workspace_num" -le 3 ] && [ "$local_num" -ge 1 ] && [ "$local_num" -le 10 ]; then
            actual_desktop=$(calculate_desktop "$workspace_num" "$local_num")
            bspc node -d "^$actual_desktop"
        fi
        ;;
    
    get-workspace)
        # Get current workspace number
        get_current_workspace
        ;;
    
    cycle)
        # Cycle to next workspace
        # Usage: bspwm-workspace-helper.sh cycle
        current_workspace=$(get_current_workspace)
        next_workspace=$(( (current_workspace % 3) + 1 ))
        set_current_workspace "$next_workspace"
        # Jump to first desktop of new workspace
        actual_desktop=$(calculate_desktop "$next_workspace" 1)
        bspc desktop -f "^$actual_desktop"
        ;;
    
    *)
        echo "Usage: $0 {switch|focus|move|move-to-workspace|get-workspace|cycle} [args]"
        exit 1
        ;;
esac
