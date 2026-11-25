# Roadmap

Work here follows bug reports and requests, so if something is broken or
missing for you, open an [issue](https://github.com/PyDevices/omnipython-lvgl/issues).

## Drawing

- On the ESP32-P4, LVGL's drawing uses the chip's Pixel Processing Accelerator
  (`LV_USE_PPA`) for plain fills and simple image copies, kept only where it
  measures faster than drawing in software.
- `lv_conf.h` follows LVGL 9.6's template, so every 9.6 option is listed in
  place with the value this build uses.
