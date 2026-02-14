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

# Get date
get_date() {
    date "+%a %Y-%m-%d %H:%M"
}

# Get VPN status
get_vpn() {
    local vpn_status=$(mullvad status 2>/dev/null)
    
    # Determine VPN state
    if echo "$vpn_status" | grep -q "Connected"; then
        # Extract full relay code: "us-phx-wg-208"
        echo "$(echo "$vpn_status" | grep "Relay:" | awk '{print $2}')"
    elif echo "$vpn_status" | grep -q "Connecting"; then
        echo "Connecting"
    elif echo "$vpn_status" | grep -q "Blocked"; then
        echo "Blocked"
    else
        echo "Unsecured"
    fi
}

# Get network connection (WiFi/Ethernet)
get_network() {
    # Determine network connection (WiFi > Ethernet > Disconnected)
    local wifi=$(nmcli -t -f active,ssid dev wifi | grep '^yes' | cut -d: -f2)
    local ethernet=$(nmcli -t -f device,state dev | grep 'ethernet:connected' | cut -d: -f1)
    
    if [ -n "$wifi" ]; then
        echo "$wifi"
    elif [ -n "$ethernet" ]; then
        echo "Wired"
    else
        echo "Disconnected"
    fi
}

# Update function
update_bar() {
    local desktops=$(get_desktops)
    local brightness=$(get_brightness)
    local volume=$(get_volume)
    local battery=$(get_battery)
    local datetime=$(get_date)
    local vpn=$(get_vpn)
    local network=$(get_network)
    
    # Build status line
    local left="%{l} $desktops"
    
    # Make VPN clickable: left=toggle, right=reconnect
    local vpn_clickable="%{A:sh -c 'if mullvad status | grep -q Connected; then mullvad disconnect; else mullvad connect; fi':}%{A3:mullvad reconnect:}${vpn}%{A}%{A}"
    
    # Make network clickable: left=toggle wifi, right=open nmtui
    local network_clickable="%{A:sh -c 'test \$(nmcli radio wifi) = enabled && nmcli radio wifi off || nmcli radio wifi on':}%{A3:sh -c 'st -e nmtui':}${network}%{A}%{A}"
    
    # Make volume clickable: left=mute toggle
    local volume_clickable="%{A:wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle:}${volume}%{A}"
    
    # Right side - vpn, network, brightness, volume, date, battery
    local right="${vpn_clickable}   ${network_clickable}   ${brightness}%   ${volume_clickable}   ${datetime}   ${battery}"
    
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

# Volume changes (instant - monitors PulseAudio events)
pactl subscribe 2>/dev/null | grep --line-buffered "sink" | while read; do
    update_bar
done &

# VPN/WiFi polling (every 3s)
while true; do
    sleep 3
    update_bar
done
