"""Test Jacobi descent directions from nullspace-switched Route H roots."""

from __future__ import annotations

import argparse
import csv
import pickle
from pathlib import Path

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import stroboscopic_curve_fixed_rotation_correction
from run_chapter3_route_h_nullspace_branch_switch_probe import (
    _amplitude,
    _assemble_fixed_rotation_jacobian,
)


DEFAULT_CACHE = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
CSV_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_switched_branch_direction_probe.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_switched_branch_direction_probe.md"
FIELDS = (
    "branch_id",
    "null_sign",
    "rho_step",
    "source_rotation_angle_rad",
    "target_rotation_angle_rad",
    "source_mean_jacobi",
    "candidate_mean_jacobi",
    "delta_mean_jacobi",
    "jacobi_slope_per_rho",
    "source_amplitude",
    "candidate_amplitude",
    "delta_amplitude",
    "max_map_residual",
    "curve_jacobi_span",
    "phase_residual",
    "accepted_correction",
    "jacobi_descent",
)


def _mean_jacobi(member: object) -> float:
    return float(
        np.mean(jacobi_constant(member.corrected_states, SYSTEMS["earth_moon"].mu))
    )


def _correct(
    source: object,
    *,
    target_rho: float,
    initial_states: np.ndarray,
    max_iterations: int,
) -> object:
    return stroboscopic_curve_fixed_rotation_correction(
        source.seed,
        target_rotation_angle_rad=target_rho,
        initial_states=initial_states,
        phase_reference_states=initial_states,
        max_iterations=max_iterations,
        tolerance=1.0e-10,
        phase_tolerance=1.0e-10,
        max_step=0.01,
        max_state_step=2.0e-3,
    )


def _accepted(member: object) -> bool:
    mu = SYSTEMS["earth_moon"].mu
    return bool(
        float(np.max(member.final_residual_norms)) < 1.0e-9
        and float(np.ptp(jacobi_constant(member.corrected_states, mu))) < 1.0e-9
        and abs(float(member.phase_residual_history[-1])) < 1.0e-10
    )


def _write_doc(rows: list[dict[str, object]], singular_values: np.ndarray) -> None:
    accepted = [row for row in rows if row["accepted_correction"]]
    descent = [row for row in rows if row["jacobi_descent"]]
    best = min(descent, key=lambda row: float(row["delta_mean_jacobi"])) if descent else None
    status = "pass" if descent else "bounded_no_descent_direction"
    best_text = (
        f"`{best['branch_id']}`, delta-rho `{float(best['rho_step']):.3e}`, "
        f"delta-JC `{float(best['delta_mean_jacobi']):.3e}`"
        if best is not None
        else "N/A"
    )
    DOC_PATH.write_text(
        f"""# Chapter 3 Route H Switched-Branch Direction Probe

## Result

- Status: `{status}`
- Fold smallest singular value: `{singular_values[-1]:.6e}`
- Fold spectral gap: `{singular_values[-2] / singular_values[-1]:.6e}`
- Accepted direction probes: `{len(accepted)}/{len(rows)}`
- Accepted Jacobi-descent probes: `{len(descent)}`
- Best local descent: {best_text}

## Interpretation

Two corrected roots are initialized on opposite sides of the strongly separated
fold null direction. Each root is then corrected at positive and negative rotation-
number offsets. A descent direction must pass the strict map, phase, and pointwise-
Jacobi gates and lower mean Jacobi by more than `1e-10`; smaller changes are treated
as fold-level numerical ambiguity.

A passing row identifies a local branch direction worth continuing, but it does not
yet prove coverage of the four Fig. 3.16 Jacobi anchors. That requires a persistent,
checkpointed continuation with target insertion and independent revalidation.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--member-index", type=int, default=-1)
    parser.add_argument("--null-perturbation", type=float, default=5.0e-3)
    parser.add_argument("--rho-steps", default="1e-6,1e-5")
    parser.add_argument("--max-iterations", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rho_steps = tuple(float(value) for value in args.rho_steps.split(","))
    if (
        args.null_perturbation <= 0.0
        or not rho_steps
        or any(value <= 0.0 for value in rho_steps)
        or args.max_iterations < 1
    ):
        raise ValueError("null perturbation and rho steps must be positive")
    with args.cache.open("rb") as stream:
        family = tuple(pickle.load(stream))
    fold = family[args.member_index]
    singular_values, null_direction = _assemble_fixed_rotation_jacobian(fold)
    null_direction /= float(np.max(np.linalg.norm(null_direction, axis=1)))

    rows: list[dict[str, object]] = []
    for null_sign in (-1.0, 1.0):
        branch = _correct(
            fold,
            target_rho=fold.rotation_angle_rad,
            initial_states=(
                fold.corrected_states
                + null_sign * args.null_perturbation * null_direction
            ),
            max_iterations=args.max_iterations,
        )
        if not _accepted(branch):
            continue
        source_jacobi = _mean_jacobi(branch)
        source_amplitude = _amplitude(branch)
        branch_id = f"null_{int(null_sign):+d}_{args.null_perturbation:.1e}"
        for magnitude in rho_steps:
            for rho_sign in (-1.0, 1.0):
                rho_step = rho_sign * magnitude
                candidate = _correct(
                    branch,
                    target_rho=branch.rotation_angle_rad + rho_step,
                    initial_states=branch.corrected_states,
                    max_iterations=args.max_iterations,
                )
                candidate_jacobi = _mean_jacobi(candidate)
                accepted = _accepted(candidate)
                delta_jacobi = candidate_jacobi - source_jacobi
                rows.append(
                    {
                        "branch_id": branch_id,
                        "null_sign": int(null_sign),
                        "rho_step": rho_step,
                        "source_rotation_angle_rad": branch.rotation_angle_rad,
                        "target_rotation_angle_rad": candidate.rotation_angle_rad,
                        "source_mean_jacobi": source_jacobi,
                        "candidate_mean_jacobi": candidate_jacobi,
                        "delta_mean_jacobi": delta_jacobi,
                        "jacobi_slope_per_rho": delta_jacobi / rho_step,
                        "source_amplitude": source_amplitude,
                        "candidate_amplitude": _amplitude(candidate),
                        "delta_amplitude": _amplitude(candidate) - source_amplitude,
                        "max_map_residual": float(np.max(candidate.final_residual_norms)),
                        "curve_jacobi_span": float(
                            np.ptp(
                                jacobi_constant(
                                    candidate.corrected_states,
                                    SYSTEMS["earth_moon"].mu,
                                )
                            )
                        ),
                        "phase_residual": float(candidate.phase_residual_history[-1]),
                        "accepted_correction": accepted,
                        "jacobi_descent": accepted and delta_jacobi < -1.0e-10,
                    }
                )

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    _write_doc(rows, singular_values)
    descent = sum(bool(row["jacobi_descent"]) for row in rows)
    print(f"Route H switched-branch direction probe: rows={len(rows)}, descent={descent}")
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
