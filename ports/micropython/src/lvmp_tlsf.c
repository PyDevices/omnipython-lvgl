// SPDX-FileCopyrightText: 2026 Nunzio Raciti
//
// SPDX-License-Identifier: MIT

/**
 * @file lvmp_tlsf.c
 *
 * LVGL's TLSF allocator for the LVMP pools of lv_mem_core_micropython.c
 * (LVMP_POOL_TLSF, see lvmp_pool.h). LVGL compiles
 * lv_tlsf.c only with LV_STDLIB_BUILTIN, so it is built here, in a translation
 * unit of its own, with that setting: nothing else in LVGL changes.
 */
#if __has_include("lvgl/include/lvgl/config/lv_conf_internal.h")
// LVGL 9.6 moved its public headers to include/lvgl/.
#include "lvgl/include/lvgl/config/lv_conf_internal.h"
#define LVMP_TLSF_HAS_POOL_EXPAND 0
#else
#include "lvgl/src/lv_conf_internal.h"
#define LVMP_TLSF_HAS_POOL_EXPAND 1
#endif
#include "lvmp_pool.h"
#if LV_USE_STDLIB_MALLOC == LV_STDLIB_MICROPYTHON_OVERRIDE && LVMP_POOL
#undef LV_USE_STDLIB_MALLOC
#define LV_USE_STDLIB_MALLOC LV_STDLIB_BUILTIN
// LVGL 9.6 compiles lv_tlsf.c under LV_USE_TLSF, which lv_conf_internal.h
// has already derived from the real LV_USE_STDLIB_MALLOC: turn it on here.
#undef LV_USE_TLSF
#define LV_USE_TLSF 1
// lv_tlsf.c sizes its tables for LV_MEM_SIZE (and, before LVGL 9.6,
// LV_MEM_POOL_EXPAND_SIZE), which lv_conf_internal.h defines only with
// LV_STDLIB_BUILTIN: one TLSF per pool.
#define LV_MEM_SIZE LVMP_POOL_BYTES
#if LVMP_TLSF_HAS_POOL_EXPAND
#define LV_MEM_POOL_EXPAND_SIZE 0
#endif
#include "lvgl/src/stdlib/builtin/lv_tlsf.c"
#endif
