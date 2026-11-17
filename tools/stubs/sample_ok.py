# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""What a user writes against the stub: mypy must accept it."""

import lvgl as lv

lv.init()
screen = lv.screen_active()
label = lv.label(screen)
label.set_text("Hello")
label.set_width(120)
