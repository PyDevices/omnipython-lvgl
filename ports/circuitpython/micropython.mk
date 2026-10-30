# CircuitPython user C module glue for LVGL and its generated bindings.
#
# CircuitPython builds user C modules the way MicroPython does, so this
# directory can be handed to any CircuitPython port's make as is, with no
# patches to CircuitPython's own tree:
#
#   make -C ports/unix USER_C_MODULES=<repo>/ports/circuitpython
#   make -C ports/raspberrypi BOARD=adafruit_feather_rp2040 CIRCUITPY_GIFIO=0 \
#       USER_C_MODULES=<repo>/ports/circuitpython
#
# On a board, CIRCUITPY_GIFIO=0 goes on the make line: LVGL links its own
# copy of the AnimatedGIF decoder (LV_USE_GIF in this repository's lv_conf.h),
# and CircuitPython's gifio links another, so the two collide at link time.
# The unix port compiles no gifio and needs nothing.

LVCP_DIR := $(USERMOD_DIR)
# $(abspath) tidies ".." in the text without following symlinks, so look beside
# the real directory.
LVCP_REAL := $(realpath $(LVCP_DIR))

ifeq ($(wildcard $(TOP)/py/circuitpy_mpconfig.h),)
$(error ports/circuitpython is for CircuitPython builds; MicroPython builds use ports/micropython)
endif

ifeq ($(CIRCUITPY_GIFIO),1)
$(error lvgl: add CIRCUITPY_GIFIO=0 to the make line. LVGL links its own AnimatedGIF decoder, which collides with gifio's)
endif

# The generated binding, lv_conf.h and the lvgl submodule sit at the root of
# this repository, two levels up from the directory this one really is (a
# build that hands the module over through a symlink still finds them).
LV_BINDINGS_DIR := $(abspath $(LVCP_REAL)/../..)
LVGL_DIR := $(LV_BINDINGS_DIR)/lvgl
LVCP_C := $(LV_BINDINGS_DIR)/generated/lvgl_circuitpython.c
LVCP_H := $(LV_BINDINGS_DIR)/generated/lvgl_circuitpython.h
$(if $(wildcard $(LVGL_DIR)/lvgl.h),,$(error $(LVGL_DIR) is empty. Run: git -C $(LV_BINDINGS_DIR) submodule update --init lvgl))
$(if $(wildcard $(LVCP_C)),,$(error $(LVCP_C) not found. Run $(LV_BINDINGS_DIR)/regenerate_all.sh --target circuitpython))
$(if $(wildcard $(LVCP_H)),,$(error $(LVCP_H) not found. Run $(LV_BINDINGS_DIR)/regenerate_all.sh --target circuitpython))

# LVGL itself. Its host backends (SDL, X11, Wayland, OpenGL ES, ...) need host
# libraries and are left out of board builds; on unix each compiles to nothing
# unless lv_conf.h turns it on.
LVCP_LVGL_SOURCES := $(shell find $(LVGL_DIR)/src -type f -name '*.c')
ifeq ($(findstring /ports/unix,$(abspath $(CURDIR))),)
LVCP_EXCLUDE_DIRS := \
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
LVCP_LVGL_SOURCES := $(foreach s,$(LVCP_LVGL_SOURCES),$(if $(strip $(foreach d,$(LVCP_EXCLUDE_DIRS),$(findstring $(d)/,$(s)))),,$(s)))
endif

# LVGL has no MP_QSTR_* in it, so it goes in SRC_USERMOD_LIB_C, which py.mk
# compiles and links but never scans for qstrs. Scanning it would only cost
# time, and on espressif the scan's command line passes the kernel's limit.
SRC_USERMOD_LIB_C += $(LVCP_LVGL_SOURCES)

# The CircuitPython side: the module (registered with MP_REGISTER_MODULE in
# shared-bindings/lvgl/__init__.c), the generated bindings, LVGL's allocator on
# CircuitPython's heap, LVGL's JPEG decoder on CircuitPython's TJpgDec (a no-op
# without jpegio), and what an LVGL assertion does (safe mode, not a hang).
# These are scanned for qstrs.
LVCP_SPIKE := $(LVCP_DIR)/src/circuitpython_spike
LVCP_SOURCES := \
	$(LVCP_SPIKE)/shared-bindings/lvgl/__init__.c \
	$(LVCP_SPIKE)/shared-module/lvgl/__init__.c \
	$(LVCP_DIR)/src/lv_mem_core_circuitpython.c \
	$(LVCP_DIR)/src/lv_jpegio_decoder_circuitpython.c \
	$(LVCP_DIR)/src/lv_assert_circuitpython.c \
	$(LVCP_C)
SRC_USERMOD_C += $(LVCP_SOURCES)

# The spike includes "shared-bindings/lvgl/__init__.h"; CircuitPython's own
# -I$(TOP) comes first and has no lvgl/, so these resolve to the spike's.
# LV_CIRCUITPYTHON_BUILD picks the allocator above in lv_conf.h and leaves
# lvgl.init()/deinit() to the spike.
CFLAGS_USERMOD += -DLV_CIRCUITPYTHON_BUILD=1 -I$(LVCP_SPIKE) -I$(LV_BINDINGS_DIR) -I$(LVGL_DIR) -Wno-unused-function

# LVGL's bindings bring about 53 KB of qstrs. CircuitPython 11 keeps a ROM qstr
# pool's strings in one blob addressed by 16-bit offsets, 64 KB at most, which
# a board's own modules and LVGL together pass. Where CircuitPython has the
# MICROPY_QSTR_OFFSET_BYTES setting, four-byte offsets lift that limit for
# about two bytes of flash per qstr.
CFLAGS_USERMOD += -DMICROPY_QSTR_OFFSET_BYTES=4

# Upstream LVGL and the generated bindings trip warnings CircuitPython's ports
# make errors of, and the board ports append those -Werror flags after
# CFLAGS_USERMOD, so a module-wide -Wno-* would lose. A target-specific flag
# lands last, so they are turned off per object, for this module's objects
# only. -Wfloat-equal, -Wdouble-promotion and -Wcast-align are the board
# ports' (arc and chart compare floats directly); the rest are LVGL's style.
LVCP_OBJ_CFLAGS := -Wno-cast-align -Wno-nested-externs -Wno-unused-parameter \
	-Wno-sign-compare -Wno-missing-prototypes -Wno-old-style-definition \
	-Wno-float-conversion -Wno-double-promotion -Wno-shadow -Wno-type-limits \
	-Wno-suggest-attribute=format -Wno-float-equal -Wno-unused-const-variable \
	-Wno-unused-but-set-variable -Wno-unused-function -Wno-undef

# py.mk names a user module's object $(BUILD)/<module dir name>/<path inside
# it>.o, and a source outside the module (LVGL and the generated binding, two
# levels up) $(BUILD)/<absolute path>.o. Both spellings are declared.
LVCP_OBJ = $(BUILD)/$(patsubst $(LVCP_DIR)/%,$(notdir $(LVCP_DIR))/%,$(1)) $(BUILD)/$(1)
$(foreach _s,$(LVCP_LVGL_SOURCES) $(LVCP_SOURCES),\
	$(eval $(call LVCP_OBJ,$(_s:.c=.o)): CFLAGS += $(LVCP_OBJ_CFLAGS)))
