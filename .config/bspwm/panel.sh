#!/usr/bin/env bash

# Colors
COLOR_ACTIVE="#FFFFFF"
COLOR_OCCUPIED="#888888"
COLOR_EMPTY="#444444"
COLOR_BG="#1a1a1a"
COLOR_FG="#CCCCCC"

# Get desktop info
get_desktops() {
    local desktops=""
    local current=$(bspc query -D -d focused --names 2>/dev/null)
    
    for i in {1..9}; do
        local occupied=$(bspc query -N -d "^$i" 2>/dev/null | wc -l)
        
        # Use printf to ensure consistent width: 3 chars total ("[1]" or " 1 ")
        if [ "$i" = "$current" ]; then
            # Active desktop with brackets (clickable)
            local indicator=$(printf "[%s]" "$i")
            desktops+="%{A:bspc desktop -f ^$i:}%{F$COLOR_ACTIVE}${indicator}%{F-}%{A}"
        elif [ "$occupied" -gt 0 ]; then
            # Occupied desktop with padding to match bracket width (clickable)
            local indicator=$(printf " %s " "$i")
            desktops+="%{A:bspc desktop -f ^$i:}%{F$COLOR_OCCUPIED}${indicator}%{F-}%{A}"
        else
            # Empty desktop with padding to match bracket width (clickable)
            local indicator=$(printf " %s " "$i")
            desktops+="%{A:bspc desktop -f ^$i:}%{F$COLOR_EMPTY}${indicator}%{F-}%{A}"
        fi
    done
    
    echo "$desktops"
}

# Get brightness percentage
get_brightness() {
    brightnessctl -m | cut -d, -f4 | tr -d '%'
}

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

# Get battery info
get_battery() {
    local bat_path="/sys/class/power_supply/BAT0"
    
    if [ ! -d "$bat_path" ]; then
        echo "N/A"
        return
    fi
    
    local capacity=$(cat "$bat_path/capacity")
    local status=$(cat "$bat_path/status")
    local state="D"
    
    if [ "$status" = "Charging" ]; then
        state="C"
    fi
    
    echo "$state ${capacity}%"
}

# Get date (format depends on state file)
get_date() {
    local format_file="/tmp/panel_date_format"
    local format=$(cat "$format_file" 2>/dev/null || echo "compact")
    
    if [ "$format" = "verbose" ]; then
        date "+%A, %B %d, %Y %I:%M %p"
    else
        date "+%a %Y-%m-%d %H:%M"
    fi
}

# Get VPN status (cached - updated only by mullvad listen)
get_vpn() {
    cat /tmp/panel_vpn 2>/dev/null || echo "Unsecured"
}

# Update VPN cache
update_vpn_cache() {
    local vpn_status=$(mullvad status 2>/dev/null)
    
    # Determine VPN state
    if echo "$vpn_status" | grep -q "Connected"; then
        # Extract full relay code: "us-phx-wg-208"
        echo "$(echo "$vpn_status" | grep "Relay:" | awk '{print $2}')" > /tmp/panel_vpn
    elif echo "$vpn_status" | grep -q "Connecting"; then
        echo "Connecting" > /tmp/panel_vpn
    elif echo "$vpn_status" | grep -q "Blocked"; then
        echo "Blocked" > /tmp/panel_vpn
    else
        echo "Unsecured" > /tmp/panel_vpn
    fi
}

# Get network connection (cached - updated only by nmcli monitor)
get_network() {
    cat /tmp/panel_network 2>/dev/null || echo "Disconnected"
}

# Update network cache
update_network_cache() {
    local connection=$(nmcli -t -f type,state,name connection show --active | head -1)
    
    if echo "$connection" | grep -q "^802-11-wireless"; then
        echo "$connection" | cut -d: -f3 > /tmp/panel_network
    elif echo "$connection" | grep -q "^802-3-ethernet"; then
        echo "Wired" > /tmp/panel_network
    else
        echo "Disconnected" > /tmp/panel_network
    fi
}

# Update function
update_bar() {
    local desktops=$(get_desktops)
    local brightness=$(get_brightness)
    # local volume=$(get_volume)  # COMMENTED OUT FOR TESTING
    local battery=$(get_battery)
    local datetime=$(get_date)
    local vpn=$(get_vpn)
    local network=$(get_network)  # TESTING - ADDED BACK
    
    # Build status line
    local left="%{l} $desktops"
    
    local vpn_clickable="%{A:sh -c 'if mullvad status | grep -q Connected; then mullvad disconnect; else mullvad connect; fi':}%{A3:mullvad reconnect:}${vpn}%{A}%{A}"
    local network_clickable="%{A:sh -c 'test \$(nmcli radio wifi) = enabled && nmcli radio wifi off || nmcli radio wifi on':}%{A3:sh -c 'st -e nmtui':}${network}%{A}%{A}"
    local datetime_clickable="%{A:sh -c 'if [ \$(cat /tmp/panel_date_format 2>/dev/null || echo compact) = compact ]; then echo verbose > /tmp/panel_date_format; else echo compact > /tmp/panel_date_format; fi':}%{A3:sh -c 'date \"+\%A, \%B \%d, \%Y \%I:\%M \%p\" | xclip -selection clipboard':}${datetime}%{A}%{A}"
    
    # Right side - vpn + network + brightness + date + battery for testing
    local right="${vpn_clickable}   ${network_clickable}   ${brightness}%   ${datetime_clickable}   ${battery}"
    
    echo "%{B$COLOR_BG}%{F$COLOR_FG}${left}%{r}${right} "
}

# Initial update
update_bar

# Desktop changes (instant - unbuffered)
stdbuf -oL bspc subscribe desktop | while read -r event; do
    update_bar
done &

# Brightness changes (instant - monitors udev events)
udevadm monitor --kernel --subsystem-match=backlight 2>/dev/null | grep --line-buffered "KERNEL\[" | while read; do
    update_bar
done &

# Battery changes (instant - monitors udev events for BAT0 and AC)
udevadm monitor --kernel --subsystem-match=power_supply 2>/dev/null | grep --line-buffered -E "BAT0|AC" | while read; do
    update_bar
done &

# Time/Date changes (instant - monitors RTC)
inotifywait -m -q -e modify /sys/class/rtc/rtc0/time /sys/class/rtc/rtc0/date 2>/dev/null | while read; do
    update_bar
done &

# Volume changes (monitors PipeWire events via pw-mon) - COMMENTED OUT FOR TESTING
# pw-mon -N 2>/dev/null | grep --line-buffered "volume\|mute" | while read; do
#     update_bar
# done &

# Date format toggle trigger
[ ! -f /tmp/panel_date_format ] && echo "compact" > /tmp/panel_date_format
inotifywait -m -q -e close_write /tmp/panel_date_format 2>/dev/null | while read; do
    update_bar
done &

# Network changes (monitors NetworkManager events)
update_network_cache  # Initialize cache
nmcli monitor 2>/dev/null | while read; do
    update_network_cache
    update_bar
done &

# VPN changes (monitors Mullvad events)
update_vpn_cache  # Initialize cache
mullvad status listen 2>/dev/null | while read; do
    update_vpn_cache
    update_bar
done &

# Periodic update for time/date only (every 60s)
while true; do
    sleep 60
    update_bar
done
