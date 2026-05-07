"""Regression tests for v1.5 — docs + structured BURN_IN + dogfood metrics CSV.

Covers:
- B7: getting_started.md + troubleshooting.md exist with reasonable size
- C8: burn_in.yml validates against a small JSON-Schema-style check;
      burn_in_query.py CLI runs and produces output
- C9: dogfood_metrics.csv parses and has ≥4 rows + correct header

These are smoke tests — content correctness is the human review's job.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
SCRIPTS = REPO_ROOT / "scripts"
BURN_IN_YML = REPO_ROOT / "burn_in.yml"
DOGFOOD_CSV = REPO_ROOT / "evals" / "dogfood_metrics.csv"


# ---------- B7: docs ----------


def test_getting_started_exists_and_reasonable_size() -> None:
    """v1.5 acceptance: getting_started.md exists, ~80 lines (target), audience-appropriate length."""
    p = DOCS / "getting_started.md"
    assert p.exists(), f"missing {p}"
    lines = p.read_text(encoding="utf-8").splitlines()
    assert 50 <= len(lines) <= 200, f"getting_started.md has {len(lines)} lines; target ~80 (50-200 OK)"


def test_troubleshooting_exists_and_reasonable_size() -> None:
    p = DOCS / "troubleshooting.md"
    assert p.exists(), f"missing {p}"
    lines = p.read_text(encoding="utf-8").splitlines()
    assert 60 <= len(lines) <= 250, f"troubleshooting.md has {len(lines)} lines; target ~60-150"


def test_getting_started_mentions_all_6_skills() -> None:
    """Sanity: walkthrough should reference each skill at least once."""
    text = (DOCS / "getting_started.md").read_text(encoding="utf-8")
    for skill in (
        "/research-plan",
        "/research-gather",
        "/dossier-build",
        "/agent-index",
        "/dossier-audit",
        "/url-freshness-check",
    ):
        assert skill in text, f"getting_started.md missing {skill}"


def test_troubleshooting_covers_known_failures() -> None:
    """Sanity: troubleshooting should cover the v1.0+ BURN_IN-listed top failures."""
    text = (DOCS / "troubleshooting.md").read_text(encoding="utf-8").lower()
    expected_topics = (
        "url extraction",  # macOS regex bug
        "modulenotfounderror",  # validator import
        "github urls",  # 404 cluster
        "memory-verification",  # anti-cheat
        "claim_family",  # cross-stage
    )
    missing = [t for t in expected_topics if t not in text]
    assert not missing, f"troubleshooting.md missing topics: {missing}"


# ---------- C8: structured BURN_IN ----------


REQUIRED_BURN_IN_FIELDS = {"id", "phase", "stage", "finding", "severity", "status"}
ALLOWED_SEVERITIES = {"high", "medium", "low"}
ALLOWED_STATUSES = {"surfaced", "applied", "deferred", "wontfix"}


def test_burn_in_yml_parses() -> None:
    assert BURN_IN_YML.exists(), f"missing {BURN_IN_YML}"
    data = yaml.safe_load(BURN_IN_YML.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "entries" in data
    assert isinstance(data["entries"], list)
    assert len(data["entries"]) >= 10, f"expected ≥10 entries, got {len(data['entries'])}"


def test_burn_in_yml_entries_well_formed() -> None:
    data = yaml.safe_load(BURN_IN_YML.read_text(encoding="utf-8"))
    seen_ids: set[str] = set()
    for i, entry in enumerate(data["entries"]):
        loc = f"entries[{i}]"
        assert isinstance(entry, dict), f"{loc}: must be a mapping"
        missing = REQUIRED_BURN_IN_FIELDS - set(entry.keys())
        assert not missing, f"{loc}: missing fields {missing}"
        assert entry["severity"] in ALLOWED_SEVERITIES, f"{loc}: bad severity"
        assert entry["status"] in ALLOWED_STATUSES, f"{loc}: bad status"
        # If status is applied, fix_version is required.
        if entry["status"] == "applied":
            assert entry.get("fix_version"), f"{loc}: status=applied requires fix_version"
        # ID uniqueness.
        assert entry["id"] not in seen_ids, f"{loc}: duplicate id {entry['id']!r}"
        seen_ids.add(entry["id"])


def test_burn_in_query_script_runs() -> None:
    """Smoke: query script doesn't crash on a known filter."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "burn_in_query.py"),
            "--severity",
            "high",
            "--format",
            "ids",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    ids = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert ids, "expected at least one high-severity ID"


def test_burn_in_query_format_options_work() -> None:
    """All 3 output formats produce non-empty output."""
    for fmt in ("table", "yaml", "ids"):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "burn_in_query.py"),
                "--phase",
                "phase-5c",
                "--format",
                fmt,
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"format={fmt}: stderr={result.stderr}"
        assert result.stdout, f"format={fmt}: empty stdout"


def test_high_severity_items_all_resolved_in_v1_5() -> None:
    """As of v1.5, all high-severity items should have status=applied.

    If this test fails, a new high-severity finding has been added without
    a fix. That's load-bearing for the v1.x release theme.
    """
    data = yaml.safe_load(BURN_IN_YML.read_text(encoding="utf-8"))
    unresolved = [
        e for e in data["entries"]
        if e.get("severity") == "high" and e.get("status") != "applied"
    ]
    assert not unresolved, (
        f"high-severity items not yet resolved:\n"
        + "\n".join(f"  - {e['id']}: {e['finding']}" for e in unresolved)
    )


# ---------- C9: dogfood metrics CSV ----------


REQUIRED_CSV_COLUMNS = {
    "date",
    "vol",
    "total_entries",
    "total_urls",
    "hard_404_count",
    "attribution_corrections_in_audit",
    "toolkit_version",
    "notes",
}


def test_dogfood_metrics_csv_parses() -> None:
    assert DOGFOOD_CSV.exists(), f"missing {DOGFOOD_CSV}"
    with DOGFOOD_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert reader.fieldnames is not None
        missing_cols = REQUIRED_CSV_COLUMNS - set(reader.fieldnames)
        assert not missing_cols, f"missing columns: {missing_cols}"
        assert len(rows) >= 4, f"expected ≥4 backfilled rows, got {len(rows)}"


def test_dogfood_metrics_dates_in_iso_format() -> None:
    import re
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    with DOGFOOD_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            assert iso_re.match(row["date"]), (
                f"row {i} date {row['date']!r} not in YYYY-MM-DD"
            )


def test_dogfood_metrics_includes_v1_0_baseline_runs() -> None:
    """The CSV should have at least vol26 (v1.0 GATE) + vol27 + vol28 (v1.1) backfilled."""
    with DOGFOOD_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        vols = [row["vol"] for row in reader]
    assert "vol26" in vols, f"missing vol26 baseline; vols={vols}"
    assert "vol27" in vols
    assert "vol28" in vols
