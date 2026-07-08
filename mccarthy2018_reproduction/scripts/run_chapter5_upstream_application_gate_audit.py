"""Audit Chapter 5 application readiness after Route H upstream upgrades.

This audit distinguishes a regenerated Route H/DE421 baseline from the
high-fidelity BCR4BP or optimized-transfer layer requested for Chapter 5.  It
lets the staged gate record concrete Chapter 5 progress without overclaiming
that the final application layer is complete.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import load_best_chapter3_corrected_dro_family

OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_upstream_application_gate_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_upstream_application_gate_audit.md"

BASE_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family.csv"
EXTENDED_FAMILY_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
)
PALC_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
CONTINUATION_LOG_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_continuation_log.csv"
ROUTE_H_FAMILY_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"
ROUTE_H_VALIDATION_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_validation.csv"
)
CHAPTER4_ROUTE_H_FIGURE = PROJECT_ROOT / "outputs" / "figures_png" / "fig_4_route_h.png"
FIG_5_6 = PROJECT_ROOT / "outputs" / "figures_png" / "fig_5_6.png"
FIG_5_7 = PROJECT_ROOT / "outputs" / "figures_png" / "fig_5_7.png"
DE421_KERNEL = PROJECT_ROOT / "data" / "raw" / "ephemeris" / "de421.bsp"
READINESS_AUDIT = PROJECT_ROOT / "data" / "computed" / "chapter5_high_fidelity_optimization_readiness_audit.csv"

FIELDS = (
    "gate_id",
    "requirement",
    "status",
    "metric",
    "value",
    "threshold",
    "evidence_artifact",
    "decision",
    "notes",
)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if np.isfinite(number):
            return f"{number:.16g}"
        return str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _artifact(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _row(
    *,
    gate_id: str,
    requirement: str,
    status: str,
    metric: str,
    value: Any,
    threshold: str,
    evidence_artifact: str,
    decision: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "requirement": requirement,
        "status": status,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "evidence_artifact": evidence_artifact,
        "decision": decision,
        "notes": notes,
    }


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _write_doc(rows: list[dict[str, Any]], *, route_h_member: Any) -> None:
    lines = "\n".join(
        f"- `{row['gate_id']}`: status `{row['status']}`, metric "
        f"`{row['metric']}` = `{_fmt(row['value'])}`, decision `{row['decision']}`"
        for row in rows
    )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 Upstream Application Gate Audit

## Purpose

This file records whether Chapter 5 can use the upgraded upstream quasi-DRO
evidence without overstating the result as high-fidelity or optimized.

## Current Route H Input

- Source member id: `{route_h_member.member}`
- Max abs z: `{route_h_member.max_abs_z_km}` km
- Rotation angle rho: `{route_h_member.rotation_angle_rad}` rad
- Mapping time: `{route_h_member.mapping_time_days}` days

## Gate Rows

{lines}

## Decision

Figures 5.6 and 5.7 now have a regenerated Route H / DE421-oriented baseline
from the accepted high-amplitude quasi-DRO branch. The stricter high-fidelity
readiness decision is generated separately by
`scripts/run_chapter5_high_fidelity_optimization_readiness_audit.py`; when that
audit passes, the Chapter 5 source-layer optimization result supersedes this
baseline-only gate.
""",
        encoding="utf-8",
    )


def main() -> None:
    system = SYSTEMS["earth_moon"]
    family = load_best_chapter3_corrected_dro_family(
        BASE_FAMILY_PATH,
        EXTENDED_FAMILY_PATH,
        PALC_FAMILY_PATH,
        CONTINUATION_LOG_PATH,
        system,
        ROUTE_H_FAMILY_PATH,
    )
    route_h_member = family[-1]
    ch3_pass = route_h_member.max_abs_z_km >= 10500.0 and ROUTE_H_VALIDATION_PATH.exists()
    ch4_route_h_pass = CHAPTER4_ROUTE_H_FIGURE.exists() and CHAPTER4_ROUTE_H_FIGURE.stat().st_size > 0
    de421_pass = DE421_KERNEL.exists() and DE421_KERNEL.stat().st_size > 0
    fig56_pass = FIG_5_6.exists() and FIG_5_6.stat().st_size > 0
    fig57_pass = FIG_5_7.exists() and FIG_5_7.stat().st_size > 0
    route_h_de421_baseline_pass = ch3_pass and ch4_route_h_pass and de421_pass and fig56_pass and fig57_pass
    readiness_rows = _read_rows(READINESS_AUDIT)
    readiness_by_gate = {row.get("gate_id", ""): row for row in readiness_rows}
    high_fidelity_pass = readiness_by_gate.get("C5-HF-READINESS-STATUS", {}).get("status") == "pass"

    rows = [
        _row(
            gate_id="C5-UPSTREAM-ROUTE-H-INPUT",
            requirement="Chapter 5 quasi-DRO application baselines must use an accepted high-amplitude upstream quasi-DRO member.",
            status="pass" if ch3_pass else "fail",
            metric="route_h_member_max_abs_z_km",
            value=route_h_member.max_abs_z_km,
            threshold=">= 10500",
            evidence_artifact=f"{_artifact(ROUTE_H_FAMILY_PATH)};{_artifact(ROUTE_H_VALIDATION_PATH)}",
            decision="use_route_h_member_for_chapter5_baseline" if ch3_pass else "keep_chapter5_blocked",
            notes="Uses the strongest accepted combined Chapter 3 family member.",
        ),
        _row(
            gate_id="C5-UPSTREAM-CHAPTER4-SOURCE",
            requirement="Chapter 5 must not advance beyond baseline unless the Chapter 4 torus/DG source layer is regenerated.",
            status="pass" if ch4_route_h_pass else "fail",
            metric="fig_4_route_h_png_bytes",
            value=CHAPTER4_ROUTE_H_FIGURE.stat().st_size if CHAPTER4_ROUTE_H_FIGURE.exists() else None,
            threshold="> 0",
            evidence_artifact=_artifact(CHAPTER4_ROUTE_H_FIGURE),
            decision="route_h_chapter4_source_available" if ch4_route_h_pass else "wait_for_chapter4",
            notes="This is Route H quasi-DRO source-layer evidence, not original L1 thesis-scale manifold replacement.",
        ),
        _row(
            gate_id="C5-ROUTE-H-DE421-BASELINE",
            requirement="Route H quasi-DRO DE421-oriented application figures must be regenerated from the accepted member.",
            status="pass" if route_h_de421_baseline_pass else "fail",
            metric="fig_5_6_png_bytes",
            value=FIG_5_6.stat().st_size if FIG_5_6.exists() else None,
            threshold="> 0 and Fig. 5.7 exists",
            evidence_artifact=f"{_artifact(FIG_5_6)};{_artifact(FIG_5_7)};{_artifact(DE421_KERNEL)}",
            decision="route_h_de421_baseline_available" if route_h_de421_baseline_pass else "regenerate_fig_5_6_5_7",
            notes="DE421 frame embedding is a geometry baseline, not a corrected ephemeris trajectory.",
        ),
        _row(
            gate_id="C5-HIGH-FIDELITY-OPTIMIZATION",
            requirement="High-fidelity Chapter 5 upgrade requires BCR4BP/ephemeris correction or optimized transfer evidence.",
            status="pass" if high_fidelity_pass else "blocked_missing_high_fidelity_optimization",
            metric="missing_high_fidelity_capabilities",
            value=readiness_by_gate.get("C5-HF-READINESS-STATUS", {}).get("value", 0),
            threshold="0",
            evidence_artifact=_artifact(READINESS_AUDIT) if READINESS_AUDIT.exists() else "none",
            decision="use_readiness_audit_source_layer_result" if high_fidelity_pass else "do_not_claim_high_fidelity_chapter5",
            notes=(
                "Readiness audit supplies accepted Route H/BCR4BP correction and optimized-transfer source-layer evidence."
                if high_fidelity_pass
                else "No accepted high-fidelity/optimization readiness audit exists yet."
            ),
        ),
        _row(
            gate_id="C5-STAGED-APPLICATION-STATUS",
            requirement="Record whether Chapter 5 has progressed from proxy to Route H baseline or full high-fidelity application.",
            status=(
                "route_h_bcr4bp_optimization_source_layer_passed"
                if high_fidelity_pass
                else "route_h_de421_baseline_ready_high_fidelity_blocked"
                if route_h_de421_baseline_pass
                else "blocked_before_route_h_baseline"
            ),
            metric="route_h_de421_baseline_pass",
            value=route_h_de421_baseline_pass,
            threshold="true",
            evidence_artifact=f"{_artifact(OUTPUT)};{_artifact(DOC_OUTPUT)}",
            decision=(
                "chapter5_source_layer_optimization_available"
                if high_fidelity_pass
                else "next_define_bcr4bp_or_optimization_audit"
                if route_h_de421_baseline_pass
                else "regenerate_route_h_chapter5_baseline"
            ),
            notes="Baseline gate defers the final high-fidelity decision to the readiness audit.",
        ),
    ]

    _write_rows(rows)
    _write_doc(rows, route_h_member=route_h_member)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "chapter5 upstream audit: "
        f"route_h_de421_baseline={route_h_de421_baseline_pass}, "
        f"high_fidelity={'pass' if high_fidelity_pass else 'blocked_missing_high_fidelity_optimization'}",
        flush=True,
    )


if __name__ == "__main__":
    main()
