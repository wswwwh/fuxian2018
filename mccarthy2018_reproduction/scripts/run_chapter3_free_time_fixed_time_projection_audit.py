"""Audit high-amplitude free-time states projected to fixed mapping time.

The monotone-rho and simple amplitude-chart routes both stalled below 10,500 km.
This script tests the next chart change: start from high-amplitude free-time
states, fix the McCarthy mapping time, and add an explicit max-|z| target row so
the projection cannot collapse silently back to the 10,27x km fixed-time fold.

The output is diagnostic only.  It does not update Fig. 3.16 / Fig. 3.17 source
data.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_chapter3_integrated_breakthrough as campaign

FREE_TIME_STATE_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_free_time_branch_states.npz"
)
PARAMETER_AWARE_STATE_PATH = (
    PROJECT_ROOT / "data" / "computed" / "chapter3_route_b_parameter_aware_palc_states.npz"
)
OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter3_free_time_fixed_time_projection_audit.csv"
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter3_free_time_fixed_time_projection_audit.md"

TARGET_MIN_KM = 10500.0
TARGET_STRETCH_KM = 11000.0

FIELDS = (
    "attempt_id",
    "source_archive",
    "source_case_id",
    "source_index",
    "source_mapping_time_days",
    "source_max_abs_z_km",
    "source_rho_rad",
    "source_mean_jacobi",
    "target_max_abs_z_km",
    "projected_max_abs_z_km",
    "amplitude_error_km",
    "projected_rho_rad",
    "projected_mean_jacobi",
    "converged",
    "projection_acceptance",
    "passed_10500_gate",
    "passed_11000_gate",
    "map_residual_max",
    "jacobi_mean_span",
    "jacobi_one_map_drift",
    "jacobi_ten_return_span",
    "phase_return_error",
    "condition_number",
    "raw_condition_number",
    "gate_1_residual",
    "gate_2_jacobi",
    "gate_3_phase",
    "gate_5_target_amplitude",
    "gate_6_mapping_time",
    "gate_7_condition",
    "failed_gates",
    "failure_reason",
    "newton_iterations",
    "max_correction_norm",
)


@dataclass(frozen=True)
class ProjectionSource:
    archive: str
    case_id: str
    index: int
    states: np.ndarray
    phases: np.ndarray
    mapping_time_days: float
    rho: float
    mean_jacobi: float
    max_abs_z_km: float


def _fmt(value: Any) -> str:
    return campaign._fmt(value)


def _write_header(path: Path, fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        csv.DictWriter(stream, fieldnames=fields).writeheader()


def _append_row(path: Path, fields: tuple[str, ...], row: dict[str, Any]) -> None:
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writerow({field: _fmt(row.get(field)) for field in fields})
        stream.flush()


def _sources_from_archive(path: Path, archive_name: str, min_source_z_km: float) -> list[ProjectionSource]:
    if not path.exists():
        return []
    sources: list[ProjectionSource] = []
    with np.load(path, allow_pickle=True) as data:
        phases = np.asarray(data["phase_grid"], dtype=float)
        accepted = np.asarray(data["accepted"], dtype=bool) if "accepted" in data else np.ones(data["states"].shape[0], dtype=bool)
        for index in range(data["states"].shape[0]):
            if not bool(accepted[index]):
                continue
            max_z = float(data["max_abs_z_km"][index])
            if max_z < min_source_z_km:
                continue
            sources.append(
                ProjectionSource(
                    archive=archive_name,
                    case_id=str(data["case_ids"][index]),
                    index=index,
                    states=np.asarray(data["states"][index], dtype=float),
                    phases=phases,
                    mapping_time_days=float(data["mapping_time_days"][index]),
                    rho=float(data["rho"][index]),
                    mean_jacobi=float(data["mean_jacobi"][index]),
                    max_abs_z_km=max_z,
                )
            )
    return sources


def _load_sources(min_source_z_km: float, max_candidates: int) -> list[ProjectionSource]:
    sources = []
    sources.extend(_sources_from_archive(FREE_TIME_STATE_PATH, "free_time_branch", min_source_z_km))
    sources.extend(_sources_from_archive(PARAMETER_AWARE_STATE_PATH, "parameter_aware_forward", min_source_z_km))
    sources.sort(key=lambda item: item.max_abs_z_km, reverse=True)
    return sources[:max_candidates]


def _projection_row(source: ProjectionSource, attempt_id: str) -> dict[str, Any]:
    predictor = campaign.fixed_time._fixed_unknown_vector(
        source.states,
        source.rho,
        source.mean_jacobi,
    )
    (
        assembly,
        correction_norms,
        converged,
        solver_failure,
        condition,
        raw_condition,
    ) = campaign._solve_fixed_time_target_amplitude(
        case_id=attempt_id,
        predictor=predictor,
        target_max_abs_z_km=source.max_abs_z_km,
        phases=source.phases,
        reference_states=source.states,
    )
    validation = campaign.fixed_time._validation_for(assembly)
    map_residual = float(np.max(assembly.map_residual_norms))
    jacobi_span = float(np.ptp(assembly.jacobi_values))
    one_map_drift = campaign._float_from_validation(validation, "one_map_sweep_jacobi_drift")
    ten_return = campaign._float_from_validation(validation, "ten_return_jacobi_span")
    phase_return = campaign._float_from_validation(validation, "one_map_phase_return_error")
    amplitude_error = assembly.max_abs_z_km - source.max_abs_z_km
    gates = {
        "gate_1_residual": converged and map_residual < campaign.GATE_1_MAP_RESIDUAL,
        "gate_2_jacobi": (
            converged
            and jacobi_span < campaign.GATE_2_CURVE_JACOBI_SPAN
            and one_map_drift is not None
            and one_map_drift < campaign.GATE_2_ONE_MAP_JACOBI_DRIFT
            and ten_return is not None
            and ten_return < campaign.GATE_2_TEN_RETURN_JACOBI
        ),
        "gate_3_phase": converged and phase_return is not None and phase_return < campaign.GATE_3_PHASE_RETURN,
        "gate_5_target_amplitude": abs(amplitude_error) < campaign.AMPLITUDE_TARGET_TOL_KM,
        "gate_6_mapping_time": abs(campaign.T_FIXED_DAYS - campaign.fixed_time.T_FIXED_DAYS) < campaign.GATE_6_MAPPING_TIME_DAYS,
        "gate_7_condition": condition < campaign.GATE_7_SCALED_CONDITION,
    }
    failed = tuple(name for name, passed in gates.items() if not passed)
    accepted = converged and not failed and assembly.max_abs_z_km >= TARGET_MIN_KM
    return {
        "attempt_id": attempt_id,
        "source_archive": source.archive,
        "source_case_id": source.case_id,
        "source_index": source.index,
        "source_mapping_time_days": source.mapping_time_days,
        "source_max_abs_z_km": source.max_abs_z_km,
        "source_rho_rad": source.rho,
        "source_mean_jacobi": source.mean_jacobi,
        "target_max_abs_z_km": source.max_abs_z_km,
        "projected_max_abs_z_km": assembly.max_abs_z_km,
        "amplitude_error_km": amplitude_error,
        "projected_rho_rad": assembly.rho,
        "projected_mean_jacobi": campaign.fixed_time._mean_jacobi(assembly.states),
        "converged": converged,
        "projection_acceptance": accepted,
        "passed_10500_gate": assembly.max_abs_z_km >= TARGET_MIN_KM,
        "passed_11000_gate": assembly.max_abs_z_km >= TARGET_STRETCH_KM,
        "map_residual_max": map_residual,
        "jacobi_mean_span": jacobi_span,
        "jacobi_one_map_drift": one_map_drift,
        "jacobi_ten_return_span": ten_return,
        "phase_return_error": phase_return,
        "condition_number": condition,
        "raw_condition_number": raw_condition,
        **gates,
        "failed_gates": "; ".join(failed),
        "failure_reason": solver_failure if solver_failure else "; ".join(failed),
        "newton_iterations": len(correction_norms),
        "max_correction_norm": max(correction_norms) if correction_norms else 0.0,
    }


def _write_doc(rows: list[dict[str, Any]], *, min_source_z_km: float, max_candidates: int) -> None:
    accepted = [row for row in rows if bool(row["projection_acceptance"])]
    best_attempt = max(rows, key=lambda row: float(row["projected_max_abs_z_km"])) if rows else None
    row_lines = "\n".join(
        f"- `{row['attempt_id']}` from `{row['source_case_id']}`: source "
        f"`{float(row['source_max_abs_z_km']):.12g}` km -> projected "
        f"`{float(row['projected_max_abs_z_km']):.12g}` km, accepted "
        f"`{row['projection_acceptance']}`, failed `{row['failed_gates']}`"
        for row in rows
    ) or "- none"
    DOC_OUTPUT.write_text(
        f"""# Chapter 3 Free-Time To Fixed-Time Projection Audit

## Scope

This audit starts from accepted high-amplitude free-time quasi-DRO states and
tries to project them to the McCarthy fixed mapping time while preserving the
source max-|z| amplitude through an explicit target-amplitude row.

It is diagnostic only and does not update Fig. 3.16 / Fig. 3.17.

## Configuration

- Minimum source amplitude: `{min_source_z_km}` km
- Max candidates: `{max_candidates}`
- Fixed mapping time: `{campaign.T_FIXED_DAYS}` days
- Minimum target: `{TARGET_MIN_KM}` km

## Outcome

- Rows evaluated: `{len(rows)}`
- Accepted fixed-time projections above 10,500 km: `{len(accepted)}`
- Best projected max abs z: `{best_attempt['projected_max_abs_z_km'] if best_attempt else 'N/A'}` km

## Rows

{row_lines}

## Interpretation

An accepted row would be a candidate for independent branch continuation and
figure-source review. Rejected rows show that high-amplitude free-time states do
not survive this fixed-time target-amplitude projection under the current
corrector and audit gates.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-source-z-km", type=float, default=10500.0)
    parser.add_argument("--max-candidates", type=int, default=4)
    args = parser.parse_args()
    if args.max_candidates <= 0:
        raise SystemExit("--max-candidates must be positive")

    _write_header(OUTPUT, FIELDS)
    sources = _load_sources(args.min_source_z_km, args.max_candidates)
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        attempt_id = f"free_time_fixed_T_projection_{index:02d}"
        print(
            f"{attempt_id}: source={source.case_id}, source_z={source.max_abs_z_km:.6f} km",
            flush=True,
        )
        row = _projection_row(source, attempt_id)
        _append_row(OUTPUT, FIELDS, row)
        rows.append(row)
        print(
            f"{attempt_id}: accepted={row['projection_acceptance']} "
            f"projected_z={float(row['projected_max_abs_z_km']):.6f} "
            f"failed={row['failed_gates']}",
            flush=True,
        )

    _write_doc(rows, min_source_z_km=args.min_source_z_km, max_candidates=args.max_candidates)
    print(f"wrote {OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(
        "free-time fixed-time projection audit: "
        f"rows={len(rows)}, "
        f"accepted={sum(bool(row['projection_acceptance']) for row in rows)}",
        flush=True,
    )


if __name__ == "__main__":
    main()
