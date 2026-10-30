# This file is used by MicroPython Make-based builds such as the Unix port.
# For CMake-based builds, see the .cmake file in the same directory.

# When building Micropython, the parent directory of this module is given as:
#     make USER_C_MODULES=<path to workspace root>

LVMP_DIR := $(USERMOD_DIR)
# The generated binding, lv_conf.h and the lvgl submodule sit at the root of
# this repository, two levels up.
BINDINGS_DIR := $(abspath $(LVMP_DIR)/../..)
LVMP_C := $(BINDINGS_DIR)/generated/lvgl_micropython.c
LVGL_DIR := $(BINDINGS_DIR)/lvgl
$(if $(wildcard $(LVGL_DIR)/lvgl.h),,$(error $(LVGL_DIR) is empty. Run: git -C $(BINDINGS_DIR) submodule update --init lvgl))
SOURCES = $(shell find $(LVGL_DIR)/src -type f -name "*.c")

# jpegio Phase 2 moved the JPEG decoder out of LVGL: LV_USE_TJPGD is 0 in the
# bindings (lvgl-bindings aa6c6bc), and the jpegio module registers its own
# TJpgDec with LVGL instead, so a firmware carries one decoder rather than two.
# Built without jpegio (micropython-pydevices' modules/jpegio since 2026-10-06;
# displayif's before), this module decodes PNG and LVGL's BIN and draws nothing
# at all for a JPEG -- silently, at run time. Say so at build time instead (#11).
ifeq ($(findstring jpegio,$(USER_C_MODULES)),)
$(info omnipython-lvgl: no jpegio in this build -- lv.image will not draw a JPEG.)
$(info   jpegio owns the TJpgDec decoder; PNG and LVGL BIN still decode.)
$(info   Name jpegio's module as well for JPEG.)
endif

# LVGL is available on every port, but its desktop/host-GUI and OS-specific
# driver backends (OpenGL/SDL/GLFW/X11/Wayland/evdev/libinput/qnx/uefi/nuttx/
# windows) plus the OpenGLES draw unit need host libraries and break cross
# builds (e.g. lv_opengles_shader.c fails -Werror). This exclusion lives in the
# module's own config: only desktop ports (unix/webassembly/windows) keep the
# full source sweep; every other (embedded) port drops these backends.
LVMP_PORT_DIR := $(abspath $(CURDIR))
LVMP_IS_DESKTOP := $(findstring /ports/unix,$(LVMP_PORT_DIR))$(findstring /ports/webassembly,$(LVMP_PORT_DIR))$(findstring /ports/windows,$(LVMP_PORT_DIR))
ifeq ($(LVMP_IS_DESKTOP),)
LVMP_EXCLUDE_DIRS := \
    $(LVGL_DIR)/src/drivers/opengles \
    $(LVGL_DIR)/src/drivers/sdl \
    $(LVGL_DIR)/src/drivers/glfw \
    $(LVGL_DIR)/src/drivers/x11 \
    $(LVGL_DIR)/src/drivers/wayland \
    $(LVGL_DIR)/src/drivers/evdev \
    $(LVGL_DIR)/src/drivers/libinput \
    $(LVGL_DIR)/src/drivers/qnx \
    $(LVGL_DIR)/src/drivers/uefi \
    $(LVGL_DIR)/src/drivers/nuttx \
    $(LVGL_DIR)/src/drivers/windows \
    $(LVGL_DIR)/src/draw/opengles \
    $(LVGL_DIR)/src/libs/gltf
SOURCES := $(foreach s,$(SOURCES),$(if $(strip $(foreach d,$(LVMP_EXCLUDE_DIRS),$(findstring $(d)/,$(s)))),,$(s)))
endif

SOURCES += $(LVMP_DIR)/src/lv_mem_core_micropython.c

$(if $(wildcard $(LVMP_C)),,$(error $(LVMP_C) not found. Run $(BINDINGS_DIR)/regenerate_all.sh --target micropython))

# -Wno-unused-function here is not enough on ports that append -Werror after py.mk
# (e.g. webassembly); those ports add -Wno-unused-function after -Werror too.
CFLAGS_USERMOD += -I$(BINDINGS_DIR) -I$(LVMP_DIR) -Wno-unused-function
SRC_USERMOD_LIB_C += $(SOURCES)
SRC_USERMOD_C += $(LVMP_C)
SRC_USERMOD_C += $(LVMP_DIR)/src/lvgl_micropython_build.c

# --- which commit this firmware was built from ---------------------
# Computed at build time from this repository's git, never stored; "unknown" when
# there is no git (a tarball). Read on a target as <module>.__revision__.
LVMP_REVISION := $(shell git -C $(LVMP_DIR) describe --always --dirty --abbrev=7 2>/dev/null || echo unknown)
CFLAGS_USERMOD += -DLVMP_REVISION='"$(LVMP_REVISION)"'

# With LV_USE_FLOAT=1, upstream LVGL trips -Werror=double-promotion / float-conversion.
# Port Makefiles (unix/webassembly) append -Wdouble-promotion after CFLAGS_USERMOD,
# so put the suppress on the LVGL object rules (same idea as circuitpython.mk).
# GCC 16 also counts a variable only ever incremented as set-but-unused
# (lv_buttonmatrix.c's txt_tot_i), which older GCC did not.
LVMP_FLOAT_CFLAGS := -Wno-double-promotion -Wno-float-conversion -Wno-unused-but-set-variable
# py.mk names a user-module object $(BUILD)/<module dir basename>/<path inside
# the module>, and how it spells a source outside every module directory
# changed in v1.29.0 (the absolute path is kept). This module is
# ports/micropython; LVGL and the generated binding sit two levels up, outside
# it, so the repository root is registered as a module directory too and its
# objects become $(BUILD)/<root dir basename>/.... Each object is named both
# ways below, since a flag rule on a target that doesn't exist never applies
# and upstream LVGL then fails the port's -Werror=double-promotion with no hint.
# The absolute spelling can't be a target on Windows: a path with a drive (C:/...)
# under $(BUILD) holds a second colon, which make reads as a static pattern rule.
USERMOD_DIRS += $(BINDINGS_DIR)
# py.mk sorts the module directories and strips the first that matches, so
# the root (a prefix of this directory) names every object here, this
# module's own src/ included. A MicroPython that strips only this directory
# names src/ by it, hence the second spelling. A spelling a pattern didn't
# match is still the absolute path, so every spelling that holds a colon is
# dropped, not only the third.
LVMP_OBJ = $(foreach o,$(BUILD)/$(patsubst $(BINDINGS_DIR)/%,$(notdir $(BINDINGS_DIR))/%,$(1)) $(BUILD)/$(patsubst $(LVMP_DIR)/%,$(notdir $(LVMP_DIR))/%,$(1)) $(BUILD)/$(1),$(if $(findstring :,$(o)),,$(o)))
$(foreach s,$(SOURCES),\
	$(eval $(call LVMP_OBJ,$(s:.c=.o)): CFLAGS += $(LVMP_FLOAT_CFLAGS)))
$(eval $(call LVMP_OBJ,$(LVMP_C:.c=.o)): CFLAGS += $(LVMP_FLOAT_CFLAGS))
$(eval $(call LVMP_OBJ,$(LVMP_DIR)/src/lv_mem_core_micropython.o): CFLAGS += $(LVMP_FLOAT_CFLAGS))
