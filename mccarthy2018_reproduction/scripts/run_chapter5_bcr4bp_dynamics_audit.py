"""Audit the Chapter 5 BCR4BP dynamics kernel.

This audit validates only the dynamics-model layer.  It does not provide an
ephemeris-corrected multiple-shooting solution or an optimized transfer.
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

from qp_orbits.bcr4bp import (  # noqa: E402
    BCR4BPParameters,
    bcr4bp_rhs,
    bicircular_solar_acceleration,
    earth_moon_bcr4bp_parameters,
    integrate_bcr4bp,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.corrected_dro_family import load_corrected_dro_family_csv  # noqa: E402
from qp_orbits.cr3bp import cr3bp_rhs  # noqa: E402


OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter5_bcr4bp_dynamics_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter5_bcr4bp_dynamics_audit.md"
ROUTE_H_FAMILY = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"

FIELDS = (
    "gate_id",
    "requirement",
    "status",
    "metric",
    "value",
    "threshold",
    "acceptance",
    "evidence_artifact",
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
    acceptance: bool,
    evidence_artifact: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "requirement": requirement,
        "status": status,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "acceptance": acceptance,
        "evidence_artifact": evidence_artifact,
        "notes": notes,
    }


def _write_rows(rows: list[dict[str, Any]]) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})


def _write_doc(rows: list[dict[str, Any]], params: BCR4BPParameters) -> None:
    row_lines = "\n".join(
        f"- `{row['gate_id']}`: status `{row['status']}`, metric "
        f"`{row['metric']}` = `{_fmt(row['value'])}`, acceptance `{_fmt(row['acceptance'])}`"
        for row in rows
    )
    DOC_OUTPUT.write_text(
        f"""# Chapter 5 BCR4BP Dynamics Audit

## Purpose

This file validates the first high-fidelity interface layer: a bicircular
Sun-Earth-Moon dynamics kernel in the same normalized Earth-Moon rotating frame
used by the CR3BP code.

## Mean Parameters

- `mu`: `{params.mu}`
- `sun_mass_parameter`: `{params.sun_mass_parameter}`
- `sun_distance`: `{params.sun_distance}`
- `sun_angular_rate`: `{params.sun_angular_rate}`

## Gate Rows

{row_lines}

## Decision

The BCR4BP dynamics kernel is available as a model-level building block. This
does not complete Chapter 5 high-fidelity reproduction: ephemeris-corrected
multiple shooting and optimized-transfer acceptance rows are still required
before promoted application figures can be claimed.
""",
        encoding="utf-8",
    )


def _route_h_initial_state() -> tuple[np.ndarray, int, float]:
    family = load_corrected_dro_family_csv(ROUTE_H_FAMILY, require_contiguous_members=False)
    member = family[-1]
    return member.states[0].copy(), member.member, member.max_abs_z_km


def main() -> None:
    system = SYSTEMS["earth_moon"]
    params = earth_moon_bcr4bp_parameters(system)
    probe_state = np.array([0.82, 0.04, 0.02, 0.0, 0.18, 0.01], dtype=float)

    cr3bp_reduction_error = float(
        np.max(np.abs(bcr4bp_rhs(0.37, probe_state, params.without_sun()) - cr3bp_rhs(0.37, probe_state, system.mu)))
    )
    barycenter_tide_norm = float(np.linalg.norm(bicircular_solar_acceleration(1.23, [0.0, 0.0, 0.0], params)))

    sample_times = np.linspace(0.0, 2.0 * np.pi, 9)
    rhs_samples = np.array([bcr4bp_rhs(time, probe_state, params) for time in sample_times])
    finite_rhs_acceptance = bool(np.all(np.isfinite(rhs_samples)))

    route_h_state, route_h_member, route_h_max_abs_z_km = _route_h_initial_state()
    t_eval = np.linspace(0.0, 0.05, 21)
    route_h_solution = integrate_bcr4bp(
        route_h_state,
        (float(t_eval[0]), float(t_eval[-1])),
        params,
        t_eval=t_eval,
        rtol=1.0e-10,
        atol=1.0e-12,
        max_step=0.005,
    )
    route_h_state_span = (
        float(np.max(np.linalg.norm(route_h_solution.y.T - route_h_solution.y[:, [0]].T, axis=1)))
        if route_h_solution.success
        else float("nan")
    )
    route_h_acceptance = bool(
        route_h_solution.success
        and route_h_solution.y.shape[1] == t_eval.size
        and np.all(np.isfinite(route_h_solution.y))
    )

    rows = [
        _row(
            gate_id="C5-BCR4BP-CR3BP-REDUCTION",
            requirement="The BCR4BP RHS must reduce to the existing CR3BP RHS when the solar mass parameter is zero.",
            status="pass" if cr3bp_reduction_error <= 1.0e-14 else "fail",
            metric="max_rhs_difference",
            value=cr3bp_reduction_error,
            threshold="<= 1e-14",
            acceptance=cr3bp_reduction_error <= 1.0e-14,
            evidence_artifact="src/qp_orbits/bcr4bp.py;src/qp_orbits/cr3bp.py",
            notes="This guards the state ordering and rotating-frame acceleration convention.",
        ),
        _row(
            gate_id="C5-BCR4BP-BARYCENTER-TIDE",
            requirement="The differential solar acceleration should vanish at the Earth-Moon barycenter.",
            status="pass" if barycenter_tide_norm <= 1.0e-14 else "fail",
            metric="barycenter_solar_acceleration_norm",
            value=barycenter_tide_norm,
            threshold="<= 1e-14",
            acceptance=barycenter_tide_norm <= 1.0e-14,
            evidence_artifact="src/qp_orbits/bcr4bp.py",
            notes="This verifies that the solar term is differential, not an absolute inertial pull.",
        ),
        _row(
            gate_id="C5-BCR4BP-FINITE-RHS",
            requirement="The mean Sun-Earth-Moon BCR4BP RHS must remain finite over one relative Sun-angle cycle for a representative state.",
            status="pass" if finite_rhs_acceptance else "fail",
            metric="finite_rhs_samples",
            value=int(np.sum(np.all(np.isfinite(rhs_samples), axis=1))),
            threshold=str(sample_times.size),
            acceptance=finite_rhs_acceptance,
            evidence_artifact="src/qp_orbits/bcr4bp.py",
            notes="This is a model-level sanity check, not a trajectory correction result.",
        ),
        _row(
            gate_id="C5-BCR4BP-ROUTE-H-SHORT-PROPAGATION",
            requirement="The BCR4BP kernel must accept the current Route H quasi-DRO source as an initial guess without numerical failure.",
            status="pass" if route_h_acceptance else "fail",
            metric="route_h_short_propagation_state_span",
            value=route_h_state_span,
            threshold="finite integration over 0.05 normalized time",
            acceptance=route_h_acceptance,
            evidence_artifact=f"{_artifact(ROUTE_H_FAMILY)};src/qp_orbits/bcr4bp.py",
            notes=f"Route H member {route_h_member}, max abs z {route_h_max_abs_z_km} km.",
        ),
    ]

    _write_rows(rows)
    _write_doc(rows, params)
    accepted = sum(1 for row in rows if row["acceptance"])
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"chapter5 BCR4BP dynamics audit: accepted_rows={accepted}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
