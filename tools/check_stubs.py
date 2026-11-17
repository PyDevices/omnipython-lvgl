#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT
"""Check that the type stub reaches a user the way the wheel delivers it.

From the repository root, with mypy installed:

    python tools/check_stubs.py

The wheel installs `generated/lvgl.pyi` as the stub-only package `lvgl-stubs`
beside the compiled `lvgl` module, which is how PEP 561 types an extension
module. This lays the stub out that way in a scratch folder and runs three
things, each in its own process with a hard timeout:

1. mypy over the stub, so a stub that doesn't parse or contradicts itself fails.
2. mypy over `tools/stubs/sample_ok.py`, which must pass.
3. mypy over `tools/stubs/sample_bad.py`, which must fail with its one planted
   error, so the stub is proved to reach a user and to catch a mistake.

It doesn't compile the extension. Whether a built wheel carries `lvgl-stubs` is
checked by `ports/cpython/tests`, which run against each wheel CI builds.
`mypy.stubtest` isn't a gate here: the stub covers three ports and the C
extension builds its structs' methods and its enum namespaces at runtime, so
stubtest reports about a thousand differences that aren't mistakes in the stub.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUB = ROOT / "generated" / "lvgl.pyi"
SAMPLES = ROOT / "tools" / "stubs"
TIMEOUT = 600  # seconds, per step


def run(command, env=None):
    try:
        return subprocess.run(command, env=env, timeout=TIMEOUT, capture_output=True, text=True, check=False)
    except subprocess.TimeoutExpired:
        print("timed out: " + " ".join(command))
        return None


def show(result):
    if result is not None:
        print((result.stdout + result.stderr).rstrip())


def main():
    status = 0
    mypy = [sys.executable, "-m", "mypy", "--no-incremental"]
    with tempfile.TemporaryDirectory() as scratch:
        site = Path(scratch) / "site"
        (site / "lvgl-stubs").mkdir(parents=True)
        (site / "lvgl-stubs" / "__init__.pyi").write_bytes(STUB.read_bytes())
        # Not MYPYPATH: a checker finds an installed stub package through site-packages.
        env = dict(os.environ, PYTHONPATH=str(site))

        print("== mypy over the stub")
        result = run(mypy + [str(STUB)])
        show(result)
        status |= result is None or result.returncode != 0

        print("== sample a user writes: must pass")
        result = run(mypy + [str(SAMPLES / "sample_ok.py")], env)
        show(result)
        status |= result is None or result.returncode != 0

        print("== sample with one planted error: must fail")
        result = run(mypy + [str(SAMPLES / "sample_bad.py")], env)
        show(result)
        if result is None or result.returncode == 0 or '"set_text" of "label"' not in result.stdout:
            print("the planted error was not reported: the stub is not being read")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
