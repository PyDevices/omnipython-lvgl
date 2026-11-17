#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Brad Barnett
#
# SPDX-License-Identifier: MIT

"""Choose or check the version a release would publish.

Usage:
    release_version.py LINE REQUESTED [TAG ...]

LINE is the LVGL line the release follows, such as ``9.6``. REQUESTED is
empty for the next final, or a version ``X.Y.Z``, ``X.Y.ZrcN`` or
``X.Y.Z.devN``. Each TAG is an existing ``vX.Y.Z[rcN|.devN]`` tag. The version
to publish is printed. A refused request prints the reason on stderr and exits
with status 1.

A request is refused unless it is on LINE, is the next final's patch number
(highest final tag plus one), and sorts above every existing tag.
"""

import re
import sys

PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:(rc|\.dev)(\d+))?$")
# .dev sorts before rc, and both before the final.
PHASE = {".dev": 0, "rc": 1, None: 2}


def parse(text):
    match = PATTERN.match(text)
    if not match:
        return None
    major, minor, patch, phase, number = match.groups()
    return (int(major), int(minor), int(patch), PHASE[phase], int(number or 0))


def check(line, requested, tags):
    """Return the version to publish, or raise ValueError saying why not."""
    major, minor = (int(part) for part in line.split("."))
    known = [parse(tag[1:]) for tag in tags if tag.startswith("v")]
    known = [key for key in known if key and key[:2] == (major, minor)]
    finals = [key for key in known if key[3] == 2]
    patch = max(key[2] for key in finals) + 1 if finals else 0
    final = "%d.%d.%d" % (major, minor, patch)
    if not requested:
        return final
    key = parse(requested)
    if key is None:
        raise ValueError(
            "%r is not a version: use X.Y.Z, X.Y.ZrcN or X.Y.Z.devN" % requested
        )
    if key[:2] != (major, minor):
        raise ValueError(
            "%s is not on the %s.x line this repository follows; the minor and "
            "major come from the lvgl submodule" % (requested, line)
        )
    if known and key <= max(known):
        raise ValueError(
            "%s is not greater than the latest version already published" % requested
        )
    if key[:3] != (major, minor, patch):
        raise ValueError(
            "%s skips ahead: the next release is %s, so ask for %s, %src1 or "
            "%s.devN" % (requested, final, final, final, final)
        )
    return requested


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        print(check(argv[1], argv[2], argv[3:]))
    except ValueError as error:
        print("Refused: %s" % error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
