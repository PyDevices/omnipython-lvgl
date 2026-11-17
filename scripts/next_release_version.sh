#!/usr/bin/env bash
# Compute the next release version.
#
# Versions mirror the LVGL major.minor of the lvgl submodule, with a patch
# counter of our own. The patch resets to 0 when the LVGL major or minor
# changes. The last release is the higher of the newest vX.Y.N tag and the
# VERSION file, which holds the version last released.
#   e.g. LVGL 9.5.x, last release 9.5.52 -> 9.5.53 ; a new LVGL 9.6.x line -> 9.6.0
#
# With --requested, check a version instead: X.Y.ZrcN or X.Y.Z.devN for the
# next release, or X.Y.Z for the next final. It prints the version when it is
# acceptable and exits 1 with the reason when it is not (scripts/release_version.py).
#
# Usage:
#   ./scripts/next_release_version.sh
#   ./scripts/next_release_version.sh --verbose
#   ./scripts/next_release_version.sh --requested 9.6.1.dev0

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
LVGL_DIR="$SOURCE_REPO/lvgl"

VERBOSE=0
REQUESTED=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose | -v)
            VERBOSE=1
            shift
            ;;
        --requested)
            REQUESTED="${2:?--requested needs a version}"
            shift 2
            ;;
        --help | -h)
            sed -n '2,18p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

read_lvgl_version() {
    local version_file
    for version_file in "$LVGL_DIR/include/lvgl/lv_version.h" "$LVGL_DIR/lv_version.h" "$LVGL_DIR/lvgl.h"; do
        [[ -f "$version_file" ]] || continue
        LVGL_MAJOR=$(grep -E '^#define LVGL_VERSION_MAJOR' "$version_file" | awk '{print $3}')
        LVGL_MINOR=$(grep -E '^#define LVGL_VERSION_MINOR' "$version_file" | awk '{print $3}')
        if [[ -n "${LVGL_MAJOR:-}" && -n "${LVGL_MINOR:-}" ]]; then
            return 0
        fi
    done
    echo "Error: could not read LVGL version from lvgl/lv_version.h or lvgl/lvgl.h" >&2
    echo "  Run: git submodule update --init lvgl" >&2
    exit 1
}

next_version() {
    local prefix="v${LVGL_MAJOR}.${LVGL_MINOR}."
    local latest remote_tag
    cd "$SOURCE_REPO"
    git fetch origin --tags 2>/dev/null || true
    remote_tag=$(
        git ls-remote --tags origin "${prefix}*" 2>/dev/null \
            | awk '{print $2}' \
            | sed 's|refs/tags/||' \
            | grep -v '\^{}$' \
            | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \
            | sort -V \
            | tail -n 1
    )
    if [[ -n "$remote_tag" ]]; then
        latest=$remote_tag
    else
        latest=$(git tag -l "${prefix}*" | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -n 1 || true)
    fi
    local committed
    committed=$(tr -d '[:space:]' < "$SOURCE_REPO/VERSION" 2>/dev/null || true)
    # Pre-releases (X.Y.Z.devN, X.Y.ZrcN) don't count as released versions.
    if [[ "$committed" =~ ^${LVGL_MAJOR}\.${LVGL_MINOR}\.[0-9]+$ ]]; then
        latest=$(printf '%s\n' "$latest" "v$committed" | grep -v '^$' | sort -V | tail -n 1)
    fi
    if [[ -z "$latest" ]]; then
        echo "${LVGL_MAJOR}.${LVGL_MINOR}.0"
    else
        echo "${LVGL_MAJOR}.${LVGL_MINOR}.$(("${latest##*.}" + 1))"
    fi
}

# Every published version tag, pre-releases included, plus VERSION when it
# names a final: the floor a requested version has to clear.
check_requested() {
    local tags committed
    cd "$SOURCE_REPO"
    git fetch origin --tags 2>/dev/null || true
    tags=$(
        {
            git ls-remote --tags origin 'v*' 2>/dev/null | awk '{print $2}' | sed 's|refs/tags/||' | grep -v '\^{}$' || true
            git tag -l 'v*'
        } | sort -u
    )
    committed=$(tr -d '[:space:]' < "$SOURCE_REPO/VERSION" 2>/dev/null || true)
    [[ "$committed" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] && tags="$tags"$'\n'"v$committed"
    # shellcheck disable=SC2086  # one tag per word is the point
    python3 "$SCRIPT_DIR/release_version.py" "${LVGL_MAJOR}.${LVGL_MINOR}" "$REQUESTED" $tags
}

read_lvgl_version
if [[ -n "$REQUESTED" ]]; then
    VERSION="$(check_requested)" || exit 1
else
    VERSION="$(next_version)"
fi

if [[ "$VERBOSE" -eq 1 ]]; then
    echo "LVGL API line: ${LVGL_MAJOR}.${LVGL_MINOR}.x"
    echo "Next version: ${VERSION}"
else
    echo "$VERSION"
fi
