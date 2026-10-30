# Hand-written Python helpers

Pure-Python modules that ship with the LVGL bindings. These are **not**
generator output: edit them here, and every build picks up the change.

| File | Import | Notes |
|------|--------|-------|
| `fs_driver.py` | `import fs_driver` | Python-backed `lv_fs` driver: `fs_driver.register("S")`, then `lv.binfont_create("S:fonts/x.bin")` streams from the platform filesystem. Pairs with the runtime-loadable fonts in [`../fonts/`](../fonts/) |

`display_driver.py`, the coordinator that wires LVGL to a PyDevices
`board_config`, lives in
[PyDevices/pydevices `lib/`](https://github.com/PyDevices/pydevices/blob/main/lib/display_driver.py)
and ships with `pydevices`, beside the `appdev`, `events`, `keys` and `multimer`
it needs.

## How it ships

| Build | How it ships |
|------|--------------|
| MicroPython | Frozen by [`ports/micropython/manifest.py`](../ports/micropython/manifest.py) |
| CircuitPython | Frozen by [`ports/circuitpython/manifest.py`](../ports/circuitpython/manifest.py), when the build passes it as `FROZEN_MANIFEST` |
| CPython | `py_modules` in the `pydevices-lvgl` wheel |

## MIP (optional)

```text
mip.install("github:PyDevices/omnipython-lvgl/packages/fs_driver.json")
```

`display_driver` comes with `mip.install("pydevices", index="https://PyDevices.github.io/mip")`.
