#!/usr/bin/env bash
if bluetoothctl info 80:C3:BA:53:50:59 2>/dev/null | grep -q "Connected: yes"; then
    timeout 10 bluetoothctl disconnect 80:C3:BA:53:50:59 >/dev/null 2>&1 &
else
    timeout 10 bluetoothctl connect 80:C3:BA:53:50:59 >/dev/null 2>&1 &
fi
