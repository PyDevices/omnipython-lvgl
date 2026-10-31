# Roadmap

Work here follows bug reports and requests, so if something is broken or
missing for you, open an [issue](https://github.com/PyDevices/omnipython-lvgl/issues).
Two larger changes are planned:

- Vector graphics: enable `LV_USE_VECTOR_GRAPHIC` with ThorVG, so `lv.vector_*`
  and SVG drawing work from Python. ThorVG adds real code size, so for the MCU
  builds this is a build-size question to measure per board, not a quick flip.
- Linux wheels for 64-bit ARM (`manylinux_aarch64`), so `pip install` works on
  a Raspberry Pi and other ARM Linux boards. Today Linux wheels are x86_64 only.
