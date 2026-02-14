#!/usr/bin/env bash
current=$(cat /tmp/panel_date_format 2>/dev/null || echo compact)
if [ "$current" = "compact" ]; then
    echo -n "verbose" > /tmp/panel_date_format
else
    echo -n "compact" > /tmp/panel_date_format
fi
sync
