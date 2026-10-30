# The MicroPython port

`ports/micropython` is the MicroPython build glue for LVGL. It combines the
generated LVGL binding with MicroPython user-module build files and a GC-aware
allocator. It publishes no package of its own and generates nothing: it reads
the generated binding, `lv_conf.h` and `lvgl/` from the checkout it sits in,
two directories up.

[Build MicroPython firmware with LVGL](../guides/build-micropython-firmware-with-lvgl.md)
shows how to use it.

## The pieces

```text
generated/lvgl_micropython.c, lv_conf.h, lvgl/
                         |
                         v
ports/micropython build glue + GC-aware allocator
                         |
                         v
MicroPython firmware module: import lvgl
                         |
                         v
pydevices' display_driver -> display, input, timers
```

The build glue is `micropython.mk` for Make ports and `micropython.cmake` for
CMake ports. The allocator, `lv_mem_core_micropython.c`, gives LVGL its memory
from the MicroPython garbage-collected heap. A small `lvgl_micropython` module
carries the `__revision__` of the build.

Because the port and the binding share one checkout, a firmware is always
built from one commit of both, and `lvgl_micropython.__revision__` names it.

## Where JPEG fits

LVGL can always draw PNG and its BIN format. JPEG needs the jpegio module in the
same firmware, which registers its decoder when it sees this user module. A
build without it skips JPEGs at run time rather than failing at build time.
[Show JPEG images](../guides/show-jpeg-images.md) has the details.

## Driving the display

`display_driver` is pydevices', not this firmware's. It wires the display,
input and timers, and wants a `board_config` unless your code has already
created an `appdev.App`. At an interactive MicroPython prompt, hardware timer
callbacks keep LVGL active after the script reaches the prompt.
