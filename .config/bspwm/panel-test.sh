#!/usr/bin/env bash

# Colors
COLOR_BG="#1a1a1a"
COLOR_FG="#CCCCCC"

# Get volume info
get_volume() {
    local vol=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null)
    local muted=""
    
    if [ -z "$vol" ]; then
        echo "N/A"
        return
    fi
    
    if echo "$vol" | grep -q "MUTED"; then
        muted="M "
        vol=$(echo "$vol" | awk '{print $2}')
    else
        vol=$(echo "$vol" | awk '{print $2}')
    fi
    
    # Convert to percentage (handle empty values)
    if [ -n "$vol" ]; then
        vol=$(echo "$vol * 100" | bc 2>/dev/null | cut -d. -f1)
        echo "${muted}${vol}%"
    else
        echo "N/A"
    fi
}

# Update function
update_bar() {
    local volume=$(get_volume)
    echo "%{B$COLOR_BG}%{F$COLOR_FG}%{l} Volume Test %{r}${volume} "
}

# Initial update
update_bar

# Just volume polling (every 0.5s)
while true; do
    sleep 0.5
    update_bar
done
