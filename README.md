# Safe Bluetooth Scanner & Tester

A Python tool for scanning and safely testing nearby Bluetooth devices, built with explicit safety guardrails to avoid misuse as an actual attack tool.

## What It Does

- Scans for discoverable and currently connected Bluetooth devices (via hcitool and bluetoothctl)
- Lists found devices with name and MAC address
- Offers two non-destructive interaction modes:
  - Simulation mode (default): only prints what an action would do, takes no real action
  - Safe probe mode: sends a small, limited number of l2ping packets to check reachability (no flooding), and only runs if AUTHORIZED_TESTING=1 is explicitly set

## What It Does NOT Do

This tool deliberately does not perform any flooding, denial-of-service, or destructive operations, by design, not just by default.

## Requirements

- Linux environment with hcitool and bluetoothctl installed
- Python 3

## Usage

    python safe_bt_tool.py

To enable safe probing:

    export AUTHORIZED_TESTING=1
    python safe_bt_tool.py

## Disclaimer

Intended strictly for testing devices you own or have explicit authorization to test.
