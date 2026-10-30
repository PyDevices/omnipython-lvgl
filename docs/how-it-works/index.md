# How the LVGL builds fit together

One generator turns LVGL's headers into bindings for three Pythons. Each
interpreter has its own port, in the same repository, that builds those
bindings into something you install or flash.

```text
LVGL headers + lv_conf.h
        |
        v
binding/: generator, API model -> generated/ C sources and lvgl.pyi
        |
        +--> setup.py, ports/cpython/   CPython extension, pydevices-lvgl wheels
        +--> ports/micropython/         MicroPython user C module
        +--> ports/circuitpython/       CircuitPython user C module
```

## The pieces

- **The generator** in `binding/` writes the C bindings (`generated/lvgl_*.c`)
  and the type stub (`lvgl.pyi`) for all three targets. They are committed, so
  a build compiles them and generates nothing.
- **The CPython port** compiles the CPython binding with its runtime layer
  into the `pydevices-lvgl` wheels, the one thing here that is published as a
  package.
- **The MicroPython and CircuitPython ports** compile the generated bindings
  into firmware, as user C modules, and publish no package of their own.

All three read the same `generated/`, `lv_conf.h`, `lvgl/` submodule and
`python/` helpers, so any one commit of the repository builds every
interpreter from the same binding. A release covers all of it at once.

## Why one binding

The ports share the same parsed declarations, the same API model, the same
inheritance order and the same diagnostics policy. MicroPython and
CircuitPython share the `mp_obj_t` lowering because CircuitPython embeds the
same object API, and keep their own registration and VM or garbage collector
glue. CPython gets native `PyObject *` code with its own GIL, lock and module
initialization. The runtimes differ in mechanism and not in what you can call:
an API difference has to be a recorded exception, not a side effect of one
port's build system. [Generator architecture](generator-architecture.md) has
the pipeline.

## The pages for each port

- [The CPython port](cpython-port.md): the runtime layer, ownership and callbacks.
- [The MicroPython port](micropython-port.md): the user module and its allocator.
- [The CircuitPython port](circuitpython-port.md): the user module and its JPEG decoder.

## Driving the display

The binding does not choose a display, an event loop or a board. For that,
pydevices has a `display_driver` module that wires LVGL to a `board_config`:
display flush, input devices and the event loop. It ships with
[pydevices](https://github.com/PyDevices/pydevices), because it needs that
package's `appdev`, `events`, `keys` and `multimer`, and the bindings don't. You
can also use the bindings with plumbing of your own, as
[the first program](../get-started/first-program.md) does.
