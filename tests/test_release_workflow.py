from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_regeneration_has_no_release_mutation_options():
    script = (ROOT / "regenerate_all.sh").read_text()
    assert "--no-commit" not in script
    assert "--no-tag" not in script
    assert "git commit" not in script
    assert "git tag" not in script


def test_release_workflow_is_manual_and_publish_is_opt_in():
    workflow = (ROOT / ".github/workflows/release.yml").read_text()
    assert "workflow_dispatch:" in workflow
    assert "default: dry-run" in workflow
    assert "if: inputs.mode == 'release'" in workflow
    assert "needs: [validate, matrix]" in workflow
    # One repository: nothing to dispatch a release to.
    assert "gh workflow run" not in workflow
    assert not (ROOT / ".github/workflows/check-dispatch-token.yml").exists()
    assert not (ROOT / "scripts/publish_release_tag.sh").exists()


def test_release_gate_is_non_mutating_and_runs_full_validation():
    script = (ROOT / "scripts/release_dry_run.sh").read_text()
    assert "pytest" in script
    assert "verify_bindings.sh" in script
    assert "regenerate_all.sh --check --hash" in script
    assert "publish_release_tag.sh" not in script


def test_linux_integration_builds_every_port_from_this_checkout():
    workflow = (ROOT / ".github/workflows/linux-integration.yml").read_text()
    assert "ports/micropython/manifest.py" in workflow
    assert 'USER_C_MODULES="$GITHUB_WORKSPACE/integration/omnipython-lvgl/ports/circuitpython"' in workflow
    assert "pip install -e ." in workflow
    assert "ports/cpython/tests" in workflow
    assert "test_lvgl_smoke.py" in workflow
    # The ports read the binding from the same tree: no consumer checkout,
    # no pin to write.
    assert "repository: PyDevices/" not in workflow
    assert "LVGL_BINDINGS_COMMIT" not in workflow
