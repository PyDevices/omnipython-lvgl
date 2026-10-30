![A blue button reading Hello from LVGL on a light gray background](docs/images/hello.png)

# omnipython-lvgl

omnipython-lvgl is the part of OmniPython that gives CPython,
MicroPython-compatible and CircuitPython-compatible programs the same
`import lvgl as lv`, from one set of bindings generated from LVGL's headers.

On a desktop, install the wheel:

```bash
python -m pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pydevices-lvgl
```

On a board, LVGL comes with your firmware build. Clone this repository with
its `lvgl` submodule, then hand `ports/micropython` or `ports/circuitpython` to
the interpreter's own build:

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl
make -C micropython/ports/unix FROZEN_MANIFEST=$PWD/omnipython-lvgl/ports/micropython/manifest.py
make -C circuitpython/ports/unix USER_C_MODULES=$PWD/omnipython-lvgl/ports/circuitpython
```

```python
import lvgl as lv

lv.init()
disp = lv.display_create(240, 120)
disp.set_color_format(lv.COLOR_FORMAT.RGB565)
buf = bytearray(240 * 120 * 2)
disp.set_buffers(buf, None, len(buf), lv.DISPLAY_RENDER_MODE.FULL)
flushed = []
disp.set_flush_cb(lambda d, area, px: (flushed.append(area.get_width()), d.flush_ready()))

button = lv.button(lv.screen_active())
button.center()
label = lv.label(button)
label.set_text("Hello from LVGL")
button.add_event_cb(lambda e: print("clicked"), lv.EVENT.CLICKED, None)
button.send_event(lv.EVENT.CLICKED, None)

lv.tick_inc(50)
lv.refr_now(disp)
print(label.get_text(), "- drew", flushed[-1], "px wide")
```

```text
clicked
Hello from LVGL - drew 240 px wide
```

The picture at the top is the frame that program drew.

[Docs](docs/index.md) · [Examples](https://pydevices.github.io/gallery/pyscript/) · [Roadmap](ROADMAP.md)

OmniPython is made by [PyDevices](https://pydevices.com).
