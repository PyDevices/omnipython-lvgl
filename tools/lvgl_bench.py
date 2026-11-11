# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Time LVGL's rendering and measure its memory, the same way on every interpreter.

Run it on a board (MicroPython or CircuitPython) after a soft reset, so the
heap holds nothing but this script, or with CPython on a desktop. It prints
one ``BENCH`` line per measurement and a ``BENCH_RESULT=`` JSON line at the
end, so two builds can be compared line by line.

What it measures:

* free heap before ``import lvgl``, after it, and after the board's display
  starts (``board_config`` and ``display_driver``), where there is one;
* the heap each scene's widgets take;
* the median time of one refresh (``lv.refr_now``) for four fixed scenes:
  a full-screen redraw, a scrolling list, rotated and scaled images, and
  wrapped text. Each scene is timed on an off-screen display whose flush does
  nothing ("render": LVGL alone) and, when the board has a display, on the
  board's own ("screen": LVGL and the panel transfer).

``lv.mem_monitor`` reports nothing under the MicroPython and CircuitPython
allocators, which take LVGL's memory from the garbage-collected heap, so the
heap figures are the measure of LVGL's memory there. CPython reports the
process's resident memory instead.

Usage::

    python tools/lvgl_bench.py            # CPython: off-screen display only
    mpftp run tools/lvgl_bench.py --follow   # a board, after mpftp soft-reset

Pass ``render`` on the command line, or set ``LVGL_BENCH_RENDER_ONLY``, to
skip the board's display.
"""

import gc
import sys

try:
    from time import ticks_diff, ticks_us
except ImportError:
    try:
        from time import perf_counter_ns as _ns
    except ImportError:
        from time import monotonic_ns as _ns

    def ticks_us():
        return _ns() // 1000

    def ticks_diff(a, b):
        return a - b


RUNS = 7
_ANIM_OFF = 0  # lv_anim_enable_t is a bool in LVGL 9: LV_ANIM_OFF is false
SCROLL_STEPS = 12
WIDTH, HEIGHT = 800, 480  # the off-screen display when there is no board display

_results = {}


def _free():
    """Free heap in bytes, after a collection; None where it can't be read."""
    gc.collect()
    mem_free = getattr(gc, "mem_free", None)
    if mem_free is not None:
        return mem_free()
    try:
        with open("/proc/self/statm") as f:
            # resident pages, negated so that "free" falls as memory is used
            return -int(f.read().split()[1]) * 4096
    except (OSError, ValueError, IndexError):
        return None


def _report(key, value, unit):
    _results[key] = value
    print("BENCH %s %s %s" % (key, value, unit))


def _median(values):
    values = sorted(values)
    return values[len(values) // 2]


def _render_only():
    if any(arg == "render" for arg in sys.argv[1:]):
        return True
    try:
        import os

        return bool(os.getenv("LVGL_BENCH_RENDER_ONLY"))
    except (ImportError, AttributeError):
        return False


free_start = _free()
import lvgl as lv  # noqa: E402

free_lvgl = _free()

screen_disp = None
if not _render_only():
    try:
        import board_config  # noqa: F401
        import display_driver

        screen_disp = lv.display_get_default()
        inst = display_driver.event_loop.current_instance()
        if inst is not None:
            # The bench drives every refresh itself.
            inst.disable()
    except ImportError as exc:
        print("BENCH no board display: %s" % exc)
free_display = _free()

if not lv.is_initialized():
    lv.init()

_report("lvgl_version", "%d.%d.%d" % (lv.version_major(), lv.version_minor(), lv.version_patch()), "")
_report("platform", sys.platform, "")
_report("implementation", sys.implementation.name, "")
if free_start is not None:
    _report("heap_free_start", free_start, "B")
    _report("heap_import_lvgl", free_start - free_lvgl, "B")
    _report("heap_display_init", free_lvgl - free_display, "B")
    _report("heap_free_after_display", free_display, "B")

if screen_disp is not None:
    WIDTH = screen_disp.get_horizontal_resolution()
    HEIGHT = screen_disp.get_vertical_resolution()
_report("resolution", "%dx%d" % (WIDTH, HEIGHT), "")


def _flush(disp, area, color_p):
    disp.flush_ready()


def _offscreen_display():
    """A display the size of the board's whose flush does nothing, so a
    refresh times LVGL's drawing alone. Its draw buffer is a tenth of the
    screen, rendered in partial mode, as most boards' are."""
    disp = lv.display_create(WIDTH, HEIGHT)
    disp.set_color_format(lv.COLOR_FORMAT.RGB565)
    rows = max(1, HEIGHT // 10)
    buf = lv.draw_buf_create(WIDTH, rows, lv.COLOR_FORMAT.RGB565, 0)
    disp.set_draw_buffers(buf, None)
    disp.set_render_mode(lv.DISPLAY_RENDER_MODE.PARTIAL)
    disp.set_flush_cb(_flush)
    return disp, buf


free_before_offscreen = _free()
render_disp, render_buf = _offscreen_display()
if free_before_offscreen is not None:
    _report("heap_offscreen_display", free_before_offscreen - _free(), "B")


def _time_refresh(disp, before=None, runs=RUNS):
    """The median microseconds of one refresh of `disp`. `before(i)` runs
    first each time, inside the timing: a scroll step or a text change is part
    of the work a refresh pays for."""
    times = []
    for i in range(runs):
        t0 = ticks_us()
        if before is not None:
            before(i)
        lv.refr_now(disp)
        times.append(ticks_diff(ticks_us(), t0))
    return _median(times)


def _font(size):
    return getattr(lv, "font_montserrat_%d" % size, None) or lv.font_get_default()


# --- scenes: each builds a screen on the display that is default ---------


def scene_full(scr):
    """A gradient background, a grid of twelve buttons, an arc, a slider and a bar."""
    scr.set_style_bg_color(lv.color_hex(0x203040), 0)
    scr.set_style_bg_grad_color(lv.color_hex(0x80A0C0), 0)
    scr.set_style_bg_grad_dir(lv.GRAD_DIR.VER, 0)
    scr.set_flex_flow(lv.FLEX_FLOW.ROW_WRAP)
    scr.set_style_pad_all(8, 0)
    scr.set_style_pad_gap(8, 0)
    bw = (WIDTH - 8 * 5) // 4
    bh = (HEIGHT - 8 * 5) // 5
    for i in range(12):
        btn = lv.button(scr)
        btn.set_size(bw, bh)
        btn.set_style_radius(12, 0)
        btn.set_style_shadow_width(10, 0)
        label = lv.label(btn)
        label.set_text("Button %d" % i)
        label.center()
    arc = lv.arc(scr)
    arc.set_size(bh, bh)
    arc.set_value(70)
    slider = lv.slider(scr)
    slider.set_width(bw * 2)
    slider.set_value(40, _ANIM_OFF)
    bar = lv.bar(scr)
    bar.set_width(bw)
    bar.set_value(60, _ANIM_OFF)
    return None


def scene_list(scr):
    """A full-screen column of 40 rows, each a card with two labels; the timing scrolls it."""
    col = lv.obj(scr)
    col.set_size(WIDTH, HEIGHT)
    col.set_flex_flow(lv.FLEX_FLOW.COLUMN)
    col.set_style_pad_gap(4, 0)
    for i in range(40):
        row = lv.obj(col)
        row.set_size(lv.pct(100), 48)
        row.set_style_radius(8, 0)
        row.set_style_border_width(1, 0)
        row.remove_flag(lv.obj.FLAG.SCROLLABLE)
        title = lv.label(row)
        title.set_text("Row %d" % i)
        title.align(lv.ALIGN.LEFT_MID, 0, 0)
        detail = lv.label(row)
        detail.set_text("detail text for row %d" % i)
        detail.align(lv.ALIGN.RIGHT_MID, 0, 0)
    col.update_layout()
    return col


_IMG = 128
_img_data = None


def _image_dsc():
    """An RGB565 test card, 128 pixels square, made here so no file is needed."""
    global _img_data
    data = bytearray(_IMG * _IMG * 2)
    for y in range(_IMG):
        for x in range(_IMG):
            r = (x * 31) // (_IMG - 1)
            g = (y * 63) // (_IMG - 1)
            b = 31 if ((x // 16) + (y // 16)) & 1 else 0
            v = (r << 11) | (g << 5) | b
            i = (y * _IMG + x) * 2
            data[i] = v & 0xFF
            data[i + 1] = v >> 8
    _img_data = data
    return lv.image_dsc_t(
        {
            "header": {
                "magic": lv.IMAGE_HEADER_MAGIC,
                "cf": lv.COLOR_FORMAT.RGB565,
                "w": _IMG,
                "h": _IMG,
                "stride": _IMG * 2,
            },
            "data_size": len(data),
            "data": data,
        }
    )


_dsc = None


def scene_image(scr):
    """Three copies of the test card: rotated 30 degrees, scaled 1.5 times, and both."""
    global _dsc
    if _dsc is None:
        _dsc = _image_dsc()
    scr.set_style_bg_color(lv.color_hex(0xFFFFFF), 0)
    for i, (angle, scale) in enumerate(((300, 256), (0, 384), (450, 320))):
        img = lv.image(scr)
        img.set_src(_dsc)
        img.set_pivot(_IMG // 2, _IMG // 2)
        img.set_rotation(angle)
        img.set_scale(scale)
        img.set_antialias(True)
        img.align(lv.ALIGN.LEFT_MID, (WIDTH * (2 * i + 1)) // 6 - _IMG // 2, 0)
    return None


_TEXT = (
    "LVGL draws every glyph of this paragraph again on each refresh. "
    "The quick brown fox jumps over the lazy dog; pack my box with five dozen "
    "liquor jugs. Sphinx of black quartz, judge my vow. 0123456789 "
)


def scene_text(scr):
    """Two wrapped labels filling the screen; the timing changes their text each refresh."""
    labels = []
    for i, size in enumerate((14, 24)):
        label = lv.label(scr)
        label.set_width(WIDTH - 16)
        label.set_style_text_font(_font(size), 0)
        label.set_long_mode(lv.label.LONG_MODE.WRAP)
        label.set_text(_TEXT * (4 - 2 * i))
        label.align(lv.ALIGN.TOP_LEFT, 8, 8 + i * (HEIGHT // 2))
        labels.append(label)
    return labels


SCENES = (("full", scene_full), ("list", scene_list), ("image", scene_image), ("text", scene_text))


def _run_scene(name, build, disp, where):
    disp.set_default()
    before_build = _free()
    scr = lv.obj(None)
    state = build(scr)
    lv.screen_load(scr)
    lv.refr_now(disp)  # the first draw lays it out and fills any cache
    if before_build is not None and where == "render":
        _report("heap_scene_%s" % name, before_build - _free(), "B")

    if name == "list":
        def step(i):
            state.scroll_by(0, -24 if (i // SCROLL_STEPS) % 2 == 0 else 24, _ANIM_OFF)

        us = _time_refresh(disp, step, SCROLL_STEPS)
    elif name == "text":
        def step(i):
            for n, label in enumerate(state):
                label.set_text(_TEXT * (4 - 2 * n) if i % 2 else _TEXT[1:] * (4 - 2 * n))

        us = _time_refresh(disp, step)
    else:
        def step(i):
            scr.invalidate()

        us = _time_refresh(disp, step)
    _report("%s_%s_us" % (where, name), us, "us")
    # Back to an empty screen before deleting this one.
    lv.screen_load(lv.obj(None))
    scr.delete()
    gc.collect()


targets = [("render", render_disp)]
if screen_disp is not None:
    targets.append(("screen", screen_disp))
for where, disp in targets:
    for name, build in SCENES:
        _run_scene(name, build, disp, where)

if screen_disp is not None:
    screen_disp.set_default()

try:
    import json

    print("BENCH_RESULT=" + json.dumps(_results))
except ImportError:
    print("BENCH_RESULT=" + repr(_results))
