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

// On by default on ESP32, off elsewhere; a build sets LVMP_POOL_TLSF to 1 or 0
// to choose. ESP32 is told apart by CONFIG_IDF_TARGET, which the port's
// mpconfigport.h brings in from sdkconfig.h, not by ESP_PLATFORM: the esp32
// port compiles every user C module a second time, for the executable, without
// ESP_PLATFORM, and that second copy is the one linked.
#ifndef LVMP_POOL_TLSF
#if defined(CONFIG_IDF_TARGET)
#define LVMP_POOL_TLSF (1)
#else
#define LVMP_POOL_TLSF (0)
#endif
#endif
#define LVMP_POOL (LVMP_POOL_TLSF)

// The first pool is small and each new one doubles, up to LVMP_POOL_BYTES:
// gc.collect() scans a pool whole, used or not, so a pool much larger than
// what LVGL keeps in it costs every collection. 32 + 64 + 128 + 7 x 256 KB,
// about 2 MB, before allocations go back to gc_alloc().
#define LVMP_POOL_MAX   (10)
#define LVMP_POOL_FIRST (32 * 1024)
#define LVMP_POOL_BYTES (256 * 1024)
#define LVMP_POOL_BIG   (32 * 1024)

#endif // LVMP_POOL_H
