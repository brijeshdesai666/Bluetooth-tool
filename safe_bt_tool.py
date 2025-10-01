#!/usr/bin/env python3
"""
safe_bt_tool.py

- Shows discoverable devices and connected devices.
- Provides a non-destructive "attack" interface:
    * simulation mode (default) - prints actions it WOULD take.
    * safe probe mode ("AUTHORIZED_TESTING=1" required) - runs a limited l2ping count (non-flood).
- DOES NOT perform floods or denial-of-service operations.
"""

import subprocess
import re
import os
import threading
import time

# ---------- Utilities ----------
def run_cmd(cmd_list, timeout=5):
    try:
        out = subprocess.check_output(cmd_list, stderr=subprocess.DEVNULL, timeout=timeout)
        return out.decode(errors="ignore")
    except Exception:
        return ""

# ---------- Scanning ----------
def parse_hcitool_scan(output):
    devices = {}
    for line in output.splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        parts = re.split(r'\s+', line, maxsplit=1)
        if len(parts) == 2:
            mac, name = parts
            devices[mac.upper()] = name.strip()
    return devices

def get_hcitool_scan():
    return parse_hcitool_scan(run_cmd(["hcitool", "scan"]))

def parse_hcitool_con(output):
    devices = {}
    for line in output.splitlines():
        m = re.search(r'([0-9A-F:]{17})', line, re.I)
        if m:
            mac = m.group(1).upper()
            name = run_cmd(["hcitool", "name", mac]).strip() or "(unknown)"
            devices[mac] = name
    return devices

def get_hcitool_con():
    return parse_hcitool_con(run_cmd(["hcitool", "con"]))

def parse_bluetoothctl_devices(output):
    devices = {}
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("Device "):
            try:
                _, rest = line.split("Device ", 1)
                mac, name = rest.split(" ", 1)
                devices[mac.upper()] = name.strip()
            except ValueError:
                continue
    return devices

def get_bluetoothctl_connected():
    return parse_bluetoothctl_devices(run_cmd(["bluetoothctl", "devices", "Connected"]))

def scan_devices():
    """Return dict MAC -> name for discoverable and/or connected devices."""
    results = {}
    try:
        results.update(get_hcitool_scan())
    except Exception:
        pass
    try:
        con = get_hcitool_con()
        for mac, name in con.items():
            results.setdefault(mac, name)
    except Exception:
        pass
    try:
        bt = get_bluetoothctl_connected()
        for mac, name in bt.items():
            results.setdefault(mac, name)
    except Exception:
        pass
    return results

# ---------- "Attack" functionality (SAFE) ----------
def simulate_attack(mac, name):
    """Prints a safe simulation message for the target."""
    print(f"[SIMULATION] Would start DoS-style l2ping flood on {name} ({mac}) — NOT RUNNING.")

def safe_probe(mac, name, count=4):
    """
    Runs a limited l2ping probe (non-flooding) to check reachability.
    This is intentionally small and only runs when AUTHORIZED_TESTING=1 is set.
    """
    if os.environ.get("AUTHORIZED_TESTING") != "1":
        print("[ERROR] Safe probe blocked. To allow non-destructive probe set AUTHORIZED_TESTING=1 in the environment.")
        return

    print(f"[PROBE] Running {count} l2ping packets to {name} ({mac})...")
    try:
        # limited pings only; do NOT use -f or continuous flood switches
        subprocess.call(["l2ping", "-c", str(count), mac])
    except FileNotFoundError:
        print("[ERROR] l2ping not found on PATH.")
    except Exception as e:
        print(f"[ERROR] Probe failed: {e}")

def start_safe_actions(devices, mode="simulate"):
    """
    mode:
      - "simulate" : only prints what it would do (safe default)
      - "probe"    : runs safe_probe (requires AUTHORIZED_TESTING=1 env var)
    """
    threads = []
    for mac, name in devices.items():
        if mode == "simulate":
            t = threading.Thread(target=simulate_attack, args=(mac, name))
        elif mode == "probe":
            t = threading.Thread(target=safe_probe, args=(mac, name))
        else:
            raise ValueError("Unknown mode")
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(0.3)
    # join threads briefly so user sees output
    for t in threads:
        t.join(timeout=2)

# ---------- CLI ----------
def main():
    os.system("clear")
    print("==== Bluetooth Safe Scanner & Tester ====\n")
    devices = scan_devices()
    if not devices:
        print("[*] No Bluetooth devices found (discoverable or connected).")
        return

    print("Devices (discoverable OR currently connected):")
    for i, (mac, name) in enumerate(devices.items(), start=1):
        print(f"{i}. {name} - {mac}")

    print("\nChoose action:")
    print("  1) Simulate 'attack' on ALL devices (safe)")
    print("  2) Safe probe (limited l2ping count) on ALL devices (requires AUTHORIZED_TESTING=1)")
    print("  3) Probe a single device")
    print("  q) Quit")

    choice = input("> ").strip().lower()
    if choice == "1":
        start_safe_actions(devices, mode="simulate")
    elif choice == "2":
        start_safe_actions(devices, mode="probe")
    elif choice == "3":
        sel = input("Enter device number: ").strip()
        try:
            idx = int(sel) - 1
            mac = list(devices.keys())[idx]
            name = devices[mac]
            if os.environ.get("AUTHORIZED_TESTING") != "1":
                print("[WARNING] Safe probe blocked. Set AUTHORIZED_TESTING=1 to permit non-destructive probes.")
                print("[SIMULATION] Showing simulated action instead.")
                simulate_attack(mac, name)
            else:
                safe_probe(mac, name)
        except Exception:
            print("[ERROR] Invalid selection.")
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()
