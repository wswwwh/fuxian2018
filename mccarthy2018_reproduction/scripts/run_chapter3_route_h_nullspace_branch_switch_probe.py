"""Probe Route H branch switching along the fold Jacobian null direction."""

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
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_matrix,
    stroboscopic_curve_fixed_rotation_correction,
)


DEFAULT_CACHE = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
SPECTRUM_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_fold_singular_spectrum.csv"
CANDIDATE_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_nullspace_branch_switch_probe.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_nullspace_branch_switch_probe.md"
SPECTRUM_FIELDS = ("rank_from_smallest", "singular_value", "ratio_to_smallest")
CANDIDATE_FIELDS = (
    "case_id",
    "sign",
    "perturbation_max_node_norm",
    "predictor_map_residual",
    "source_mean_jacobi",
    "candidate_mean_jacobi",
    "delta_mean_jacobi",
    "source_amplitude",
    "candidate_amplitude",
    "delta_amplitude",
    "solution_max_node_distance",
    "best_phase_shift_rad",
    "phase_aligned_max_node_distance",
    "max_map_residual",
    "curve_jacobi_span",
    "phase_residual",
    "accepted_correction",
    "distinct_root",
    "lower_jacobi_distinct_root",
)


def _assemble_fixed_rotation_jacobian(member: object) -> tuple[np.ndarray, np.ndarray]:
    states = member.corrected_states
    sample_count = states.shape[0]
    interpolation = _trigonometric_interpolation_matrix(
        member.seed.phases,
        member.seed.phases + member.rotation_angle_rad,
    )
    _, stms = _stroboscopic_map_and_stms(
        states,
        period=member.seed.orbit_period,
        mu=member.seed.mu,
        max_step=0.01,
    )
    state_size = states.size
    jacobian = np.zeros((state_size + 1, state_size), dtype=float)
    for row in range(sample_count):
        for col in range(sample_count):
            block = -interpolation[row, col] * np.eye(6)
            if row == col:
                block += stms[row]
            jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
    phase = np.roll(states, -1, axis=0) - np.roll(states, 1, axis=0)
    phase /= np.linalg.norm(phase)
    jacobian[-1, :] = phase.reshape(-1)
    _, singular_values, right_vectors = np.linalg.svd(jacobian, full_matrices=False)
    return singular_values, right_vectors[-1].reshape(states.shape)


def _amplitude(member: object) -> float:
    component = member.seed.mode_component
    displacement = member.corrected_states[:, component] - member.seed.orbit_state[component]
    return float(np.sqrt(2.0 * np.mean(displacement**2)))


def _predictor_residual(member: object, states: np.ndarray) -> float:
    interpolation = _trigonometric_interpolation_matrix(
        member.seed.phases,
        member.seed.phases + member.rotation_angle_rad,
    )
    mapped, _ = _stroboscopic_map_and_stms(
        states,
        period=member.seed.orbit_period,
        mu=member.seed.mu,
        max_step=0.01,
    )
    return float(np.max(np.linalg.norm(mapped - interpolation @ states, axis=1)))


def _phase_aligned_distance(source: object, candidate_states: np.ndarray) -> tuple[float, float]:
    # Use an odd, endpoint-inclusive grid so the exact zero shift is present.
    shifts = np.linspace(-np.pi, np.pi, 721, endpoint=True)
    distances: list[float] = []
    for shift in shifts:
        interpolation = _trigonometric_interpolation_matrix(
            source.seed.phases,
            source.seed.phases + float(shift),
        )
        shifted = interpolation @ source.corrected_states
        distances.append(
            float(np.max(np.linalg.norm(candidate_states - shifted, axis=1)))
        )
    index = int(np.argmin(distances))
    return float(shifts[index]), distances[index]


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(
    source: object,
    singular_values: np.ndarray,
    candidate_rows: list[dict[str, object]],
) -> None:
    accepted = [row for row in candidate_rows if row["accepted_correction"]]
    distinct = [row for row in candidate_rows if row["distinct_root"]]
    lower = [row for row in candidate_rows if row["lower_jacobi_distinct_root"]]
    spectral_gap = float(singular_values[-2] / singular_values[-1])
    status = "pass" if lower else "bounded_no_branch_switch"
    DOC_PATH.write_text(
        f"""# Chapter 3 Route H Nullspace Branch-Switch Probe

## Result

- Status: `{status}`
- Source member samples: `{source.corrected_states.shape[0]}`
- Source rotation angle: `{source.rotation_angle_rad:.16g}`
- Smallest singular value: `{singular_values[-1]:.6e}`
- Next singular value: `{singular_values[-2]:.6e}`
- Null-direction spectral gap: `{spectral_gap:.6e}`
- Accepted corrections: `{len(accepted)}/{len(candidate_rows)}`
- Distinct corrected roots: `{len(distinct)}`
- Distinct roots with lower Jacobi: `{len(lower)}`

## Interpretation

The fixed-rotation, phase-constrained Jacobian has one strongly separated smallest
right-singular direction. Positive and negative perturbations along that direction
are corrected back at the same rotation number. A candidate counts as a branch
switch only when it independently passes map, phase, and pointwise-Jacobi gates and
remains more than `1e-4` in phase-aligned maximum node distance from the source
root. A lower-Jacobi
distinct root is the prerequisite for a new continuation branch; merely returning
to the source root is recorded as negative evidence.

The probe is local and does not by itself satisfy the four Fig. 3.16 Jacobi targets.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--member-index", type=int, default=-1)
    parser.add_argument(
        "--perturbations",
        default="1e-5,1e-4,1e-3,5e-3",
        help="Comma-separated maximum per-node state perturbations.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    perturbations = tuple(float(value) for value in args.perturbations.split(","))
    if not perturbations or any(value <= 0.0 for value in perturbations):
        raise ValueError("perturbations must be positive")
    with args.cache.open("rb") as stream:
        family = tuple(pickle.load(stream))
    source = family[args.member_index]
    singular_values, null_direction = _assemble_fixed_rotation_jacobian(source)
    block_norms = np.linalg.norm(null_direction, axis=1)
    null_direction /= float(np.max(block_norms))

    spectrum_rows = [
        {
            "rank_from_smallest": rank,
            "singular_value": float(value),
            "ratio_to_smallest": float(value / singular_values[-1]),
        }
        for rank, value in enumerate(singular_values[::-1][:12], start=1)
    ]
    _write_csv(SPECTRUM_PATH, SPECTRUM_FIELDS, spectrum_rows)

    mu = SYSTEMS["earth_moon"].mu
    source_jacobi = float(np.mean(jacobi_constant(source.corrected_states, mu)))
    source_amplitude = _amplitude(source)
    candidate_rows: list[dict[str, object]] = []
    for perturbation in perturbations:
        for sign in (-1.0, 1.0):
            initial_states = source.corrected_states + sign * perturbation * null_direction
            predictor_residual = _predictor_residual(source, initial_states)
            candidate = stroboscopic_curve_fixed_rotation_correction(
                source.seed,
                target_rotation_angle_rad=source.rotation_angle_rad,
                initial_states=initial_states,
                phase_reference_states=initial_states,
                max_iterations=64,
                tolerance=1.0e-10,
                phase_tolerance=1.0e-10,
                max_step=0.01,
                max_state_step=2.0e-3,
            )
            candidate_jacobi = float(
                np.mean(jacobi_constant(candidate.corrected_states, mu))
            )
            residual = float(np.max(candidate.final_residual_norms))
            span = float(np.ptp(jacobi_constant(candidate.corrected_states, mu)))
            phase = float(candidate.phase_residual_history[-1])
            distance = float(
                np.max(
                    np.linalg.norm(
                        candidate.corrected_states - source.corrected_states,
                        axis=1,
                    )
                )
            )
            phase_shift, aligned_distance = _phase_aligned_distance(
                source,
                candidate.corrected_states,
            )
            accepted = bool(residual < 1.0e-9 and span < 1.0e-9 and abs(phase) < 1.0e-10)
            distinct = bool(accepted and aligned_distance > 1.0e-4)
            candidate_rows.append(
                {
                    "case_id": f"null_{sign:+.0f}_{perturbation:.1e}",
                    "sign": int(sign),
                    "perturbation_max_node_norm": perturbation,
                    "predictor_map_residual": predictor_residual,
                    "source_mean_jacobi": source_jacobi,
                    "candidate_mean_jacobi": candidate_jacobi,
                    "delta_mean_jacobi": candidate_jacobi - source_jacobi,
                    "source_amplitude": source_amplitude,
                    "candidate_amplitude": _amplitude(candidate),
                    "delta_amplitude": _amplitude(candidate) - source_amplitude,
                    "solution_max_node_distance": distance,
                    "best_phase_shift_rad": phase_shift,
                    "phase_aligned_max_node_distance": aligned_distance,
                    "max_map_residual": residual,
                    "curve_jacobi_span": span,
                    "phase_residual": phase,
                    "accepted_correction": accepted,
                    "distinct_root": distinct,
                    "lower_jacobi_distinct_root": distinct and candidate_jacobi < source_jacobi,
                }
            )

    _write_csv(CANDIDATE_PATH, CANDIDATE_FIELDS, candidate_rows)
    _write_doc(source, singular_values, candidate_rows)
    lower = sum(bool(row["lower_jacobi_distinct_root"]) for row in candidate_rows)
    print(
        f"Route H nullspace branch-switch probe: sigma_min={singular_values[-1]:.3e}, "
        f"gap={singular_values[-2] / singular_values[-1]:.3e}, lower_distinct={lower}"
    )
    print(f"wrote {SPECTRUM_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {CANDIDATE_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
