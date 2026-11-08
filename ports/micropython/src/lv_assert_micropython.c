/**
 * @file lv_assert_micropython.c
 *
 * What a failed LVGL assertion does on MicroPython (lv_conf.h names this
 * function in LV_ASSERT_HANDLER for MicroPython builds). LVGL's default is
 * to spin forever, and on a board that locks the MicroPython scheduler out:
 * USB serial and WebREPL go silent and only a power cycle brings it back.
 *
 * Instead this raises RuntimeError("LVGL assert failed in <function>
 * (<file>:<line>)"). LVGL's log is off in MicroPython builds, so the
 * function and line are how to find the assertion's message in LVGL's source.
 *
 * Where the exception lands decides what LVGL state needs repair:
 *
 *  - Inside a Python callback (a flush callback, an event, a timer), the
 *    binding's callback wrapper catches it, prints it and returns to LVGL,
 *    which carries on with its pass. The call that asserted is abandoned and
 *    nothing else changes. This is the usual case: Python code changing a
 *    widget while LVGL renders.
 *  - With no Python callback in between, it unwinds out of every LVGL frame
 *    to whoever called LVGL from Python. A pass in progress is abandoned, so
 *    the flags LVGL holds for its length are cleared first: otherwise
 *    lv_timer_handler() would return at once forever after, or every later
 *    invalidation would assert again, and neither resets on a soft reset.
 *
 * With no Python frame at all to catch it, nlr_jump() ends in the port's
 * nlr_jump_fail(), the port's own fatal path.
 */
#include "py/runtime.h"

#include "lvgl/lvgl.h"
#include "lvgl/src/core/lv_global.h"
#include "lvgl/src/display/lv_display_private.h"


void lv_micropython_assert_failed(const char *file, int line, const char *func);

// From the generated binding: how many Python callbacks LVGL is inside.
int mp_lv_nesting_depth(void);

static void lv_micropython_end_pass(void) {
    if (!lv_is_initialized()) {
        return;
    }
    LV_GLOBAL_DEFAULT()->timer_state.already_running = false;
    for (lv_display_t *disp = lv_display_get_next(NULL); disp != NULL; disp = lv_display_get_next(disp)) {
        disp->rendering_in_progress = 0;
    }
}

void lv_micropython_assert_failed(const char *file, int line, const char *func) {
    // Keep only the file's own name. A loop, not strrchr: some ports'
    // C libraries (stm32's) don't provide it.
    const char *base = file;
    for (const char *p = file; *p; p++) {
        if (*p == '/' || *p == '\\') {
            base = p + 1;
        }
    }
    if (mp_lv_nesting_depth() == 0) {
        lv_micropython_end_pass();
    }
    mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("LVGL assert failed in %s (%s:%d)"), func, base, line);
}
