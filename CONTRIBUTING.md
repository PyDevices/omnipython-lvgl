# Contributing to omnipython-lvgl

This repository holds the whole LVGL family: the generator that writes the
bindings from LVGL's headers, the shared `lv_conf.h`, and the three ports that
build those bindings into MicroPython, CircuitPython and CPython. A change to
the generator and the ports that use it lands in one pull request, and every
build reads the same generated source. How the pieces fit together is in
[How it works](docs/how-it-works/index.md); this page is for changing them.

## Where things are

```text
omnipython-lvgl/
  binding/              The generator (binding.generate is the entry point)
  lvgl/                 LVGL submodule
  lv_conf.h             The one LVGL config, for every target
  generated/            Generated bindings, API model and shared stub (committed)
  python/               Hand-written helpers (fs_driver.py)
  packages/             mip manifests
  fonts/                Font files fs_driver.py loads at runtime
  regenerate_all.sh     Regenerates every binding artifact
  setup.py, pyproject.toml, VERSION
                        The CPython wheel (built from the root; see below)
  ports/micropython/    MicroPython user C module: build files, allocator, build stamp
  ports/circuitpython/  CircuitPython user C module: module sources, allocator, JPEG decoder
  ports/cpython/        CPython runtime (src/), jpegio's decoder (src/jpegio/), tests
  docs/                 The docs site's source
  tests/                Generator tests
  tools/                The smoke suite every interpreter runs, artifact hashing
  scripts/              Verification and release utilities
  scratch/              Upstream-baseline oracle, to diff against LVGL's upstream binding
```

The wheel's `setup.py` and `pyproject.toml` sit at the root, not in
`ports/cpython/`, because the shared wheel builder runs cibuildwheel at the
repository root. They compile `ports/cpython/src/`, `generated/lvgl_python.c`
and LVGL, and install `python/fs_driver.py` beside the extension.

`docs/` also holds `baseline/`, the compact historical API record that
`binding.api_report` and the tests read. It stays off the site.

## Set up

```bash
git clone --recurse-submodules --shallow-submodules https://github.com/PyDevices/omnipython-lvgl.git
cd omnipython-lvgl
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

`requirements.txt` holds the generator's runtime dependencies alone;
`requirements-dev.txt` adds the pinned test and static-checking tools.

## The usual loop

Change something in `binding/`, the LVGL submodule or `lv_conf.h`, regenerate
the target you need, then rebuild that target's firmware or extension and run
the smoke suite on it. A change to a port's own sources (an allocator, the
CPython runtime, a build file) needs only the rebuild. If you changed the C API
surface or the LVGL headers, rebuild at least one port before trusting the
result.

## Generate the bindings

Regenerate after changing `lvgl/`, `lv_conf.h` or `binding/`, then commit the
updated files under `generated/`:

```bash
./regenerate_all.sh                    # all targets
./regenerate_all.sh --target micropython
./regenerate_all.sh --target circuitpython
./regenerate_all.sh --target cpython
./regenerate_all.sh --pyi-only         # shared stub only
./regenerate_all.sh --check --hash     # read-only reproducibility check, the gate a release uses
```

`regenerate_all.sh` never commits, tags, pushes or publishes. It calls the
generator directly:

```bash
PYTHONPATH=. .venv/bin/python -m binding.generate
```

Call `-m binding.generate` yourself only for flags the wrapper doesn't expose,
such as `binding.api_report`:

```bash
PYTHONPATH=. .venv/bin/python -m binding.api_report generated/api.json \
    --baseline docs/baseline/lvgl-bindings-api-baseline.json.gz \
    --classification docs/baseline/lvgl-bindings-api-baseline-classification.json \
    --format markdown
```

The unified command preprocesses LVGL once and writes the selected target's C
source, the target-neutral `api.json`, the shared `lvgl.pp`, the CircuitPython
generated header and the shared `lvgl.pyi`. The API model is hashed and
includes visibility and target availability; deliberate exceptions live in
[`binding/api_policy.json`](binding/api_policy.json). Preprocessing removes compiler line markers, so the
inputs are reproducible across checkout paths. `--check` generates into a
temporary directory and never changes the working tree.

The stub comes only from the canonical [`generated/api.json`](generated/api.json). Use `--pyi-only`
when you change typing emission, so the C bindings, the model and the
preprocessed input aren't regenerated.

## Build a port

The firmware builds take a port directory from this checkout; the guides have
the full steps:

- [Build MicroPython firmware with LVGL](docs/guides/build-micropython-firmware-with-lvgl.md)
- [Build CircuitPython firmware with LVGL](docs/guides/build-circuitpython-firmware-with-lvgl.md)
- [Build the CPython extension from source](docs/guides/build-the-cpython-extension-from-source.md)

Each port finds the generated binding, `lv_conf.h` and `lvgl/` two directories
up from itself, so a build fails at once, with the command to run, if the
submodule or a generated file is missing.

After changing CPython native code (`ports/cpython/src/` or
`generated/lvgl_python.c`), reinstall the editable build before you test: an
editable install doesn't recompile on import.

## Check your work

```bash
.venv/bin/python -m pytest -q tests ports/micropython/tests ports/circuitpython/tests
./scripts/verify_bindings.sh           # read-only checks
./scripts/release_dry_run.sh           # the complete non-mutating release gate
```

The tests under `ports/micropython/tests` and `ports/circuitpython/tests` read
the build files and sources and check they are wired together; they run under
CPython. The CPython extension has its own tests, run against the built
extension:

```bash
python -m pip install -e .
python -m unittest discover -s ports/cpython/tests -v
```

Every interpreter runs the same smoke suite, with the interpreter you built:

```bash
python tools/test_lvgl_smoke.py
../micropython/ports/unix/build-standard/micropython tools/test_lvgl_smoke.py
../circuitpython/ports/unix/build-coverage/micropython tools/test_lvgl_smoke.py
```

`linux-integration.yml` does the same in CI: it builds the MicroPython v1.29.0
and CircuitPython 11.0.0-alpha.1 unix ports with `ports/micropython` and
`ports/circuitpython`, builds the CPython extension, and runs the smoke suite
on all three.

[`scratch/upstream_baseline/run.sh`](scratch/upstream_baseline/run.sh) verifies that the pinned upstream generator
still reproduces the baseline, without keeping its source or full outputs in
this repository. All of its output goes to a temporary directory that is
removed on exit. Set `LVGL_BINDINGS_UPSTREAM_REPO` to reuse a checkout at the
pinned commit instead of cloning one.

### The CircuitPython JPEG decoder

[`ports/circuitpython/tests/test_lvgl_jpeg_decode.py`](ports/circuitpython/tests/test_lvgl_jpeg_decode.py) renders `lv.image` on the
jpegio corpus and compares the result to jpegio's golden digests, with
CircuitPython's own `jpegio` to `displayio.Bitmap` as a second witness. The
witness skips the right-edge MCU block of odd widths, where CircuitPython's
`bitmap_output()` mis-strides; that is a CircuitPython bug, not the decoder's.
It needs a [micropython-pydevices](https://github.com/PyDevices/micropython-pydevices)
checkout beside this one for the frames, or `JPEGIO_FRAMES=` pointing at them.
Without a CircuitPython build,
[`ports/circuitpython/tools/host_jpegio_decoder_check.sh`](ports/circuitpython/tools/host_jpegio_decoder_check.sh) links LVGL,
CircuitPython's `lib/tjpgd` and the decoder, renders the corpus and compares
the digests.

## Sync the CPython JPEG decoder

The CPython extension draws JPEGs with jpegio's LVGL decoder, the one
MicroPython builds use, so a JPEG draws the same on every interpreter. It is
copied into `ports/cpython/src/jpegio/` from
[micropython-pydevices](https://github.com/PyDevices/micropython-pydevices)'s
`modules/jpegio`, at the commit recorded in `ports/cpython/JPEGIO_COMMIT`. To
move it, from an exact commit:

```bash
ports/cpython/scripts/sync_from_jpegio.sh --ref <40-character-commit-sha>
```

Commit `ports/cpython/JPEGIO_COMMIT` and `ports/cpython/src/jpegio/` together.

## Releasing

Versions mirror LVGL's major and minor API line and use their own patch
counter: the line is `9.5.N`, and `N` advances with each release regardless of
LVGL's own patch number. One release covers the generator, the three ports and
the wheel. The firmware ports publish nothing of their own: a firmware build
takes this repository at a commit.

Generation, validation and release are separate actions. Preview the gate and
the next version without changing anything:

```bash
./scripts/release_dry_run.sh
./scripts/next_release_version.sh --verbose
```

The next version is one past the newer of the highest `v9.5.*` tag and the
`VERSION` file.

The **Release** workflow (`release.yml`) is run by hand with two inputs: `ref`
(an exact 40-character commit SHA or a `vX.Y.Z` tag) and `mode`. In the default
`dry-run` mode it builds and smoke-tests every port, runs the release gate and
reports the version, and changes nothing. In `release` mode, and only when
`main` is at the validated commit, it also writes the version to `VERSION` on
`main` and publishes a GitHub Release, which starts
`publish-release-packages.yml` to build and upload the wheels. A push to `main`
never starts a release.

### Package matrix

`pyproject.toml` keeps the wheel's platform policy:

- CPython 3.11 to 3.15 and free-threaded 3.15t, Linux x86_64 manylinux wheels.
- CPython 3.11 to 3.15 and free-threaded 3.15t, Windows AMD64 wheels.
- CPython 3.13 and 3.14, Android arm64-v8a and x86_64 wheels.
- Pyodide and WebAssembly wheels from the shared release workflow.

Native wheel smoke tests import `lvgl`, call `init()` and call `deinit()`.

### Check a wheel locally

```bash
python -m pip install build
python -m build --wheel
python -m pip install --force-reinstall dist/pydevices_lvgl-*.whl
python -m unittest discover -s ports/cpython/tests -v
```

The wheel must contain `lvgl.pyi` beside the native extension; the tests verify
the install. To reproduce the release platforms, use cibuildwheel: Linux
manylinux builds need Docker, Windows builds need native MSVC, and Android
builds need the Android SDK and NDK that cibuildwheel uses.

## Don't change CircuitPython or MicroPython

Don't commit changes inside an interpreter checkout. Durable fixes belong here:
the ports' build files, `ports/circuitpython/scripts/partitions-16MB-lvgl.csv`
and the sources.

## The docs site

The LVGL documentation is built from `docs/`:

```bash
pip install -r docs/requirements.txt
sphinx-build -W --keep-going -b html docs _site
```

`-W` fails on any warning, as Read the Docs does.
