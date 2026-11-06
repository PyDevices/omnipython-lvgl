// SPDX-FileCopyrightText: 2026 Brad Barnett
//
// SPDX-License-Identifier: MIT

// LVGL's gesture recogniser (src/indev/lv_indev_gesture.c) calls the double
// sqrt(). An stm32 firmware built with single-precision floats links only
// MicroPython's single-precision libm, which has sqrtf() and no sqrt(), so the
// link fails. Gesture distances are pixels: single precision is plenty.

#include "py/mpconfig.h"

#if MICROPY_FLOAT_IMPL == MICROPY_FLOAT_IMPL_FLOAT

float sqrtf(float x);

double sqrt(double x) {
    return sqrtf((float)x);
}

#endif
