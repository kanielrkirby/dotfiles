#!/usr/bin/env bash
# Helper script for panel click actions

case "$1" in
    date-toggle)
        current=$(cat /tmp/panel_date_format 2>/dev/null || echo compact)
        if [ "$current" = "compact" ]; then
            echo verbose > /tmp/panel_date_format
        else
            echo compact > /tmp/panel_date_format
        fi
        ;;
    
    date-copy)
        date "+%A, %B %d, %Y %I:%M %p" | xclip -selection clipboard
        ;;
    
    vpn-toggle)
        if mullvad status | grep -q Connected; then
            mullvad disconnect
        else
            mullvad connect
        fi
        ;;
    
    vpn-reconnect)
        mullvad reconnect
        ;;
    
    wifi-toggle)
        if [ "$(nmcli radio wifi)" = "enabled" ]; then
            nmcli radio wifi off
        else
            nmcli radio wifi on
        fi
        ;;
    
    network-config)
        st -e nmtui
        ;;
    
    bluetooth-headphones)
        timeout 10 bluetoothctl info 80:C3:BA:53:50:59 2>/dev/null | grep -q "Connected: yes"
        if [ $? -eq 0 ]; then
            timeout 10 bluetoothctl disconnect 80:C3:BA:53:50:59 >/dev/null 2>&1 &
        else
            timeout 10 bluetoothctl connect 80:C3:BA:53:50:59 >/dev/null 2>&1 &
        fi
        ;;
    
    bluetooth-mouse)
        timeout 10 bluetoothctl info D8:C8:63:41:63:DB 2>/dev/null | grep -q "Connected: yes"
        if [ $? -eq 0 ]; then
            timeout 10 bluetoothctl disconnect D8:C8:63:41:63:DB >/dev/null 2>&1 &
        else
            timeout 10 bluetoothctl connect D8:C8:63:41:63:DB >/dev/null 2>&1 &
        fi
        ;;
esac
