# Install

LVGL reaches Python three ways, one per interpreter, all from
[omnipython-lvgl](https://github.com/PyDevices/omnipython-lvgl). Pick the
section for the one you use. All three give you `import lvgl as lv` with the
same API.

| You use | You get it by |
|---|---|
| CPython on a desktop | `pip install omnipython-lvgl` |
| MicroPython-compatible firmware | building firmware with `ports/micropython` |
| CircuitPython-compatible firmware | building firmware with `ports/circuitpython` |

## CPython

The wheel is `omnipython-lvgl` on PyPI.

```bash
python -m pip install omnipython-lvgl
```

Check it:

```bash
python -c "import lvgl as lv; lv.init(); lv.deinit(); print('ok')"
```

```text
ok
```

CI builds a wheel per CPython minor version (3.11 to 3.15, and the
free-threaded 3.15t) for Linux x86_64, Linux aarch64 (64-bit Raspberry Pi OS,
for one) and Windows x64. There are Android
wheels for 3.13 and 3.14 (`android_21_arm64_v8a` and `android_21_x86_64`) and a
Pyodide wheel for the browser. pip picks the tag that matches your interpreter;
use the same `pip` and `python` you will run.

The binding has run on a Raspberry Pi 4 and a Pi 3 B+. A Pi 5 runs the same
64-bit Raspberry Pi OS and should take the same aarch64 wheel, but nobody has
tried it yet. If you do, [open an issue](https://github.com/PyDevices/omnipython-lvgl/issues)
and say what worked.

Pin a version with `omnipython-lvgl==9.6.1`. For an Android build, ask pip for
the platform:

```bash
pip install --only-binary=:all: --platform android_21_arm64_v8a omnipython-lvgl
```

In Pyodide, install with micropip:

```python
import micropip
await micropip.install("omnipython-lvgl")
```

On Windows Python from WSL, use `pip.exe` and `python.exe` the same way:

```bash
pip.exe install omnipython-lvgl
python.exe -c "import lvgl as lv; lv.init(); lv.deinit(); print('ok')"
```

An older `omnipython-lvgl` wheel carried `display_driver.py`, which ships in
`omnipython`. Upgrade both in one command, `pip install -U omnipython omnipython-lvgl`.
Upgraded on its own after an `omnipython` that already has the file, pip's
uninstall of the old `omnipython-lvgl` deletes the `display_driver.py` both
wheels wrote; `pip install --force-reinstall --no-deps omnipython` puts it back.

No wheel for your platform? [Build it from source](../guides/build-the-cpython-extension-from-source.md).

## MicroPython-compatible firmware

LVGL is a user C module, so it comes with a firmware build. Clone
omnipython-lvgl, with its `lvgl` submodule, next to your MicroPython checkout:

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl
```

On MicroPython 1.29 or later, add one line to the manifest your build already
uses. For the unix port that is `ports/unix/variants/standard/manifest.py`:

```python
include("/path/to/omnipython-lvgl/ports/micropython/manifest.py")
```

Then build as usual, and `import lvgl` works on the result:

```bash
cd micropython/ports/unix
make
```

[Build MicroPython firmware with LVGL](../guides/build-micropython-firmware-with-lvgl.md)
has the other ports, older MicroPython, and building with other modules.

## CircuitPython-compatible firmware

CircuitPython 11 builds user C modules the way MicroPython does, so you hand
`ports/circuitpython` to CircuitPython's own `make` and nothing in the
CircuitPython tree changes:

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl
make -C circuitpython/ports/unix VARIANT=coverage USER_C_MODULES=/path/to/omnipython-lvgl/ports/circuitpython
```

For a board, `CIRCUITPY_GIFIO=0` goes on the same line, and LVGL adds about
1 MB of firmware, so check the app partition.
[Build CircuitPython firmware with LVGL](../guides/build-circuitpython-firmware-with-lvgl.md)
has the details.

## What each install gives you

The three builds share one binding, so everything after `import lvgl as lv`
is the same. What differs is how the screen is driven. On a board, or on a
desktop with PyDevices, the `display_driver` helper from
[omnipython](https://github.com/PyDevices/omnipython) wires LVGL to the display
and touch for you. Without it, you give LVGL a buffer and a flush callback, as
[the first program](first-program.md) does.
