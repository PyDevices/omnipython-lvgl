# Frozen Python helpers that ship with the LVGL CircuitPython integration:
# fs_driver.py, kept once at the root of this repository in python/. LVGL's
# PyDevices coordinator, display_driver.py, ships with pydevices (lib/): put
# pydevices on CIRCUITPY as source, as you do for appdev, events and keys.
#
# Freeze-only: upstream port/board/variant frozen modules come from a
# workspace aggregator via FROZEN_MANIFEST_UPSTREAM.

module("fs_driver.py", base_path="../../python", opt=3)
