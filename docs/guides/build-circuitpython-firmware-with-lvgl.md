# Build CircuitPython firmware with LVGL

`ports/circuitpython` in omnipython-lvgl is a user C module for CircuitPython.
CircuitPython 11 builds user C modules the way MicroPython does, so you hand
that directory to any port's `make` as `USER_C_MODULES` and nothing in the
CircuitPython tree is patched.

## Get the sources

Pick a release tag from the
[CircuitPython releases](https://github.com/adafruit/circuitpython/releases),
and fetch its submodules:

```bash
git clone --branch 11.0.0-alpha.1 https://github.com/adafruit/circuitpython.git circuitpython
cd circuitpython
make fetch-all-submodules
cd ..
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl.git
```

The port reads the generated binding, `lv_conf.h` and `lvgl/` from the same
checkout, two directories up from itself, so there is nothing to generate or
fetch. A clone without the `lvgl` submodule stops the build at once and names
the command that fetches it.

## Install the toolchain

Install CircuitPython's build tools and cross-compilers before building. This
repository doesn't do it for you: follow CircuitPython's
[BUILDING.md](https://github.com/adafruit/circuitpython/blob/main/BUILDING.md)
and Adafruit's
[Building CircuitPython](https://learn.adafruit.com/building-circuitpython/linux)
guide. For an Arm board you need `gcc-arm-none-eabi`; check
`arm-none-eabi-gcc --version` after installing.

Create a Python venv for CircuitPython's `requirements-dev.txt`, which
provides `minify_html` and related tools (if `minify_html` fails to install,
you may need Rust):

```bash
python3 -m venv .venv
.venv/bin/pip install -r circuitpython/requirements-dev.txt
export PATH="$(pwd)/.venv/bin:$PATH"
```

## Build for the unix port or a board

```bash
make -C circuitpython/ports/unix VARIANT=coverage \
    USER_C_MODULES=/path/to/omnipython-lvgl/ports/circuitpython
make -C circuitpython/ports/raspberrypi BOARD=<board> CIRCUITPY_GIFIO=0 \
    USER_C_MODULES=/path/to/omnipython-lvgl/ports/circuitpython
```

Add `FROZEN_MANIFEST=/path/to/omnipython-lvgl/ports/circuitpython/manifest.py`
to freeze the `fs_driver` helper as well.

`CIRCUITPY_GIFIO=0` is for boards: LVGL links its own AnimatedGIF decoder, which
collides with `gifio`'s. The build stops with a message if you forget it.

LVGL adds about 1 MB to the firmware, more than most boards' default firmware
region holds, so a board with a small app partition needs a bigger one. LVGL's
qstrs also need CircuitPython's four-byte qstr offsets
(`MICROPY_QSTR_OFFSET_BYTES`), which `micropython.mk` sets on ports that have
them. For a worked example with a partition table, see
[Flash LVGL CircuitPython on a Qualia](flash-lvgl-circuitpython-on-a-qualia.md).

## Build with other PyDevices modules

[micropython-pydevices](https://github.com/PyDevices/micropython-pydevices)'
`build_mp.py` fetches CircuitPython, passes the modules you name to its make as
`USER_C_MODULES`:

```bash
./build_mp.py --interpreter circuitpython --port unix \
    --modules /path/to/omnipython-lvgl/ports/circuitpython,pygraphics
```

`--modules` takes a short name for each module that lives in
micropython-pydevices and a full path for one that doesn't, such as this
port. The binary lands in `builds/circuitpython/unix/coverage/`.

For a board, name CircuitPython's port and board, and put `CIRCUITPY_GIFIO=0`
at the end:

```bash
./build_mp.py --interpreter circuitpython --port espressif \
    --board <board> --modules /path/to/omnipython-lvgl/ports/circuitpython CIRCUITPY_GIFIO=0
```

## Check the build

Run the smoke test from your omnipython-lvgl checkout with the interpreter you
built (`build-coverage/micropython` for the unix `make` line above):

```bash
./circuitpython/ports/unix/build-coverage/micropython ./omnipython-lvgl/tools/test_lvgl_smoke.py
```

```text
All LVGL smoke tests passed.
```

## Driving the screen

CircuitPython has no `machine.Timer`, so the application pumps LVGL: `app.run()`
or your own `asyncio` loop. With [pydevices](https://github.com/PyDevices/pydevices),
`display_driver` does the wiring. Put pydevices on the board as source
(`--no-mpy`), with your `board_config`:

```python
import display_driver  # noqa: F401 - initializes display and input
import lvgl as lv
from display_driver import app

scr = lv.screen_active()
label = lv.label(scr)
label.set_text("Hello CircuitPython LVGL!")
label.center()

app.run()
```

`display_driver` wants a `board_config` unless your code has already created an
`appdev.App`. To skip pydevices, give LVGL a buffer and a flush callback as the
[first program](../get-started/first-program.md) does.

JPEG images need `CIRCUITPY_JPEGIO` on: [Show JPEG images](show-jpeg-images.md).
