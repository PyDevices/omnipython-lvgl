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

// Off unless a build sets LVMP_POOL_TLSF to 1, on every port. Set it where the
// root-pointer scan sees it too: in the board's mpconfigboard.h, or in
// CFLAGS_EXTRA on a make port. A definition that reaches only the compiler
// (on the esp32 port, a CMake target_compile_definitions) leaves the pools'
// root pointer unregistered and the build fails.
//
// The pools trade collection time for allocation time: gc.collect() scans
// them whole, used or not. On an ESP32-P4 with 31 MB of GC heap in PSRAM, a
// collection on a fresh heap took 6.1 ms with them against 2.9 ms without,
// while creating and deleting 50 labels on a fragmented heap took 14 ms with
// them against 43-49 ms without.
#ifndef LVMP_POOL_TLSF
#define LVMP_POOL_TLSF (0)
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
