#!/usr/bin/env bash
if bluetoothctl info D8:C8:63:41:63:DB 2>/dev/null | grep -q "Connected: yes"; then
    timeout 10 bluetoothctl disconnect D8:C8:63:41:63:DB >/dev/null 2>&1 &
else
    timeout 10 bluetoothctl connect D8:C8:63:41:63:DB >/dev/null 2>&1 &
fi
