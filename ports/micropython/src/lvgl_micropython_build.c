// lvgl_micropython.__revision__: which omnipython-lvgl commit this firmware
// was built from. The `lvgl` module itself is generated, so the stamp lives in
// this small module, the way pygraphics and audiodsp carry theirs. The build
// passes LVMP_REVISION (git describe) as a compile definition; a build with no
// git says "unknown".
#include "py/obj.h"
#include "py/objstr.h"
#include "py/runtime.h"
#include "lvmp_pool.h"

#if LVMP_POOL
// The GC blocks of lv_mem_core_micropython.c's pools: this root pointer keeps
// them, and so everything LVGL stores in them, reachable.
MP_REGISTER_ROOT_POINTER(void *lvmp_pool_mem[LVMP_POOL_MAX]);
#endif

#ifndef LVMP_REVISION
#define LVMP_REVISION "unknown"
#endif
static const MP_DEFINE_STR_OBJ(lvmp_revision_obj, LVMP_REVISION);

static const mp_rom_map_elem_t lvmp_build_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_lvgl_micropython) },
    { MP_ROM_QSTR(MP_QSTR___revision__), MP_ROM_PTR(&lvmp_revision_obj) },
};
static MP_DEFINE_CONST_DICT(lvmp_build_globals, lvmp_build_globals_table);

const mp_obj_module_t lvgl_micropython_build_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&lvmp_build_globals,
};
MP_REGISTER_MODULE(MP_QSTR_lvgl_micropython, lvgl_micropython_build_module);
