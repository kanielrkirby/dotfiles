#!/usr/bin/env -S nix run nixpkgs#python312 --
import subprocess
import sys
import threading
import time
import os
import signal
import fcntl
import json
from pathlib import Path

# No automatic cleanup - bspwmrc handles it

# Panel state - cached values
state = {
    'desktops': '',
    'set_indicator': '',
    'brightness': '',
    'volume': '',
    'volume_muted': '',
    'mic': '',
    'battery': '',
    'datetime': '',
    'vpn': 'Unsecured',
    'network': 'Disconnected',
    'bluetooth': '',
    'speedtest': '⊙',
}

# Lock for thread-safe updates
lock = threading.Lock()

# Temp files for communication
PANEL_DATE_FORMAT = Path('/tmp/panel_date_format')
PANEL_VPN = Path('/tmp/panel_vpn')
PANEL_NETWORK = Path('/tmp/panel_network')
PANEL_SPEEDTEST = Path('/tmp/panel_speedtest')
PANEL_SET = Path('/tmp/bspwm_current_set')

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1)
        return result.stdout.strip()
    except:
        return ""

def get_current_set():
    """Get current desktop set (1, 2, or 3)"""
    try:
        if PANEL_SET.exists():
            return int(PANEL_SET.read_text().strip())
    except:
        pass
    return 1

def update_desktops():
    """Update desktop state - single bspc call for maximum performance"""
    try:
        # Use bspc wm -d JSON dump - ONE call instead of two separate queries
        result = subprocess.run(
            ["bspc", "wm", "-d"],
            capture_output=True, text=True, timeout=0.5
        )
        
        data = json.loads(result.stdout)
        
        # Get current set to determine which desktops to show
        current_set = get_current_set()
        set_offset = (current_set - 1) * 9
        
        # Parse JSON to get current and occupied desktops
        current_actual = ""
        occupied_desktops = set()
        
        focused_mon_id = data.get('focusedMonitorId')
        for mon in data.get('monitors', []):
            focused_desk_id = mon.get('focusedDesktopId')
            for desk in mon.get('desktops', []):
                name = desk.get('name', '')
                # Check if occupied (has windows)
                if desk.get('root'):
                    occupied_desktops.add(name)
                # Check if focused
                if mon.get('id') == focused_mon_id and desk.get('id') == focused_desk_id:
                    current_actual = name
    except:
        current_actual = ""
        occupied_desktops = set()
        current_set = 1
        set_offset = 0
    
    # Convert actual desktop to local desktop number (1-9)
    current_local = ""
    if current_actual:
        try:
            actual_num = int(current_actual)
            if set_offset < actual_num <= set_offset + 9:
                current_local = str(actual_num - set_offset)
        except:
            pass
    
    # Build desktop display (only show desktops 1-9 for current set)
    desktops = ""
    for i in range(1, 10):
        actual_desktop = set_offset + i
        is_current = str(i) == current_local
        is_occupied = str(actual_desktop) in occupied_desktops
        
        if is_current:
            indicator = f"[{i}]"
            desktops += f"%{{A:/home/mx/.config/bspwm/bspwm-set-helper.sh focus {i}:}}%{{F#FFFFFF}}{indicator}%{{F-}}%{{A}}"
        elif is_occupied:
            indicator = f" {i} "
            desktops += f"%{{A:/home/mx/.config/bspwm/bspwm-set-helper.sh focus {i}:}}%{{F#888888}}{indicator}%{{F-}}%{{A}}"
        else:
            indicator = f" {i} "
            desktops += f"%{{A:/home/mx/.config/bspwm/bspwm-set-helper.sh focus {i}:}}%{{F#444444}}{indicator}%{{F-}}%{{A}}"
    
    # Set indicator (W/P/O for Work/Personal/Other) - clickable to cycle
    set_names = {1: "W", 2: "P", 3: "O"}
    set_label = set_names.get(current_set, '?')
    set_indicator = f"%{{A:/home/mx/.config/bspwm/bspwm-set-helper.sh cycle:}}[{set_label}]%{{A}}"
    
    with lock:
        state['desktops'] = desktops
        state['set_indicator'] = set_indicator

def update_brightness():
    """Update brightness state"""
    try:
        result = subprocess.run(
            ["brightnessctl", "-m"],
            capture_output=True, text=True, timeout=0.5
        )
        # Parse machine-readable format: device,class,curr,max,percent
        brightness = result.stdout.split(',')[3].replace('%', '') if result.stdout else ""
    except:
        brightness = ""
    with lock:
        state['brightness'] = brightness

def update_volume():
    """Update volume state"""
    volume_muted = ""
    try:
        result = subprocess.run(
            ["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
            capture_output=True, text=True, timeout=0.5
        )
        vol_output = result.stdout.strip()
        
        if not vol_output:
            volume = "N/A"
        elif "MUTED" in vol_output:
            vol = vol_output.split()[1]
            vol_percent = int(float(vol) * 100)
            volume = f"{vol_percent}%"
            volume_muted = "M"
        else:
            vol = vol_output.split()[1]
            vol_percent = int(float(vol) * 100)
            volume = f"{vol_percent}%"
    except:
        volume = "N/A"
    
    with lock:
        state['volume'] = volume
        state['volume_muted'] = volume_muted

def update_mic():
    """Update mic mute state"""
    try:
        result = subprocess.run(
            ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"],
            capture_output=True, text=True, timeout=0.5
        )
        mic_output = result.stdout.strip()
        
        if "yes" in mic_output:
            mic = "X"
        else:
            mic = ""
    except:
        mic = ""
    
    with lock:
        state['mic'] = mic

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
    
    try:
        if date_format == "verbose":
            result = subprocess.run(
                ["date", "+%A, %B %d, %Y %I:%M %p"],
                capture_output=True, text=True, timeout=0.5
            )
        else:
            result = subprocess.run(
                ["date", "+%a %Y-%m-%d %H:%M"],
                capture_output=True, text=True, timeout=0.5
            )
        datetime = result.stdout.strip()
    except:
        datetime = ""
    
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
    try:
        # Check headphones (MOMENTUM TW 4)
        h_result = subprocess.run(
            ["bluetoothctl", "info", "80:C3:BA:53:50:59"],
            capture_output=True, text=True, timeout=0.5
        )
        h_connected = "Connected: yes" in h_result.stdout
        
        # Check mouse (MX Master 3S)
        m_result = subprocess.run(
            ["bluetoothctl", "info", "D8:C8:63:41:63:DB"],
            capture_output=True, text=True, timeout=0.5
        )
        m_connected = "Connected: yes" in m_result.stdout
    except:
        h_connected = False
        m_connected = False
    
    # Build clickable bluetooth indicators with desktop-style shading
    h_color = "#FFFFFF" if h_connected else "#444444"
    m_color = "#FFFFFF" if m_connected else "#444444"
    
    # Inline bluetooth toggle commands
    h_cmd = '/home/mx/.config/bspwm/panel-toggle-bt-headphones.sh'
    m_cmd = '/home/mx/.config/bspwm/panel-toggle-bt-mouse.sh'
    
    bluetooth = f"%{{A:{h_cmd}:}}%{{A3:st -e bluetui:}}%{{F{h_color}}}[H]%{{F-}}%{{A}}%{{A}} %{{A:{m_cmd}:}}%{{A3:st -e bluetui:}}%{{F{m_color}}}[M]%{{F-}}%{{A}}%{{A}}"
    
    with lock:
        state['bluetooth'] = bluetooth

def update_speedtest():
    """Update speedtest state"""
    speedtest = PANEL_SPEEDTEST.read_text().strip() if PANEL_SPEEDTEST.exists() else "⊙"
    with lock:
        state['speedtest'] = speedtest

def render_bar():
    """Render the complete bar"""
    with lock:
        # Build clickable elements
        vpn_click = '%{A:/home/mx/.config/bspwm/panel-toggle-vpn.sh:}%{A3:mullvad reconnect:}' + state['vpn'] + '%{A}%{A}'
        
        network_click = '%{A:/home/mx/.config/bspwm/panel-toggle-wifi.sh:}%{A3:st -e nmtui:}' + state["network"] + '%{A}%{A}'
        
        # Speedtest with click to trigger test
        speedtest_color = "#444444" if state['speedtest'] == "⊙" else "#CCCCCC"
        speedtest_click = f"%{{A:/home/mx/.config/bspwm/panel-run-speedtest.sh:}}%{{F{speedtest_color}}}[{state['speedtest']}]%{{F-}}%{{A}}"
        
        # Brightness with scroll support (scroll up = +5%, scroll down = -5%)
        brightness_click = f"%{{A4:brightnessctl set +5%:}}%{{A5:brightnessctl set 5%-:}}{state['brightness']}%%{{A}}%{{A}}"
        
        # Volume with click to mute + scroll support (scroll up = +5%, scroll down = -5%, capped at 120%)
        # Format: [X][M] percentage (X = mic muted, M = volume muted)
        # Left click = toggle volume mute, Right click = toggle mic mute
        indicators = state['mic'] + state['volume_muted']
        volume_display = f"{indicators} {state['volume']}" if indicators else state['volume']
        volume_click = f"%{{A:wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle:}}%{{A3:pactl set-source-mute @DEFAULT_SOURCE@ toggle:}}%{{A4:wpctl set-volume -l 1.2 @DEFAULT_AUDIO_SINK@ 5%+:}}%{{A5:wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-:}}{volume_display}%{{A}}%{{A}}%{{A}}%{{A}}"
        
        datetime_click = '%{A:/home/mx/.config/bspwm/panel-toggle-date.sh:}%{A3:st -e sh -c "cal; read":}' + state["datetime"] + '%{A}%{A}'
        
        left = f"%{{l}} {state['desktops']} {state['set_indicator']}"
        right = f"{vpn_click}   {network_click}   {speedtest_click}   {state['bluetooth']}   {brightness_click}   {volume_click}   {datetime_click}   {state['battery']}"
        
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
        bufsize=0  # Completely unbuffered
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

def watch_mic():
    """Watch mic mute changes via pw-mon"""
    update_mic()
    proc = subprocess.Popen(
        ["pw-mon", "-N"],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            if "mute" in line.lower():
                update_mic()
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
    try:
        result = subprocess.run(
            ["mullvad", "status"],
            capture_output=True, text=True, timeout=1
        )
        vpn_status = result.stdout
        
        if "Connected" in vpn_status:
            # Parse relay from status output
            for line in vpn_status.split('\n'):
                if "Relay:" in line:
                    vpn_relay = line.split()[1]
                    PANEL_VPN.write_text(vpn_relay)
                    break
        elif "Connecting" in vpn_status:
            PANEL_VPN.write_text("Connecting")
        elif "Blocked" in vpn_status:
            PANEL_VPN.write_text("Blocked")
        else:
            PANEL_VPN.write_text("Unsecured")
    except:
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
            try:
                result = subprocess.run(
                    ["mullvad", "status"],
                    capture_output=True, text=True, timeout=1
                )
                vpn_status = result.stdout
                
                if "Connected" in vpn_status:
                    for line in vpn_status.split('\n'):
                        if "Relay:" in line:
                            vpn_relay = line.split()[1]
                            PANEL_VPN.write_text(vpn_relay)
                            break
                elif "Connecting" in vpn_status:
                    PANEL_VPN.write_text("Connecting")
                elif "Blocked" in vpn_status:
                    PANEL_VPN.write_text("Blocked")
                else:
                    PANEL_VPN.write_text("Unsecured")
            except:
                PANEL_VPN.write_text("Unsecured")
            
            update_vpn()
            render_bar()

def watch_network():
    """Watch network changes"""
    # Initialize network cache
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "type,state,name", "connection", "show", "--active"],
            capture_output=True, text=True, timeout=1
        )
        connection = result.stdout.split('\n')[0] if result.stdout else ""
        
        if "802-11-wireless" in connection:
            PANEL_NETWORK.write_text(connection.split(':')[2] if ':' in connection else "WiFi")
        elif "802-3-ethernet" in connection:
            PANEL_NETWORK.write_text("Wired")
        else:
            PANEL_NETWORK.write_text("Disconnected")
    except:
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
            try:
                result = subprocess.run(
                    ["nmcli", "-t", "-f", "type,state,name", "connection", "show", "--active"],
                    capture_output=True, text=True, timeout=1
                )
                connection = result.stdout.split('\n')[0] if result.stdout else ""
                
                if "802-11-wireless" in connection:
                    PANEL_NETWORK.write_text(connection.split(':')[2] if ':' in connection else "WiFi")
                elif "802-3-ethernet" in connection:
                    PANEL_NETWORK.write_text("Wired")
                else:
                    PANEL_NETWORK.write_text("Disconnected")
            except:
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

def watch_speedtest():
    """Watch speedtest state changes"""
    if not PANEL_SPEEDTEST.exists():
        PANEL_SPEEDTEST.write_text("⊙")
    
    update_speedtest()
    
    proc = subprocess.Popen(
        ["inotifywait", "-m", "-q", "-e", "close_write", str(PANEL_SPEEDTEST)],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            update_speedtest()
            render_bar()

def watch_set():
    """Watch desktop set changes"""
    if not PANEL_SET.exists():
        PANEL_SET.write_text("1")
    
    proc = subprocess.Popen(
        ["inotifywait", "-m", "-q", "-e", "close_write,modify", str(PANEL_SET)],
        stdout=subprocess.PIPE,
        text=True,
        stderr=subprocess.DEVNULL
    )
    if proc.stdout:
        for line in proc.stdout:
            update_desktops()
            render_bar()

if __name__ == "__main__":
    # Initialize all states
    update_desktops()
    update_brightness()
    update_volume()
    update_mic()
    update_battery()
    update_datetime()
    update_vpn()
    update_network()
    update_bluetooth()
    update_speedtest()
    
    # Render initial bar
    render_bar()
    
    # Start all watchers in threads
    threads = [
        threading.Thread(target=watch_desktops, daemon=True),
        threading.Thread(target=watch_brightness, daemon=True),
        threading.Thread(target=watch_volume, daemon=True),
        threading.Thread(target=watch_mic, daemon=True),
        threading.Thread(target=watch_battery, daemon=True),
        threading.Thread(target=watch_battery_percentage, daemon=True),
        threading.Thread(target=watch_datetime, daemon=True),
        threading.Thread(target=watch_date_format, daemon=True),
        threading.Thread(target=watch_vpn, daemon=True),
        threading.Thread(target=watch_network, daemon=True),
        threading.Thread(target=watch_bluetooth, daemon=True),
        threading.Thread(target=watch_speedtest, daemon=True),
        threading.Thread(target=watch_set, daemon=True),
    ]
    
    for thread in threads:
        thread.start()
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
