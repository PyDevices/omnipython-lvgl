# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""A build can turn a Montserrat size off without regenerating the binding."""

import re
from pathlib import Path

from binding.util import config_guard, guarded

REPO = Path(__file__).resolve().parents[1]


def test_only_montserrat_fonts_are_guarded():
    assert config_guard("lv_font_montserrat_40") == "LV_FONT_MONTSERRAT_40"
    assert config_guard("lv_font_montserrat_28_compressed") is None
    assert config_guard("lv_tree_node_class") is None
    assert guarded("x", "lv_tree_node_class") == "x"
    assert guarded("x", "lv_font_montserrat_14") == "#if LV_FONT_MONTSERRAT_14\nx\n#endif"
    assert guarded("x", "lv_font_montserrat_14", "  ") == "#if LV_FONT_MONTSERRAT_14\n  x\n  #endif"


def test_lv_conf_lets_a_build_override_every_montserrat_size():
    conf = (REPO / "lv_conf.h").read_text()
    for size in re.findall(r"#define LV_FONT_MONTSERRAT_(\d+) ", conf):
        assert "#ifndef LV_FONT_MONTSERRAT_%s\n#define LV_FONT_MONTSERRAT_%s " % (size, size) in conf


def test_every_generated_font_is_guarded():
    for name in ("lvgl_micropython.c", "lvgl_circuitpython.c", "lvgl_python.c"):
        text = (REPO / "generated" / name).read_text()
        for line_no, line in enumerate(text.splitlines()):
            if re.search(r"[&(]\s*\(?(lv_font_t\*\)\s*)?&?lv_font_montserrat_\d+\b", line) or "mp_lv_font_montserrat_" in line:
                size = re.search(r"montserrat_(\d+)", line).group(1)
                before = text.splitlines()[max(0, line_no - 3):line_no]
                assert any(l.strip() == "#if LV_FONT_MONTSERRAT_%s" % size for l in before), (name, line)
