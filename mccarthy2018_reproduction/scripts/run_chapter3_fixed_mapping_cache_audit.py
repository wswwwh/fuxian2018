"""Audit cached fixed-mapping quasi-DRO corrections against current gates.

The repository contains a fixed-mapping DRO cache with members above the
10,500 km target.  This script treats that cache as a candidate Route H and
revalidates it with the current Chapter 3 gate semantics before any figure or
downstream Chapter 4/5 decision can use it.
"""

from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for candidate in (SRC, SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_chapter3_integrated_breakthrough as campaign
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    _correction_condition_estimate,
    _member_from_correction,
    chapter3_quasi_dro_validation_row,
    write_chapter3_quasi_dro_validation,
    write_corrected_dro_family_csv,
)

DEFAULT_CACHE = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "cache"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_audit.csv"
ACCEPTED_FAMILY_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_family.csv"
)
ACCEPTED_VALIDATION_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_accepted_validation.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_fixed_mapping_cache_audit.md"

FIELDS = (
    "member_index",
    "correction_type",
    "curve_samples",
    "previous_max_abs_z_km",
    "max_abs_z_km",
    "delta_max_abs_z_km",
    "previous_rho_rad",
    "rho_rad",
    "delta_rho_rad",
    "mapping_time_days",
    "mapping_time_error_days",
    "mean_jacobi",
    "map_residual_max",
    "curve_jacobi_span",
    "amplitude_residual",
    "phase_residual",
    "one_map_sweep_jacobi_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "validation_status",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_4_rho_monotone",
    "gate_5_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "strict_acceptance",
    "passes_10500_gate",
    "passes_11000_gate",
    "failed_gates",
)


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _float_from_validation(validation: dict[str, str], key: str) -> float | None:
    return campaign._float_from_validation(validation, key)


def _write_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=FIELDS).writeheader()


def _append_row(row: dict[str, Any]) -> None:
    with OUTPUT.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writerow({field: _fmt(row.get(field)) for field in FIELDS})
        stream.flush()


def _load_cache(path: Path) -> tuple[Any, ...]:
    with path.open("rb") as stream:
        cached = pickle.load(stream)
    if not isinstance(cached, tuple):
        raise RuntimeError(f"fixed-mapping cache did not contain a tuple: {path}")
    return cached


def _row_for_member(
    *,
    member_index: int,
    correction: Any,
    previous_member: Any | None,
    validation: dict[str, str],
) -> dict[str, Any]:
    system = SYSTEMS["earth_moon"]
    member = _member_from_correction(member_index, correction, system)
    previous_max_z = None if previous_member is None else previous_member.max_abs_z_km
    previous_rho = None if previous_member is None else previous_member.rotation_angle_rad
    one_map_drift = _float_from_validation(validation, "one_map_sweep_jacobi_drift")
    ten_return = _float_from_validation(validation, "ten_return_jacobi_span")
    phase_return = _float_from_validation(validation, "one_map_phase_return_error")
    condition = _correction_condition_estimate(correction)
    gate_1 = member.map_residual_norm < campaign.GATE_1_MAP_RESIDUAL
    gate_2 = (
        member.curve_jacobi_span < campaign.GATE_2_CURVE_JACOBI_SPAN
        and one_map_drift is not None
        and one_map_drift < campaign.GATE_2_ONE_MAP_JACOBI_DRIFT
        and ten_return is not None
        and ten_return < campaign.GATE_2_TEN_RETURN_JACOBI
    )
    gate_3 = (
        abs(member.phase_residual) < campaign.GATE_3_PHASE_RETURN
        and phase_return is not None
        and phase_return < campaign.GATE_3_PHASE_RETURN
    )
    gate_4 = previous_rho is None or member.rotation_angle_rad > previous_rho
    gate_5 = previous_max_z is None or member.max_abs_z_km >= previous_max_z - campaign.GATE_5_AMPLITUDE_TOL_KM
    gate_6 = abs(member.mapping_time_days - campaign.T_FIXED_DAYS) < campaign.GATE_6_MAPPING_TIME_DAYS
    gate_7 = condition is not None and condition < campaign.GATE_7_SCALED_CONDITION
    gates = {
        "gate_1_residual": gate_1,
        "gate_2_jacobi": gate_2,
        "gate_3_phase": gate_3,
        "gate_4_rho_monotone": gate_4,
        "gate_5_amplitude": gate_5,
        "gate_6_mapping_time": gate_6,
        "gate_7_condition": gate_7,
    }
    failed = tuple(name for name, passed in gates.items() if not passed)
    strict_acceptance = not failed
    return {
        "member_index": member_index,
        "correction_type": type(correction).__name__,
        "curve_samples": member.states.shape[0],
        "previous_max_abs_z_km": previous_max_z,
        "max_abs_z_km": member.max_abs_z_km,
        "delta_max_abs_z_km": None if previous_max_z is None else member.max_abs_z_km - previous_max_z,
        "previous_rho_rad": previous_rho,
        "rho_rad": member.rotation_angle_rad,
        "delta_rho_rad": None if previous_rho is None else member.rotation_angle_rad - previous_rho,
        "mapping_time_days": member.mapping_time_days,
        "mapping_time_error_days": member.mapping_time_days - campaign.T_FIXED_DAYS,
        "mean_jacobi": member.mean_jacobi,
        "map_residual_max": member.map_residual_norm,
        "curve_jacobi_span": member.curve_jacobi_span,
        "amplitude_residual": member.amplitude_residual,
        "phase_residual": member.phase_residual,
        "one_map_sweep_jacobi_drift": one_map_drift,
        "jacobi_ten_return_span": ten_return,
        "phase_return_error": phase_return,
        "condition_number": condition,
        "validation_status": validation.get("validation_status"),
        **gates,
        "strict_acceptance": strict_acceptance,
        "passes_10500_gate": strict_acceptance and member.max_abs_z_km >= campaign.TARGET_MIN_KM,
        "passes_11000_gate": strict_acceptance and member.max_abs_z_km >= campaign.TARGET_STRETCH_KM,
        "failed_gates": "; ".join(failed),
    }


def _write_doc(
    rows: list[dict[str, Any]],
    cache_path: Path,
    accepted_family: tuple[Any, ...],
) -> None:
    accepted = [row for row in rows if bool(row["strict_acceptance"])]
    accepted_10500 = [row for row in accepted if bool(row["passes_10500_gate"])]
    accepted_11000 = [row for row in accepted if bool(row["passes_11000_gate"])]
    best = max(rows, key=lambda row: float(row["max_abs_z_km"])) if rows else None
    best_accepted = max(accepted, key=lambda row: float(row["max_abs_z_km"])) if accepted else None
    best_family_member = (
        max(accepted_family, key=lambda member: member.max_abs_z_km)
        if accepted_family
        else None
    )
    lines = "\n".join(
        f"- member `{row['member_index']}`: z `{float(row['max_abs_z_km']):.12g}` km, "
        f"rho `{float(row['rho_rad']):.12g}`, strict `{row['strict_acceptance']}`, "
        f"failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Fixed-Mapping Cache Audit

## Scope

This Route H audit revalidates the cached fixed-mapping DRO continuation file
`{cache_path.relative_to(PROJECT_ROOT)}` with the current seven-gate policy.
It exists because the cache contains members above 10,500 km that were not part
of the current staged gate audit.

## Outcome

- Rows audited: `{len(rows)}`
- Strictly accepted rows: `{len(accepted)}`
- Strictly accepted rows above 10,500 km: `{len(accepted_10500)}`
- Strictly accepted rows above 11,000 km: `{len(accepted_11000)}`
- Best trial max abs z: `{best['max_abs_z_km'] if best else 'N/A'}` km
- Best strict accepted max abs z: `{best_accepted['max_abs_z_km'] if best_accepted else 'N/A'}` km
- Exported monotone accepted family members: `{len(accepted_family)}`
- Exported monotone family best max abs z: `{best_family_member.max_abs_z_km if best_family_member else 'N/A'}` km

## Exported Data

- `{ACCEPTED_FAMILY_OUTPUT.relative_to(PROJECT_ROOT)}`
- `{ACCEPTED_VALIDATION_OUTPUT.relative_to(PROJECT_ROOT)}`

## Rows

{lines}

## Interpretation

If this audit finds accepted rows above 10,500 km, the staged gate audit must be
updated and Chapter 4 can begin from those accepted fixed-time torus data. If
high-amplitude rows fail strict Jacobi, phase, mapping-time, or conditioning
gates, the cache remains diagnostic and cannot unlock downstream figures.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--min-z-km", type=float, default=10500.0)
    parser.add_argument("--max-members", type=int, default=None)
    args = parser.parse_args()
    if args.max_members is not None and args.max_members <= 0:
        raise SystemExit("--max-members must be positive")
    if not args.cache.exists():
        raise SystemExit(f"missing fixed-mapping cache: {args.cache}")

    cached = _load_cache(args.cache)
    system = SYSTEMS["earth_moon"]
    members = [_member_from_correction(index, correction, system) for index, correction in enumerate(cached)]
    candidate_indices = [
        index
        for index, member in enumerate(members)
        if member.max_abs_z_km >= args.min_z_km
    ]
    if args.max_members is not None:
        candidate_indices = candidate_indices[: args.max_members]

    _write_header(OUTPUT)
    rows: list[dict[str, Any]] = []
    accepted_family: list[Any] = []
    for index in candidate_indices:
        correction = cached[index]
        member = members[index]
        previous = members[index - 1] if index > 0 else None
        print(f"cache_member_{index}: z={member.max_abs_z_km:.6f} km", flush=True)
        validation = chapter3_quasi_dro_validation_row(
            member,
            system,
            one_map_time_samples=7,
            ten_return_samples=401,
            max_step=campaign.bvp.INTEGRATION_MAX_STEP,
        )
        row = _row_for_member(
            member_index=index,
            correction=correction,
            previous_member=previous,
            validation=validation,
        )
        _append_row(row)
        rows.append(row)
        if bool(row["strict_acceptance"]) and (
            not accepted_family
            or member.target_vertical_amplitude_nd > accepted_family[-1].target_vertical_amplitude_nd
        ):
            accepted_family.append(member)
        print(
            f"cache_member_{index}: strict={row['strict_acceptance']} "
            f"failed={row['failed_gates']}",
            flush=True,
        )

    accepted_tuple = tuple(accepted_family)
    if accepted_tuple:
        write_corrected_dro_family_csv(ACCEPTED_FAMILY_OUTPUT, accepted_tuple)
        write_chapter3_quasi_dro_validation(
            ACCEPTED_VALIDATION_OUTPUT,
            accepted_tuple,
            system,
            one_map_time_samples=7,
            ten_return_samples=401,
            max_step=campaign.bvp.INTEGRATION_MAX_STEP,
        )
    _write_doc(rows, args.cache, accepted_tuple)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    if accepted_tuple:
        print(f"wrote {ACCEPTED_FAMILY_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
        print(f"wrote {ACCEPTED_VALIDATION_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "fixed-mapping cache audit: "
        f"rows={len(rows)}, accepted={sum(bool(row['strict_acceptance']) for row in rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
