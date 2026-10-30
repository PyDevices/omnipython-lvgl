# LVGL for Python

[LVGL](https://lvgl.io/) is a C graphics library for small displays.
omnipython-lvgl lets you drive it from Python, on a desktop with CPython and on a
board with MicroPython-compatible or CircuitPython-compatible firmware. All
three share one API, generated from LVGL's headers, so a program you write
against `import lvgl as lv` runs on each.

```python
import lvgl as lv

lv.init()
disp = lv.display_create(240, 120)
# ... a button and a label, as in the first program
```

[Install it](get-started/install.md) for the Python you use, then run
[your first program](get-started/first-program.md). The
[guides](guides/use-lvgl-from-threads.md) take one task each, the
[reference](reference/index.md) lists the names and the fonts, and
[How it works](how-it-works/index.md) explains how the three builds relate.

## Get started

- [Install](get-started/install.md)
- [Your first program](get-started/first-program.md)

## Guides

- [Use LVGL from threads](guides/use-lvgl-from-threads.md)
- [Show JPEG images](guides/show-jpeg-images.md)
- [Build the CPython extension from source](guides/build-the-cpython-extension-from-source.md)
- [Build MicroPython firmware with LVGL](guides/build-micropython-firmware-with-lvgl.md)
- [Build CircuitPython firmware with LVGL](guides/build-circuitpython-firmware-with-lvgl.md)
- [Flash LVGL CircuitPython on a Qualia](guides/flash-lvgl-circuitpython-on-a-qualia.md)

## Reference

- [Reference](reference/index.md)
- [Fonts](reference/fonts.md)

## How it works

- [How the LVGL builds fit together](how-it-works/index.md)
- [Generator architecture](how-it-works/generator-architecture.md)
- [The CPython port](how-it-works/cpython-port.md)
- [The MicroPython port](how-it-works/micropython-port.md)
- [The CircuitPython port](how-it-works/circuitpython-port.md)

## Changelog

- [Changelog](changelog.md)
