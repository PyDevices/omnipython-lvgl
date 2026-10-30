# Build MicroPython firmware with LVGL

`ports/micropython` in omnipython-lvgl is a MicroPython user C module: it
builds the generated LVGL binding into any MicroPython port. You need `git`,
and whatever MicroPython needs to build for your port. Nothing is generated at
build time.

## Get the source

Clone omnipython-lvgl with its `lvgl` submodule, next to your MicroPython
checkout:

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl
```

The port reads the generated binding, `lv_conf.h` and `lvgl/` from the same
checkout, two directories up from itself. A clone without the submodule stops
the build at once and names the command that fetches it.

## MicroPython 1.29 or later

Add one line to the manifest your build already uses:

```python
include("/path/to/omnipython-lvgl/ports/micropython/manifest.py")
```

On unix that manifest is `ports/unix/variants/standard/manifest.py`. On esp32
and rp2 it is usually `ports/<port>/boards/manifest.py`, unless your board
brings its own. Then build as usual. The include brings in the `lvgl` C module
and freezes `fs_driver`. On the unix port of MicroPython v1.29.0,
`lvgl.version_major()` and `lvgl.version_minor()` report 9 and 5.

To leave the MicroPython tree alone, write a manifest of your own and pass it
as `FROZEN_MANIFEST=`. That replaces the port's default, so include the default
too (`include("$(PORT_DIR)/variants/standard/manifest.py")` on unix,
`include("$(PORT_DIR)/boards/manifest.py")` on esp32), or you lose `asyncio`
and the port's other frozen modules. Passing the port's manifest on its own
works for a quick unix build:

```bash
make -C micropython/ports/unix FROZEN_MANIFEST=/path/to/omnipython-lvgl/ports/micropython/manifest.py
```

## Older than 1.29

Manifests there have no `c_module()`, so use `USER_C_MODULES`, and freeze
`python/fs_driver.py` yourself if you want it. On CMake ports such as esp32 and
rp2, point it at the port's CMake file:

```bash
make BOARD=ESP32_GENERIC_S3 USER_C_MODULES=/path/to/omnipython-lvgl/ports/micropython/micropython.cmake
```

On Make ports such as unix, `USER_C_MODULES` builds every module one directory
below the one you name, and `ports/` also holds the CircuitPython port, so use
MicroPython 1.29 or later there.

## With other user C modules

To build several modules together on any port, name them in one manifest: the
port's `manifest.py` carries `c_module(".")`, and a manifest that `include()`s
several such files builds them all.
[micropython-pydevices](https://github.com/PyDevices/micropython-pydevices)'
`build_mp.py` does that for you: name the modules and it builds them on a
port, with upstream's own boards.

```bash
./build_mp.py --port unix --modules lvgl,pygraphics
```

`lvgl` is this port: `build_mp.py` fetches omnipython-lvgl at the commit its
`modules.lock` pins, or uses an `omnipython-lvgl` checkout beside it. To build
another checkout, name its port by path instead
(`--modules /path/to/omnipython-lvgl/ports/micropython,pygraphics`).

Add `jpegio` when you want JPEG images:
[Show JPEG images](show-jpeg-images.md) says why.

## Check the build

Run the smoke test from your omnipython-lvgl checkout with the interpreter you
built:

```bash
./micropython/ports/unix/build-standard/micropython ./omnipython-lvgl/tools/test_lvgl_smoke.py
```

```text
All LVGL smoke tests passed.
```

`import lvgl_micropython; print(lvgl_micropython.__revision__)` tells you which
omnipython-lvgl commit a firmware was built from.

## Driving the screen

With [pydevices](https://github.com/PyDevices/pydevices) installed, its
`display_driver` drives LVGL from `machine.Timer`. At an interactive prompt,
create your widgets and drop to the prompt: the timer keeps animations, LVGL
timers and touch input running while you inspect variables. A standalone script
calls `app.run()` for an explicit loop.

```python
import display_driver  # noqa: F401 - initializes display, input, and machine.Timer
import lvgl as lv

scr = lv.screen_active()
btn = lv.button(scr)
btn.center()
label = lv.label(btn)
label.set_text("Hello MicroPython LVGL!")
```

Without pydevices, give LVGL a buffer and a flush callback as the
[first program](../get-started/first-program.md) does.
