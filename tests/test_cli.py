"""Tests for the unified ``research-toolkit`` CLI (scripts/cli.py).

Covers top-level help, subcommand --help delegation across both argv shapes
(sliced vs full + the non-argparse ``freshness`` fallback), unknown-subcommand
handling, a real subcommand run against a fixture project, and that the
declared console entry point (``scripts.cli:main``) is importlib-loadable +
callable (i.e. ``pip install -e .`` would expose it). No network, no
unittest.mock.
"""
from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts import cli  # type: ignore[import-not-found]  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures"


# ---------- top-level help ----------


def test_cli_help_lists_subcommands(capsys) -> None:
    rc = cli.main(["--help"])
    assert rc == 0
    out = capsys.readouterr().out
    # A representative spread of the core pipeline verbs must be listed.
    for verb in ("assemble", "render-index", "verify-citations", "freshness", "export"):
        assert verb in out, f"--help missing subcommand {verb!r}"


def test_cli_no_args_prints_help(capsys) -> None:
    rc = cli.main([])
    assert rc == 0
    assert "subcommand" in capsys.readouterr().out


def test_cli_rejects_unknown_subcommand(capsys) -> None:
    rc = cli.main(["definitely-not-a-verb"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown subcommand" in err


# ---------- subcommand --help delegation ----------


def test_cli_verify_citations_help_delegates(capsys) -> None:
    """A full-argv-shape script: argparse --help exits 0, surfaced as 0."""
    rc = cli.main(["verify-citations", "--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "project_dir" in out  # from verify_citations' own parser


def test_cli_assemble_help_delegates(capsys) -> None:
    """A sliced-argv-shape script delegates its own argparse help."""
    rc = cli.main(["assemble", "--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "sources" in out and "project_dir" in out


def test_cli_freshness_help_uses_fallback(capsys) -> None:
    """freshness has no argparse parser; the CLI prints a usage fallback."""
    rc = cli.main(["freshness", "--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "freshness" in out and "project_dir" in out


# ---------- real subcommand run ----------


def test_cli_verify_citations_runs_on_fixture(tmp_path, capsys) -> None:
    """Dispatch a real run; verify_citations writes a report + exits 0.

    Copy the fixture into tmp_path first because verify_citations writes a
    citation_audit_report.md into the project dir — we must not dirty the
    committed fixture.
    """
    src = FIXTURES / "v3_strict_live_demo"
    proj = tmp_path / "proj"
    shutil.copytree(src, proj)
    rc = cli.main(["verify-citations", str(proj), "--json"])
    assert rc == 0, capsys.readouterr().err
    out = capsys.readouterr().out
    assert "substring_pass" in out  # the metrics JSON was printed
    assert (proj / "citation_audit_report.md").exists()


def test_cli_dispatch_translates_systemexit(monkeypatch, capsys) -> None:
    """If a delegated main raises SystemExit, the CLI returns its code, not raise.

    Replace one registered target's callable with a hand-rolled double that
    raises SystemExit(3) (no unittest.mock).
    """

    class _FakeModule:
        @staticmethod
        def main(argv: list[str]) -> int:
            raise SystemExit(3)

    def _fake_import(name: str):
        return _FakeModule

    monkeypatch.setattr(cli.importlib, "import_module", _fake_import)
    rc = cli.main(["export", "whatever"])
    assert rc == 3


# ---------- entry-point + registry hygiene ----------


def test_cli_entry_point_is_importable_and_callable() -> None:
    """`pip install -e .` exposes ``research-toolkit = scripts.cli:main``.

    Resolve it the way a console-script shim would, without pip-installing.
    """
    module = importlib.import_module("scripts.cli")
    fn = getattr(module, "main")
    assert callable(fn)


def test_cli_every_subcommand_has_a_summary() -> None:
    missing = [v for v in cli._REGISTRY if v not in cli._SUMMARIES]
    assert not missing, f"subcommands missing a help summary: {missing}"


def test_pyproject_declares_console_entry_point() -> None:
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" in text
    assert 'research-toolkit = "scripts.cli:main"' in text


@pytest.mark.parametrize("verb", sorted({
    "cache-source", "assemble", "render-index", "build-claim-graph",
    "verify-citations", "build-dashboard", "freshness", "export",
    "backlog-stamp", "resume-gather", "compose-kg",
}))
def test_cli_core_verbs_registered(verb: str) -> None:
    assert verb in cli._REGISTRY
