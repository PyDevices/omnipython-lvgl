// SPDX-FileCopyrightText: 2026 Nunzio Raciti
//
// SPDX-License-Identifier: MIT

// LVGL allocations from TLSF pools kept in GC blocks (lv_mem_core_micropython.c).
// Shared with lvgl_micropython_build.c, which registers the pools' root pointer
// (make builds scan only SRC_USERMOD_C for root pointers, not the LVGL sources),
// and lvmp_tlsf.c, which sizes LVGL's TLSF for one pool.
#ifndef LVMP_POOL_H
#define LVMP_POOL_H

#include "py/mpconfig.h"

// ESP32: ESP-IDF's multi_heap. Other ports: LVGL's TLSF, when the board sets
// LVMP_POOL_TLSF=1.
#if defined(ESP_PLATFORM) && MICROPY_MALLOC_USES_ALLOCATED_SIZE
#define LVMP_POOL (1)
#elif defined(LVMP_POOL_TLSF) && LVMP_POOL_TLSF
#define LVMP_POOL (1)
#else
#define LVMP_POOL (0)
#endif

#define LVMP_POOL_MAX   (8)
#define LVMP_POOL_BYTES (256 * 1024)
#define LVMP_POOL_BIG   (32 * 1024)

#endif // LVMP_POOL_H
