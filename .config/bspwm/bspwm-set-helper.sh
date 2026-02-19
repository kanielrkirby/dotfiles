#!/usr/bin/env bash

# bspwm desktop set helper
# Manages 3 sets of 9 desktops each (27 total)
# Set 1: desktops 1-9
# Set 2: desktops 10-18
# Set 3: desktops 19-27

SET_FILE="/tmp/bspwm_current_set"

# Initialize set file if doesn't exist
if [ ! -f "$SET_FILE" ]; then
    echo "1" > "$SET_FILE"
fi

get_current_set() {
    cat "$SET_FILE" 2>/dev/null || echo "1"
}

set_current_set() {
    echo "$1" > "$SET_FILE"
}

# Calculate actual desktop number from set and local desktop
# Args: <set_number> <local_desktop_number>
calculate_desktop() {
    local set=$1
    local local_num=$2
    echo $(( (set - 1) * 9 + local_num ))
}

case "$1" in
    switch)
        # Switch to a different set
        # Usage: bspwm-set-helper.sh switch <set_number>
        set_num="$2"
        if [ "$set_num" -ge 1 ] && [ "$set_num" -le 3 ]; then
            set_current_set "$set_num"
            # Jump to first desktop of new set
            actual_desktop=$(calculate_desktop "$set_num" 1)
            bspc desktop -f "^$actual_desktop"
        fi
        ;;
    
    focus)
        # Focus desktop within current set
        # Usage: bspwm-set-helper.sh focus <local_desktop_number>
        current_set=$(get_current_set)
        local_num="$2"
        actual_desktop=$(calculate_desktop "$current_set" "$local_num")
        bspc desktop -f "^$actual_desktop"
        ;;
    
    move)
        # Move window to desktop within current set
        # Usage: bspwm-set-helper.sh move <local_desktop_number>
        current_set=$(get_current_set)
        local_num="$2"
        actual_desktop=$(calculate_desktop "$current_set" "$local_num")
        bspc node -d "^$actual_desktop"
        ;;
    
    move-to-set)
        # Move window to specific desktop in specific set
        # Usage: bspwm-set-helper.sh move-to-set <set_number> <local_desktop_number>
        set_num="$2"
        local_num="$3"
        if [ "$set_num" -ge 1 ] && [ "$set_num" -le 3 ] && [ "$local_num" -ge 1 ] && [ "$local_num" -le 10 ]; then
            actual_desktop=$(calculate_desktop "$set_num" "$local_num")
            bspc node -d "^$actual_desktop"
        fi
        ;;
    
    get-set)
        # Get current set number
        get_current_set
        ;;
    
    cycle)
        # Cycle to next set
        # Usage: bspwm-set-helper.sh cycle
        current_set=$(get_current_set)
        next_set=$(( (current_set % 3) + 1 ))
        set_current_set "$next_set"
        # Jump to first desktop of new set
        actual_desktop=$(calculate_desktop "$next_set" 1)
        bspc desktop -f "^$actual_desktop"
        ;;
    
    *)
        echo "Usage: $0 {switch|focus|move|move-to-set|get-set|cycle} [args]"
        exit 1
        ;;
esac
