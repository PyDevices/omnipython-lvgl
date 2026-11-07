/**
 * @file lv_malloc_core.c
 */

/*********************
 *      INCLUDES
 *********************/
#include "lvgl/src/stdlib/lv_mem.h"
#if LV_USE_STDLIB_MALLOC == LV_STDLIB_MICROPYTHON_OVERRIDE
#include <py/mpconfig.h>
#include <py/misc.h>
#include <py/gc.h>
#include <py/mpstate.h>
#include <string.h>

// ESP32: LVGL's allocations come from TLSF pools (ESP-IDF's multi_heap) kept
// inside GC-heap blocks, not from gc_alloc() one by one.
//
// gc_alloc() finds room by walking the allocation table from the first free
// block, and LVGL's thousands of small, long-lived blocks leave the table
// full of one-block holes. On an ESP32-S3 with its heap in PSRAM a 64-byte
// allocation took ~90 us and a 2 KB one ~1.3 ms, and creating one LVGL
// widget ~1-2.5 ms: a 30-row list took 2 s to build (Waveshare LCD-7,
// 2026-09-25). multi_heap allocates in O(1).
//
// The pools are ordinary GC blocks, reachable through a root pointer, so the
// collector still scans every byte of LVGL's memory: a Python wrapper or
// callback that only lv_obj_t.user_data refers to stays alive, as with
// gc_alloc(). Allocations of LVMP_POOL_BIG bytes or more, and anything that
// does not fit, still go to gc_alloc().
//
// Other ports: the same pools on LVGL's own TLSF (lv_tlsf.c, built for this in
// lvmp_tlsf.c) when the board sets LVMP_POOL_TLSF=1. STM32H743 with a 28 MB
// GC heap in SDRAM: a full-screen refresh of 48 buttons took 54 ms with a
// fresh heap and 575 ms once 2 MB of bytearrays sat behind a free block, every
// LVGL allocation walking the table past them (mpy-lvgl-boards, 2026-11-02).
#include "lvmp_pool.h"

#if LVMP_POOL && defined(ESP_PLATFORM)
#include "multi_heap.h"
#elif LVMP_POOL
// lv_tlsf.h declares these only with LV_STDLIB_BUILTIN.
typedef void * lv_tlsf_t;
lv_tlsf_t lv_tlsf_create_with_pool(void * mem, size_t bytes);
void * lv_tlsf_malloc(lv_tlsf_t tlsf, size_t bytes);
void * lv_tlsf_realloc(lv_tlsf_t tlsf, void * ptr, size_t size);
size_t lv_tlsf_free(lv_tlsf_t tlsf, const void * ptr);
size_t lv_tlsf_block_size(void * ptr);
typedef lv_tlsf_t multi_heap_handle_t;
#define multi_heap_register(mem, bytes) lv_tlsf_create_with_pool((mem), (bytes))
#define multi_heap_malloc lv_tlsf_malloc
#define multi_heap_realloc lv_tlsf_realloc
#define multi_heap_free(h, p) ((void)lv_tlsf_free((h), (p)))
#define multi_heap_get_allocated_size(h, p) lv_tlsf_block_size(p)
#endif

#if LVMP_POOL

// The pools' GC blocks are kept reachable (and so everything LVGL stores in
// them) by the root pointer lvmp_pool_mem, registered in lvgl_micropython_build.c:
// make builds do not scan this file (SRC_USERMOD_LIB_C) for root pointers.

static multi_heap_handle_t lvmp_heaps[LVMP_POOL_MAX];
static uint8_t *lvmp_start[LVMP_POOL_MAX];
static uint8_t *lvmp_end[LVMP_POOL_MAX];
static int lvmp_n;

static void lvmp_pools_reset(void)
{
    for (int i = 0; i < LVMP_POOL_MAX; i++) {
        MP_STATE_VM(lvmp_pool_mem)[i] = NULL;
        lvmp_heaps[i] = NULL;
        lvmp_start[i] = lvmp_end[i] = NULL;
    }
    lvmp_n = 0;
}

static int lvmp_pool_of(const void * p)
{
    const uint8_t *b = p;
    for (int i = 0; i < lvmp_n; i++) {
        if (b >= lvmp_start[i] && b < lvmp_end[i]) {
            return i;
        }
    }
    return -1;
}

static bool lvmp_pool_add(void)
{
    if (lvmp_n >= LVMP_POOL_MAX) {
        return false;
    }
    void *mem = gc_alloc(LVMP_POOL_BYTES, 0);
    if (mem == NULL) {
        return false;
    }
    multi_heap_handle_t h = multi_heap_register(mem, LVMP_POOL_BYTES);
    if (h == NULL) {
        gc_free(mem);
        return false;
    }
    MP_STATE_VM(lvmp_pool_mem)[lvmp_n] = mem;
    lvmp_heaps[lvmp_n] = h;
    lvmp_start[lvmp_n] = mem;
    lvmp_end[lvmp_n] = (uint8_t *)mem + LVMP_POOL_BYTES;
    lvmp_n++;
    return true;
}

static void *lvmp_pool_malloc(size_t size)
{
    if (size >= LVMP_POOL_BIG) {
        return NULL;
    }
    for (int i = 0; i < lvmp_n; i++) {
        void *p = multi_heap_malloc(lvmp_heaps[i], size);
        if (p != NULL) {
            return p;
        }
    }
    if (lvmp_pool_add()) {
        return multi_heap_malloc(lvmp_heaps[lvmp_n - 1], size);
    }
    return NULL;
}
#endif /* LVMP_POOL */
/*********************
 *      DEFINES
 *********************/

/**********************
 *      TYPEDEFS
 **********************/

/**********************
 *  STATIC PROTOTYPES
 **********************/

/**********************
 *  STATIC VARIABLES
 **********************/

/**********************
 *      MACROS
 **********************/

/**********************
 *   GLOBAL FUNCTIONS
 **********************/

void lv_mem_init(void)
{
#if LVMP_POOL
    // A fresh LVGL lifetime (first import, or lv.init() after lv.deinit() or
    // a soft reset): the previous pools, if any, were GC memory that is gone
    // or about to be.
    lvmp_pools_reset();
#endif
}

void lv_mem_deinit(void)
{
#if LVMP_POOL
    lvmp_pools_reset();
#endif
}

lv_mem_pool_t lv_mem_add_pool(void * mem, size_t bytes)
{
    /*Not supported*/
    LV_UNUSED(mem);
    LV_UNUSED(bytes);
    return NULL;
}

void lv_mem_remove_pool(lv_mem_pool_t pool)
{
    /*Not supported*/
    LV_UNUSED(pool);
    return;
}

void * lv_malloc_core(size_t size)
{
#if LVMP_POOL
    void *pooled = lvmp_pool_malloc(size);
    if (pooled != NULL) {
        return pooled;
    }
#endif
#if MICROPY_MALLOC_USES_ALLOCATED_SIZE
    // 0, not true: gc_alloc()'s second argument is alloc_flags, and 1 is
    // GC_ALLOC_FLAG_HAS_FINALISER. An LVGL struct is not an mp_obj_base_t, so
    // flagging it made gc_sweep_run_finalisers read its first word as a type
    // pointer and call mp_load_method_maybe() on whatever that happened to be
    // -- SIGBUS in gc.collect() after an lv.deinit()/lv.init() cycle, once a
    // block freed in the first lifetime came back with a different first word
    // (PyDevices/lvgl-micropython#10).
    return gc_alloc(size, 0);
#else
    return m_malloc(size);
#endif
}

void * lv_realloc_core(void * p, size_t new_size)
{
#if LVMP_POOL
    int pool = p != NULL ? lvmp_pool_of(p) : -1;
    if (pool >= 0) {
        void *q = multi_heap_realloc(lvmp_heaps[pool], p, new_size);
        if (q != NULL || new_size == 0) {
            return q;
        }
        // Did not fit in its pool: move it (another pool, or the GC heap).
        size_t old_size = multi_heap_get_allocated_size(lvmp_heaps[pool], p);
        q = lv_malloc_core(new_size);
        if (q != NULL) {
            memcpy(q, p, old_size < new_size ? old_size : new_size);
            multi_heap_free(lvmp_heaps[pool], p);
        }
        return q;
    }
    if (p == NULL) {
        return lv_malloc_core(new_size);
    }
#endif

#if MICROPY_MALLOC_USES_ALLOCATED_SIZE
    // true here is gc_realloc()'s allow_move, which is what we want -- unlike
    // the flags argument to gc_alloc() above, it is not a finaliser bit.
    return gc_realloc(p, new_size, true);
#else
    return m_realloc(p, new_size);
#endif
}

void lv_free_core(void * p)
{
#if LVMP_POOL
    int pool = p != NULL ? lvmp_pool_of(p) : -1;
    if (pool >= 0) {
        multi_heap_free(lvmp_heaps[pool], p);
        return;
    }
#endif

#if MICROPY_MALLOC_USES_ALLOCATED_SIZE
    gc_free(p);

#else
    m_free(p);
#endif
}

void lv_mem_monitor_core(lv_mem_monitor_t * mon_p)
{
    /*Not supported*/
    LV_UNUSED(mon_p);
    return;
}

lv_result_t lv_mem_test_core(void)
{
    /*Not supported*/
    return LV_RESULT_OK;
}

/**********************
 *   STATIC FUNCTIONS
 **********************/

#endif /*LV_STDLIB_MICROPYTHON*/