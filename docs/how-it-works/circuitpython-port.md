# The CircuitPython port

`ports/circuitpython` integrates the generated LVGL bindings into a
CircuitPython firmware build. It supplies the user C module glue, a GC-aware
LVGL allocator and a CircuitPython-specific JPEG decoder. It is not a pip
package and generates nothing: it reads the generated source and header,
`lv_conf.h` and `lvgl/` from the checkout it sits in, two directories up.

[Build CircuitPython firmware with LVGL](../guides/build-circuitpython-firmware-with-lvgl.md)
shows how to use it.

## The pieces

```text
generated/lvgl_circuitpython.c and .h, lv_conf.h, lvgl/
                  |
                  v
ports/circuitpython user C module glue
                  |
                  +--> CircuitPython shared-bindings and shared-module for lvgl
                  +--> generated C source and header, and the allocator
                  +--> manifest.py (freezes fs_driver when the build
                  |    passes it via FROZEN_MANIFEST)
                  |
                  v
CircuitPython firmware + pydevices: import display_driver, then import lvgl
```

## Why the application pumps LVGL

CircuitPython has no `machine.Timer` for this, so after importing
`display_driver` and `lvgl` the application runs `app.run()` or its own
`asyncio` loop to keep LVGL's tasks and events moving.

## The JPEG decoder

LVGL's JPEG support here is CircuitPython's `jpegio`, not LVGL's bundled TJpgDec.
The bindings' `lv_conf.h` sets `LV_USE_TJPGD 0` on CircuitPython, so LVGL's own
`libs/tjpgd` compiles to nothing. `src/lv_jpegio_decoder_circuitpython.c` then
registers CircuitPython's `lib/tjpgd` (compiled whenever `CIRCUITPY_JPEGIO=1`)
as LVGL's decoder through the public `lv_image_decoder_create` API. That gives
each firmware one TJpgDec. Without `CIRCUITPY_JPEGIO` the firmware still links,
and has no JPEG decoder for LVGL. `lv.tjpgd_init` does not exist on
CircuitPython. [Show JPEG images](../guides/show-jpeg-images.md) has the details
you need to use it.
