"""Probe Route H through the cold-start rotation-number fold with PALC."""

from __future__ import annotations

import argparse
import csv
import pickle
from pathlib import Path

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    _fixed_mapping_pseudo_arclength_geometry,
    stroboscopic_curve_fixed_mapping_pseudo_arclength_correction,
)


DEFAULT_CACHE = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
DEFAULT_CSV = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_fold_palc_probe.csv"
DEFAULT_DOC = PROJECT_ROOT / "docs" / "chapter3_route_h_fold_palc_probe.md"
FIELDS = (
    "member",
    "source",
    "samples",
    "step_size",
    "rotation_angle_rad",
    "delta_rotation",
    "mean_jacobi",
    "delta_jacobi",
    "amplitude",
    "max_map_residual",
    "jacobi_span",
    "phase_residual",
    "arclength_residual",
    "accepted",
)


def _metrics(member: object, previous: object | None, *, source: str, step_size: float) -> dict[str, object]:
    mu = SYSTEMS["earth_moon"].mu
    states = member.corrected_states
    mean_jacobi = float(np.mean(jacobi_constant(states, mu)))
    previous_jacobi = (
        float(np.mean(jacobi_constant(previous.corrected_states, mu)))
        if previous is not None
        else float("nan")
    )
    component = member.seed.mode_component
    displacement = states[:, component] - member.seed.orbit_state[component]
    amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    phase = getattr(member, "phase_residual_history", np.array([0.0]))
    arclength = getattr(member, "arclength_residual_history", np.array([0.0]))
    residual = float(np.max(member.final_residual_norms))
    span = float(np.ptp(jacobi_constant(states, mu)))
    delta_rotation = (
        float(member.rotation_angle_rad - previous.rotation_angle_rad)
        if previous is not None
        else float("nan")
    )
    delta_jacobi = mean_jacobi - previous_jacobi if previous is not None else float("nan")
    accepted = bool(
        residual < 1.0e-8
        and span < 2.0e-8
        and abs(float(phase[-1])) < 1.0e-10
        and abs(float(arclength[-1])) < 1.0e-10
        and (previous is None or delta_jacobi < 0.0)
    )
    return {
        "source": source,
        "samples": states.shape[0],
        "step_size": step_size,
        "rotation_angle_rad": float(member.rotation_angle_rad),
        "delta_rotation": delta_rotation,
        "mean_jacobi": mean_jacobi,
        "delta_jacobi": delta_jacobi,
        "amplitude": amplitude,
        "max_map_residual": residual,
        "jacobi_span": span,
        "phase_residual": float(phase[-1]),
        "arclength_residual": float(arclength[-1]),
        "accepted": accepted,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(path: Path, rows: list[dict[str, object]], failure: str) -> None:
    palc_rows = [row for row in rows if row["source"] == "palc"]
    accepted = [row for row in palc_rows if row["accepted"]]
    negative_rho = [row for row in accepted if float(row["delta_rotation"]) < 0.0]
    start_jc = float(rows[1]["mean_jacobi"])
    end_jc = float(rows[-1]["mean_jacobi"])
    status = "pass" if accepted and negative_rho and not failure else "fail"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Chapter 3 Route H Fold PALC Probe

## Result

- Status: `{status}`
- Accepted PALC steps: `{len(accepted)}/{len(palc_rows)}`
- Accepted negative-delta-rho steps: `{len(negative_rho)}`
- Mean Jacobi start / end: `{start_jc:.16g}` / `{end_jc:.16g}`
- Net Jacobi change: `{end_jc - start_jc:.6e}`
- Final rotation angle: `{float(rows[-1]['rotation_angle_rad']):.16g}`
- Final amplitude: `{float(rows[-1]['amplitude']):.16g}`
- Failure: `{failure or 'N/A'}`

## Interpretation

The fixed-rotation continuation stopped because it required monotonically increasing
rotation number. This probe keeps the ordered pseudo-arclength secant orientation.
A passing negative-`delta_rotation` row demonstrates that the branch crosses a
rotation-number fold while Jacobi continues to decrease and the invariant-curve,
phase, arclength, and pointwise-Jacobi audits remain within tolerance.

This is a bounded fold-crossing proof, not yet the full thesis-target cold start.
The next acceptance step is integrating this PALC fallback into the persistent
Route H generator and reaching all requested Jacobi targets from an empty cache.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--anchor-index",
        type=int,
        default=-1,
        help="Index of the current anchor; the preceding member is the previous anchor.",
    )
    parser.add_argument("--steps", type=int, default=16)
    parser.add_argument("--growth", type=float, default=1.5)
    parser.add_argument("--maximum-step", type=float, default=5.0e-2)
    parser.add_argument("--minimum-step", type=float, default=1.0e-5)
    parser.add_argument("--maximum-retries", type=int, default=8)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if (
        args.steps < 1
        or args.growth < 1.0
        or args.minimum_step <= 0.0
        or args.maximum_step < args.minimum_step
        or args.maximum_retries < 0
    ):
        raise ValueError("steps, growth, and maximum-step must define a positive bounded probe")
    with args.cache.open("rb") as stream:
        family = list(pickle.load(stream))
    current_index = args.anchor_index if args.anchor_index >= 0 else len(family) + args.anchor_index
    if current_index < 1 or current_index >= len(family):
        raise IndexError("anchor-index must select a member with a predecessor")
    if family[current_index - 1].corrected_states.shape != family[current_index].corrected_states.shape:
        raise RuntimeError("cold-start cache does not end in two compatible PALC anchors")

    previous, current = family[current_index - 1], family[current_index]
    rows = [
        {"member": 0, **_metrics(previous, None, source="anchor", step_size=0.0)},
        {"member": 1, **_metrics(current, previous, source="anchor", step_size=0.0)},
    ]
    step_size = min(
        _fixed_mapping_pseudo_arclength_geometry(previous, current)[-1],
        args.maximum_step,
    )
    failure = ""
    for index in range(args.steps):
        candidate = None
        last_error = ""
        for _ in range(args.maximum_retries + 1):
            try:
                candidate = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
                    previous,
                    current,
                    step_size=step_size,
                    max_iterations=32,
                    tolerance=1.0e-8,
                    constraint_tolerance=1.0e-10,
                    max_step=0.01,
                )
                candidate_metrics = _metrics(
                    candidate,
                    current,
                    source="palc",
                    step_size=step_size,
                )
                if candidate_metrics["accepted"]:
                    break
                candidate = None
                last_error = (
                    "candidate failed the residual, Jacobi-span, constraint, "
                    "or decreasing-Jacobi gate"
                )
                step_size *= 0.5
                if step_size < args.minimum_step:
                    break
            except Exception as error:
                last_error = f"{type(error).__name__}: {error}"
                step_size *= 0.5
                if step_size < args.minimum_step:
                    break
        if candidate is None:
            failure = last_error or "PALC retry budget exhausted"
            break
        row = {
            "member": index + 2,
            **_metrics(candidate, current, source="palc", step_size=step_size),
        }
        rows.append(row)
        previous, current = current, candidate
        step_size = min(step_size * args.growth, args.maximum_step)

    _write_csv(args.csv, rows)
    _write_doc(args.doc, rows, failure)
    accepted = sum(row["source"] == "palc" and bool(row["accepted"]) for row in rows)
    turns = sum(
        row["source"] == "palc" and bool(row["accepted"]) and float(row["delta_rotation"]) < 0.0
        for row in rows
    )
    print(f"Route H fold PALC probe: accepted={accepted}/{args.steps}, negative_delta_rho={turns}")
    print(f"wrote {args.csv.relative_to(PROJECT_ROOT)}")
    print(f"wrote {args.doc.relative_to(PROJECT_ROOT)}")
    return 0 if accepted == args.steps and turns > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
