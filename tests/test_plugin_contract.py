"""Tests for the clean-break Claude plugin surface."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SKILLS = {
    "audit",
    "dataset-research",
    "freshness",
    "release",
    "research",
    "topic-discovery",
}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, block, _ = text.split("---", 2)
    value = yaml.safe_load(block)
    assert isinstance(value, dict)
    return value


def _copy_plugin(destination: Path) -> None:
    """Copy only the files shipped in an installed plugin cache."""
    for relative in (
        ".claude-plugin",
        "bin",
        "pyproject.toml",
        "references",
        "research_toolkit",
        "schemas",
        "scripts",
        "skills",
        "validators",
    ):
        source = REPO_ROOT / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def test_plugin_manifest_names_research_toolkit() -> None:
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "research-toolkit"
    assert manifest["version"] == "3.0.0-alpha.2"


def test_core_install_keeps_pdf_capture_opt_in_and_browser_disabled() -> None:
    project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())["project"]
    assert project["dependencies"] == ["PyYAML>=6.0"]
    extras = project["optional-dependencies"]
    assert any(item.startswith("pdfplumber") for item in extras["pdf"])
    assert any(item.startswith("docling") for item in extras["rich-pdf"])
    assert "browser" not in extras
    assert not any(
        item.startswith("playwright")
        for dependencies in extras.values()
        for item in dependencies
    )
    assert any(item.startswith("pdfplumber") for item in extras["dev"])
    assert not any(item.startswith(("docling", "playwright")) for item in extras["dev"])


def test_plugin_exposes_exactly_six_namespaced_skills() -> None:
    skill_paths = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    assert {path.parent.name for path in skill_paths} == EXPECTED_SKILLS
    assert len(skill_paths) == 6
    for path in skill_paths:
        metadata = _frontmatter(path)
        assert metadata["name"] == path.parent.name
        assert metadata["description"]


def test_plugin_skills_use_portable_resource_paths() -> None:
    for path in (REPO_ROOT / "skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        assert "${CLAUDE_PLUGIN_ROOT}" in text
        assert "~/Claude/research_toolkit" not in text


def test_plugin_workflows_use_bundled_cli_launcher() -> None:
    launcher = "${CLAUDE_PLUGIN_ROOT}/bin/research-toolkit"
    for name in EXPECTED_SKILLS:
        text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
        assert launcher in text, name


def test_bundled_cli_runs_from_isolated_plugin_copy(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin-cache" / "research-toolkit"
    _copy_plugin(plugin)

    dossier = tmp_path / "dossier"
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["RESEARCH_TOOLKIT_PYTHON"] = sys.executable
    result = subprocess.run(
        [
            str(plugin / "bin" / "research-toolkit"),
            "research",
            "run",
            str(dossier),
            "--initialize",
            "--dossier-id",
            "dossier_plugin_smoke",
            "--topic",
            "Plugin portability smoke test",
            "--run-id",
            "run_plugin_smoke",
            "--date",
            "2026-07-14",
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "READY: research run boundary validates" in result.stdout
    assert (dossier / "dossier.yaml").is_file()


def test_bundled_cli_ignores_hostile_cwd_and_pythonpath(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin-cache" / "research-toolkit"
    _copy_plugin(plugin)

    hostile = tmp_path / "hostile-repository"
    hostile.mkdir()
    marker = hostile / "shadow-imported.txt"
    payload = (
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text(__name__, encoding='utf-8')\n"
        "raise RuntimeError('hostile import executed')\n"
    )
    (hostile / "yaml.py").write_text(payload, encoding="utf-8")
    (hostile / "sitecustomize.py").write_text(payload, encoding="utf-8")
    for package in ("research_toolkit", "scripts", "validators"):
        package_dir = hostile / package
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text(payload, encoding="utf-8")
    (hostile / "scripts" / "cli.py").write_text(payload, encoding="utf-8")

    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(hostile)
    environment["RESEARCH_TOOLKIT_PYTHON"] = sys.executable
    result = subprocess.run(
        [str(plugin / "bin" / "research-toolkit"), "--help"],
        cwd=hostile,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "canonical workflows" in result.stdout
    assert not marker.exists(), marker.read_text() if marker.exists() else ""

    legacy = tmp_path / "legacy"
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "v3_strict_live_demo", legacy)
    target = tmp_path / "canonical"
    import_result = subprocess.run(
        [
            str(plugin / "bin" / "research-toolkit"),
            "import-legacy",
            str(legacy),
            str(target),
        ],
        cwd=hostile,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert import_result.returncode == 0, import_result.stderr
    assert (target / "sources.jsonl").is_file()
    assert not marker.exists(), marker.read_text() if marker.exists() else ""


def test_bundled_cli_rejects_external_launcher_symlink(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin-cache" / "research-toolkit"
    _copy_plugin(plugin)
    external = tmp_path / "untrusted-repository"
    external.mkdir()
    launcher = external / "research-toolkit"
    launcher.symlink_to(plugin / "bin" / "research-toolkit")

    environment = os.environ.copy()
    environment["RESEARCH_TOOLKIT_PYTHON"] = sys.executable
    result = subprocess.run(
        [str(launcher), "--help"],
        cwd=external,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "refusing symlinked" in result.stderr


def test_bundled_cli_uvx_fallback_refreshes_local_package(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_uvx = fake_bin / "uvx"
    fake_uvx.write_text(
        "#!/bin/sh\n"
        "printf 'PYTHONPATH=%s\\n' \"${PYTHONPATH-unset}\"\n"
        "printf '%s\\n' \"$@\"\n",
        encoding="utf-8",
    )
    fake_uvx.chmod(0o755)

    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"
    environment["PYTHONPATH"] = str(tmp_path / "hostile-pythonpath")
    environment["RESEARCH_TOOLKIT_PYTHON"] = "python-that-does-not-exist"
    environment["UV_CACHE_DIR"] = str(tmp_path / "uv-cache")
    result = subprocess.run(
        [str(REPO_ROOT / "bin" / "research-toolkit"), "--help"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "PYTHONPATH=unset"
    assert lines[1:] == [
        "--quiet",
        "--isolated",
        "--refresh-package",
        "research-toolkit",
        "--from",
        str(REPO_ROOT),
        "research-toolkit",
        "--help",
    ]


def test_decision_protocol_is_self_contained() -> None:
    protocol = (REPO_ROOT / "references" / "decision_protocol.md").read_text()
    assert "do not require a personal `/exploring-options` installation" in protocol
    for name in ("research", "dataset-research", "topic-discovery"):
        text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
        assert "decision_protocol.md" in text


def test_legacy_flat_skill_directory_has_no_skill_bodies() -> None:
    assert not list((REPO_ROOT / ".claude" / "skills").glob("*.md"))


def test_retired_retry_scripts_have_no_network_or_mutation_implementation() -> None:
    for name in ("retry_escalations.py", "retry_escalations_v2.py"):
        path = REPO_ROOT / "scripts" / name
        text = path.read_text(encoding="utf-8")
        for forbidden in (
            "urlopen",
            "_FETCH",
            "update_dossier_metadata",
            "cache_blob",
            "yaml.safe_dump",
        ):
            assert forbidden not in text, (name, forbidden)
        result = subprocess.run(
            [sys.executable, str(path), "--update-manifests"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2
        assert "retired" in result.stderr
