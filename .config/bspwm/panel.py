#!/usr/bin/env -S nix run nixpkgs#python312 --
import subprocess
import sys
import threading
import time
import os
import signal
import fcntl
from pathlib import Path

# No automatic cleanup - bspwmrc handles it

# Panel state - cached values
state = {
    'desktops': '',
    'brightness': '',
    'volume': '',
    'battery': '',
    'datetime': '',
    'vpn': 'Unsecured',
    'network': 'Disconnected',
    'bluetooth': '',
}

# Lock for thread-safe updates
lock = threading.Lock()

# Temp files for communication
PANEL_DATE_FORMAT = Path('/tmp/panel_date_format')
PANEL_VPN = Path('/tmp/panel_vpn')
PANEL_NETWORK = Path('/tmp/panel_network')

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1)
        return result.stdout.strip()
    except:
        return ""

def update_desktops():
    """Update desktop state - optimized to avoid shell overhead"""
    try:
        # Direct subprocess calls without shell for speed
        current = subprocess.run(
            ["bspc", "query", "-D", "-d", "focused", "--names"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip()
        
        occupied_raw = subprocess.run(
            ["bspc", "query", "-D", "-d", ".occupied", "--names"],
            capture_output=True, text=True, timeout=0.5
        ).stdout.strip()
        
        occupied_desktops = set(occupied_raw.split('\n')) if occupied_raw else set()
    except:
        current = ""
        occupied_desktops = set()
    
    desktops = ""
    for i in range(1, 10):
        if str(i) == current:
            indicator = f"[{i}]"
            desktops += f"%{{A:bspc desktop -f ^{i}:}}%{{F#FFFFFF}}{indicator}%{{F-}}%{{A}}"
        elif str(i) in occupied_desktops:
            indicator = f" {i} "
            desktops += f"%{{A:bspc desktop -f ^{i}:}}%{{F#888888}}{indicator}%{{F-}}%{{A}}"
        else:
            indicator = f" {i} "
            desktops += f"%{{A:bspc desktop -f ^{i}:}}%{{F#444444}}{indicator}%{{F-}}%{{A}}"
    
    with lock:
        state['desktops'] = desktops

def update_brightness():
    """Update brightness state"""
    brightness = run_cmd("brightnessctl -m | cut -d, -f4 | tr -d '%'")
    with lock:
        state['brightness'] = brightness

def update_volume():
    """Update volume state"""
    vol_output = run_cmd("wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>/dev/null")
    
    if not vol_output:
        volume = "N/A"
    elif "MUTED" in vol_output:
        vol = vol_output.split()[1]
        vol_percent = int(float(vol) * 100)
        volume = f"M {vol_percent}%"
    else:
        vol = vol_output.split()[1]
        vol_percent = int(float(vol) * 100)
        volume = f"{vol_percent}%"
    
    with lock:
        state['volume'] = volume

def update_battery():
    """Update battery state"""
    bat_path = Path("/sys/class/power_supply/BAT0")
    if not bat_path.exists():
        battery = "N/A"
    else:
        capacity = (bat_path / "capacity").read_text().strip()
        status = (bat_path / "status").read_text().strip()
        battery_state = "C" if status == "Charging" else "D"
        battery = f"{battery_state} {capacity}%"
    
    with lock:
        state['battery'] = battery

def update_datetime():
    """Update date/time state"""
    date_format = PANEL_DATE_FORMAT.read_text().strip() if PANEL_DATE_FORMAT.exists() else "compact"
    
    if date_format == "verbose":
        datetime = run_cmd('date "+%A, %B %d, %Y %I:%M %p"')
    else:
        datetime = run_cmd('date "+%a %Y-%m-%d %H:%M"')
    
    with lock:
        state['datetime'] = datetime

def update_vpn():
    """Update VPN state"""
    vpn = PANEL_VPN.read_text().strip() if PANEL_VPN.exists() else "Unsecured"
    with lock:
        state['vpn'] = vpn

def update_network():
    """Update network state"""
    network = PANEL_NETWORK.read_text().strip() if PANEL_NETWORK.exists() else "Disconnected"
    with lock:
        state['network'] = network

def update_bluetooth():
    """Update Bluetooth state"""
    # Check headphones (MOMENTUM TW 4)
    headphones_info = run_cmd("bluetoothctl info 80:C3:BA:53:50:59 2>/dev/null")
    h_connected = "Connected: yes" in headphones_info
    
    # Check mouse (MX Master 3S)
    mouse_info = run_cmd("bluetoothctl info D8:C8:63:41:63:DB 2>/dev/null")
    m_connected = "Connected: yes" in mouse_info
    
    # Build clickable bluetooth indicators with desktop-style shading
    h_color = "#FFFFFF" if h_connected else "#444444"
    m_color = "#FFFFFF" if m_connected else "#444444"
    
    # Inline bluetooth toggle commands
    h_cmd = '/home/mx/.config/bspwm/panel-toggle-bt-headphones.sh'
    m_cmd = '/home/mx/.config/bspwm/panel-toggle-bt-mouse.sh'
    
    bluetooth = f"%{{A:{h_cmd}:}}%{{F{h_color}}}[H]%{{F-}}%{{A}} %{{A:{m_cmd}:}}%{{F{m_color}}}[M]%{{F-}}%{{A}}"
    
    with lock:
        state['bluetooth'] = bluetooth

def render_bar():
    """Render the complete bar"""
    with lock:
        # Build clickable elements
        vpn_click = '%{A:/home/mx/.config/bspwm/panel-toggle-vpn.sh:}%{A3:mullvad reconnect:}' + state['vpn'] + '%{A}%{A}'
        
        network_click = '%{A:/home/mx/.config/bspwm/panel-toggle-wifi.sh:}%{A3:st -e nmtui:}' + state["network"] + '%{A}%{A}'
        
        volume_click = f"%{{A:wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle:}}{state['volume']}%{{A}}"
        
        datetime_click = '%{A:/home/mx/.config/bspwm/panel-toggle-date.sh:}%{A3:/home/mx/.config/bspwm/panel-copy-date.sh:}' + state["datetime"] + '%{A}%{A}'
        
        left = f"%{{l}} {state['desktops']}"
        right = f"{vpn_click}   {network_click}   {state['bluetooth']}   {state['brightness']}%   {volume_click}   {datetime_click}   {state['battery']}"
        
        output = f"%{{B#1a1a1a}}%{{F#CCCCCC}}{left}%{{r}}{right} "
    
    print(output, flush=True)

# Event watchers (each runs in its own thread)

def watch_desktops():
    """Watch desktop changes and node transfers"""
    update_desktops()
    proc = subprocess.Popen(
        ["bspc", "subscribe", "desktop_focus", "node_transfer"],
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    if proc.stdout:
        for line in proc.stdout:
            update_desktops()
            render_bar()

def watch_brightness():
    """Watch brightness changes"""
    update_brightness()
    proc = subprocess.Popen(
        ["udevadm", "monitor", "--kernel", "--subsystem-match=backlight"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            if "KERNEL[" in line:
                update_brightness()
                render_bar()

def watch_battery():
    """Watch battery status changes (charging/discharging) via udev"""
    update_battery()
    proc = subprocess.Popen(
        ["udevadm", "monitor", "--kernel", "--subsystem-match=power_supply"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            if "power_supply" in line:
                # Small delay to let sysfs update after event
                time.sleep(0.1)
                update_battery()
                render_bar()

def watch_battery_percentage():
    """Poll battery percentage (sysfs doesn't trigger inotify)"""
    last_capacity = ""
    while True:
        time.sleep(10)  # Poll every 10 seconds
        try:
            current_capacity = Path("/sys/class/power_supply/BAT0/capacity").read_text().strip()
            if current_capacity != last_capacity:
                last_capacity = current_capacity
                update_battery()
                render_bar()
        except:
            pass

def watch_volume():
    """Watch volume changes via pw-mon"""
    update_volume()
    proc = subprocess.Popen(
        ["pw-mon", "-N"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            if "volume" in line.lower() or "mute" in line.lower():
                update_volume()
                render_bar()

def watch_datetime():
    """Watch time changes (every minute)"""
    while True:
        update_datetime()
        render_bar()
        time.sleep(60)

def watch_date_format():
    """Watch date format toggle"""
    if not PANEL_DATE_FORMAT.exists():
        PANEL_DATE_FORMAT.write_text("compact")
    
    proc = subprocess.Popen(
        ["inotifywait", "-m", "-q", "-e", "close_write", str(PANEL_DATE_FORMAT)],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            update_datetime()
            render_bar()

def watch_vpn():
    """Watch VPN changes"""
    # Initialize VPN cache
    vpn_status = run_cmd("mullvad status 2>/dev/null")
    if "Connected" in vpn_status:
        vpn_relay = run_cmd("mullvad status 2>/dev/null | grep 'Relay:' | awk '{print $2}'")
        PANEL_VPN.write_text(vpn_relay)
    elif "Connecting" in vpn_status:
        PANEL_VPN.write_text("Connecting")
    elif "Blocked" in vpn_status:
        PANEL_VPN.write_text("Blocked")
    else:
        PANEL_VPN.write_text("Unsecured")
    
    update_vpn()
    
    proc = subprocess.Popen(
        ["mullvad", "status", "listen"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            # Update cache when status changes
            vpn_status = run_cmd("mullvad status 2>/dev/null")
            if "Connected" in vpn_status:
                vpn_relay = run_cmd("mullvad status 2>/dev/null | grep 'Relay:' | awk '{print $2}'")
                PANEL_VPN.write_text(vpn_relay)
            elif "Connecting" in vpn_status:
                PANEL_VPN.write_text("Connecting")
            elif "Blocked" in vpn_status:
                PANEL_VPN.write_text("Blocked")
            else:
                PANEL_VPN.write_text("Unsecured")
            
            update_vpn()
            render_bar()

def watch_network():
    """Watch network changes"""
    # Initialize network cache
    connection = run_cmd("nmcli -t -f type,state,name connection show --active | head -1")
    if "802-11-wireless" in connection:
        PANEL_NETWORK.write_text(connection.split(':')[2] if ':' in connection else "WiFi")
    elif "802-3-ethernet" in connection:
        PANEL_NETWORK.write_text("Wired")
    else:
        PANEL_NETWORK.write_text("Disconnected")
    
    update_network()
    
    proc = subprocess.Popen(
        ["nmcli", "monitor"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            # Update cache when network changes
            connection = run_cmd("nmcli -t -f type,state,name connection show --active | head -1")
            if "802-11-wireless" in connection:
                PANEL_NETWORK.write_text(connection.split(':')[2] if ':' in connection else "WiFi")
            elif "802-3-ethernet" in connection:
                PANEL_NETWORK.write_text("Wired")
            else:
                PANEL_NETWORK.write_text("Disconnected")
            
            update_network()
            render_bar()

def watch_bluetooth():
    """Watch Bluetooth connection changes"""
    update_bluetooth()
    
    # Monitor bluetoothctl for connection events
    proc = subprocess.Popen(
        ["stdbuf", "-oL", "bluetoothctl"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    
    if proc.stdout:
        for line in proc.stdout:
            # Look for connection state changes
            if "Connected: yes" in line or "Connected: no" in line:
                update_bluetooth()
                render_bar()

if __name__ == "__main__":
    # Initialize all states
    update_desktops()
    update_brightness()
    update_volume()
    update_battery()
    update_datetime()
    update_vpn()
    update_network()
    update_bluetooth()
    
    # Render initial bar
    render_bar()
    
    # Start all watchers in threads
    threads = [
        threading.Thread(target=watch_desktops, daemon=True),
        threading.Thread(target=watch_brightness, daemon=True),
        threading.Thread(target=watch_volume, daemon=True),
        threading.Thread(target=watch_battery, daemon=True),
        threading.Thread(target=watch_battery_percentage, daemon=True),
        threading.Thread(target=watch_datetime, daemon=True),
        threading.Thread(target=watch_date_format, daemon=True),
        threading.Thread(target=watch_vpn, daemon=True),
        threading.Thread(target=watch_network, daemon=True),
        threading.Thread(target=watch_bluetooth, daemon=True),
    ]
    
    for thread in threads:
        thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
