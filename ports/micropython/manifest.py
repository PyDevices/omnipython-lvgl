# Frozen Python helpers that ship with the LVGL MicroPython usermod: fs_driver.py,
# kept once at the root of this repository in python/. LVGL's PyDevices
# coordinator, display_driver.py, ships with pydevices (lib/).
#
# This file only freezes usermod helpers and names the C module. Upstream
# port/board/variant frozen modules come from your own manifest, which pulls
# this one in with include("<repo>/ports/micropython/manifest.py").

module("fs_driver.py", base_path="../../python", opt=3)

# MicroPython 1.29: the manifest names its own C module.
c_module(".")  # this directory holds the micropython.cmake / micropython.mk for the C half
