#!/usr/bin/env bash

SPEEDTEST_FILE="/tmp/panel_speedtest"
SPEEDTEST_PID_FILE="/tmp/panel_speedtest_pid"

# Read current state
current=$(cat "$SPEEDTEST_FILE" 2>/dev/null || echo "⊙")

if [[ "$current" == "..." ]]; then
    # Cancel running test
    if [[ -f "$SPEEDTEST_PID_FILE" ]]; then
        pid=$(cat "$SPEEDTEST_PID_FILE")
        kill "$pid" 2>/dev/null
        rm -f "$SPEEDTEST_PID_FILE"
    fi
    echo "⊙" > "$SPEEDTEST_FILE"
else
    # Set testing state
    echo "..." > "$SPEEDTEST_FILE"
    
    # Run speedtest in background
    (
        # Store PID for cancellation
        echo $$ > "$SPEEDTEST_PID_FILE"
        
        # Use speedtest-go with download only
        result=$(nix shell nixpkgs#speedtest-go --command speedtest-go --no-upload 2>/dev/null | grep "Download:" | awk '{print int($3)"Mbps"}')
        
        # Remove PID file
        rm -f "$SPEEDTEST_PID_FILE"
        
        # If speedtest failed, show error briefly
        if [[ -z "$result" ]]; then
            echo "Failed" > "$SPEEDTEST_FILE"
            sleep 3
        else
            # Show result
            echo "$result" > "$SPEEDTEST_FILE"
            
            # Wait 60 seconds, then reset to idle
            sleep 60
        fi
        
        # Reset to idle state
        echo "⊙" > "$SPEEDTEST_FILE"
    ) &
fi
