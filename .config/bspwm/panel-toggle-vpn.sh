#!/usr/bin/env bash
if mullvad status | grep -q Connected; then
    mullvad disconnect
else
    mullvad connect
fi
