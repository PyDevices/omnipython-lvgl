from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def test_make_and_cmake_build_the_binding_in_this_tree():
    make = (ROOT / "micropython.mk").read_text()
    cmake = (ROOT / "micropython.cmake").read_text()
    for text in (make, cmake):
        assert "generated/lvgl_micropython.c" in text
        assert "LVGL_BINDINGS_COMMIT" not in text
        assert "fetch_bindings.sh" not in text
        assert "regenerate_lvmp.sh" not in text
    assert "$(abspath $(LVMP_DIR)/../..)" in make
    assert "${LVMP_DIR}/../.. ABSOLUTE" in cmake
    assert (REPO / "generated" / "lvgl_micropython.c").is_file()
    assert (REPO / "lv_conf.h").is_file()


def test_fs_driver_is_frozen_from_the_one_copy():
    manifest = (ROOT / "manifest.py").read_text()
    assert 'module("fs_driver.py", base_path="../../python"' in manifest
    assert (REPO / "python" / "fs_driver.py").is_file()
    assert not (ROOT / "lib" / "fs_driver.py").exists()


def test_no_consumer_smoke_wrapper_remains():
    assert not (ROOT / "tools" / "test_lvgl_unix.py").exists()
