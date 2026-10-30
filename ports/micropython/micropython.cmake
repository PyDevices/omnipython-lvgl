# This file is used by MicroPython CMake-based builds such as the ESP32 and RP2 ports.
# For Make-based builds, see the .mk file in the same directory.

# Point USER_C_MODULES at this directory (or this file) directly, e.g.:
#     idf.py build -DUSER_C_MODULES=<repo>/ports/micropython
# usermod.cmake also accepts a semicolon-separated list of module paths if you
# want this module plus others, e.g.:
#     -DUSER_C_MODULES="<repo>/ports/micropython;<path to other_mod>"

set(LVMP_DIR ${CMAKE_CURRENT_LIST_DIR})
# The generated binding, lv_conf.h and the lvgl submodule sit at the root of
# this repository, two levels up.
get_filename_component(BINDINGS_DIR ${LVMP_DIR}/../.. ABSOLUTE)
set(LVMP_C ${BINDINGS_DIR}/generated/lvgl_micropython.c)
set(LVGL_DIR ${BINDINGS_DIR}/lvgl)
if(NOT EXISTS ${LVGL_DIR}/lvgl.h)
    message(FATAL_ERROR "${LVGL_DIR} is empty. Run: git -C ${BINDINGS_DIR} submodule update --init lvgl")
endif()
file(GLOB_RECURSE SOURCES ${LVGL_DIR}/src/*.c)

# LVGL is available on every port, but its desktop/host-GUI and OS-specific
# driver backends plus the OpenGLES draw unit need host libraries and break the
# build. CMake ports here (esp32/rp2) are embedded, so drop those backends. This
# exclusion lives in the module's own config, not in the build tool.
list(FILTER SOURCES EXCLUDE REGEX "/src/drivers/(opengles|sdl|glfw|x11|wayland|evdev|libinput|qnx|uefi|nuttx|windows)/")
list(FILTER SOURCES EXCLUDE REGEX "/src/draw/opengles/")
list(APPEND SOURCES ${LVMP_DIR}/src/lv_mem_core_micropython.c)

if(NOT EXISTS ${LVMP_C})
    message(FATAL_ERROR "${LVMP_C} not found. Run ${BINDINGS_DIR}/regenerate_all.sh --target micropython")
endif()

# jpegio Phase 2 moved the JPEG decoder out of LVGL: LV_USE_TJPGD is 0 in the
# bindings (lvgl-bindings aa6c6bc), and the jpegio module registers its own
# TJpgDec with LVGL instead, so a firmware carries one decoder rather than two.
# Built without jpegio (micropython-pydevices' modules/jpegio since 2026-10-06;
# displayif's before), this module decodes PNG and LVGL's BIN and draws nothing
# at all for a JPEG -- silently, at run time. Say so at build time instead (#11).
if(NOT "${USER_C_MODULES}" MATCHES "jpegio")
    message(NOTICE
        "omnipython-lvgl: no jpegio in this build -- lv.image will not draw "
        "a JPEG. jpegio owns the TJpgDec decoder; PNG and LVGL BIN still "
        "decode. Name jpegio's module as well for JPEG.")
endif()

add_library(lv_micropython INTERFACE)
target_sources(lv_micropython INTERFACE ${LVMP_C} ${LVMP_DIR}/src/lvgl_micropython_build.c)

# --- which commit this firmware was built from ---------------------
# Computed at build time from this repository's git, never stored; "unknown" when
# there is no git (a tarball). Read on a target as <module>.__revision__.
execute_process(
    COMMAND git -C ${LVMP_DIR} describe --always --dirty --abbrev=7
    OUTPUT_VARIABLE LVMP_REVISION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
if(NOT LVMP_REVISION)
    set(LVMP_REVISION "unknown")
endif()
target_compile_definitions(lv_micropython INTERFACE LVMP_REVISION=\"${LVMP_REVISION}\")
target_include_directories(lv_micropython INTERFACE ${BINDINGS_DIR} ${LVMP_DIR})
target_link_libraries(usermod INTERFACE lv_micropython)

add_library(lvgl INTERFACE)
target_sources(lvgl INTERFACE ${SOURCES})
# Match micropython.mk / CircuitPython: LV_USE_FLOAT upstream trips -Werror=float.
target_compile_options(lvgl INTERFACE
    -Wno-unused-function
    -Wno-double-promotion
    -Wno-float-conversion
)
target_link_libraries(lv_micropython INTERFACE lvgl)
