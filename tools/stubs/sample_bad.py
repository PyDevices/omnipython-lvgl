# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""One deliberate type error, which mypy must report: a check that only passes proves nothing."""

import lvgl as lv

label = lv.label(lv.screen_active())
label.set_text(42)
