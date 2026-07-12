"""Project a free-time Route H Jacobi target back to the thesis mapping time."""

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
    _jacobi_gradient,
    _stroboscopic_map_and_stms,
    _trigonometric_interpolation_derivative_matrix,
    _trigonometric_interpolation_matrix,
    stroboscopic_curve_fixed_jacobi_free_time_rotation_correction,
)


DEFAULT_CACHE = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
FIELDS = (
    "step",
    "mapping_time_days",
    "mapping_time_error_days",
    "rotation_angle_rad",
    "mean_jacobi",
    "energy_residual",
    "curve_jacobi_span",
    "max_map_residual",
    "phase_residual",
    "amplitude",
    "newton_iterations",
    "jacobian_condition",
    "status",
)


def _amplitude(states: np.ndarray, seed: object) -> float:
    component = seed.mode_component
    displacement = states[:, component] - seed.orbit_state[component]
    return float(np.sqrt(2.0 * np.mean(displacement**2)))


def _correct_fixed_time_energy(
    *,
    seed: object,
    states: np.ndarray,
    rotation: float,
    reference: np.ndarray,
    mapping_time: float,
    target_jacobi: float,
    max_iterations: int,
) -> tuple[np.ndarray, float, dict[str, float]]:
    states = np.array(states, dtype=float, copy=True)
    rotation = float(rotation)
    phase_direction = np.roll(reference, -1, axis=0) - np.roll(reference, 1, axis=0)
    phase_direction /= np.linalg.norm(phase_direction)
    sample_count = states.shape[0]
    state_size = states.size
    best_states = states.copy()
    best_rotation = rotation
    best_metric = float("inf")
    best_metrics: dict[str, float] = {}

    for iteration in range(max_iterations + 1):
        interpolation = _trigonometric_interpolation_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        interpolation_derivative = _trigonometric_interpolation_derivative_matrix(
            seed.phases,
            seed.phases + rotation,
        )
        mapped, stms = _stroboscopic_map_and_stms(
            states,
            period=mapping_time,
            mu=seed.mu,
            max_step=0.01,
        )
        residuals = mapped - interpolation @ states
        residual_norm = float(np.max(np.linalg.norm(residuals, axis=1)))
        jacobi = jacobi_constant(states, seed.mu)
        energy_residuals = jacobi - target_jacobi
        energy_residual = float(np.max(np.abs(energy_residuals)))
        jacobi_span = float(np.ptp(jacobi))
        phase_residual = float(np.sum((states - reference) * phase_direction))
        metric = max(residual_norm, abs(energy_residual), abs(phase_residual))
        if metric < best_metric:
            best_metric = metric
            best_states = states.copy()
            best_rotation = rotation
            best_metrics = {
                "energy_residual": energy_residual,
                "curve_jacobi_span": jacobi_span,
                "max_map_residual": residual_norm,
                "phase_residual": phase_residual,
                "newton_iterations": float(iteration),
                "jacobian_condition": float("nan"),
            }
        if (
            residual_norm < 1.0e-9
            and abs(energy_residual) < 5.0e-10
            and jacobi_span < 2.0e-8
            and abs(phase_residual) < 1.0e-10
        ):
            return states, rotation, best_metrics
        if iteration == max_iterations:
            break

        jacobian = np.zeros(
            (state_size + sample_count + 1, state_size + 1),
            dtype=float,
        )
        for row in range(sample_count):
            for col in range(sample_count):
                block = -interpolation[row, col] * np.eye(6)
                if row == col:
                    block += stms[row]
                jacobian[6 * row : 6 * row + 6, 6 * col : 6 * col + 6] = block
        jacobian[:state_size, -1] = -(
            interpolation_derivative @ states
        ).reshape(-1)
        energy_gradients = _jacobi_gradient(states, seed.mu)
        for row in range(sample_count):
            jacobian[state_size + row, 6 * row : 6 * row + 6] = energy_gradients[row]
        jacobian[state_size + sample_count, :state_size] = phase_direction.reshape(-1)
        right_hand_side = -np.concatenate(
            [residuals.reshape(-1), energy_residuals, np.array([phase_residual])]
        )
        delta, _, _, singular_values = np.linalg.lstsq(
            jacobian,
            right_hand_side,
            rcond=1.0e-11,
        )
        condition = (
            float(singular_values[0] / singular_values[-1])
            if singular_values.size and singular_values[-1] > 0.0
            else float("inf")
        )
        state_delta = delta[:state_size].reshape(sample_count, 6)
        rotation_delta = float(delta[-1])
        scale = 1.0
        max_node_step = float(np.max(np.linalg.norm(state_delta, axis=1)))
        if max_node_step > 2.0e-3:
            scale = min(scale, 2.0e-3 / max_node_step)
        if abs(rotation_delta) > 1.0e-2:
            scale = min(scale, 1.0e-2 / abs(rotation_delta))
        states += scale * state_delta
        rotation = float((rotation + scale * rotation_delta) % (2.0 * np.pi))
        if metric <= best_metric:
            best_metrics["jacobian_condition"] = condition

    return best_states, best_rotation, best_metrics


def _row(
    *,
    step: int,
    mapping_time: float,
    target_time: float,
    rotation: float,
    states: np.ndarray,
    seed: object,
    metrics: dict[str, float],
) -> dict[str, object]:
    time_days = mapping_time * SYSTEMS["earth_moon"].time_unit_days
    target_days = target_time * SYSTEMS["earth_moon"].time_unit_days
    jacobi = jacobi_constant(states, seed.mu)
    status = bool(
        metrics["max_map_residual"] < 1.0e-9
        and abs(metrics["energy_residual"]) < 5.0e-10
        and metrics["curve_jacobi_span"] < 2.0e-8
        and abs(metrics["phase_residual"]) < 1.0e-10
    )
    return {
        "step": step,
        "mapping_time_days": time_days,
        "mapping_time_error_days": time_days - target_days,
        "rotation_angle_rad": rotation,
        "mean_jacobi": float(np.mean(jacobi)),
        **metrics,
        "amplitude": _amplitude(states, seed),
        "status": "pass" if status else "fail",
    }


def _write_doc(
    path: Path,
    rows: list[dict[str, object]],
    target_jacobi: float,
    failure: str,
) -> None:
    final = rows[-1]
    reached_time = abs(float(final["mapping_time_error_days"])) < 1.0e-10
    status = "pass" if reached_time and final["status"] == "pass" and not failure else "fail"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `{status}`
- Target Jacobi: `{target_jacobi:.7f}`
- Accepted homotopy steps: `{sum(row['status'] == 'pass' for row in rows)}/{len(rows)}`
- Final mapping time: `{float(final['mapping_time_days']):.16g} day`
- Mapping-time error: `{float(final['mapping_time_error_days']):.6e} day`
- Final mean Jacobi: `{float(final['mean_jacobi']):.16g}`
- Final map residual: `{float(final['max_map_residual']):.6e}`
- Final Jacobi span: `{float(final['curve_jacobi_span']):.6e}`
- Failure: `{failure or 'N/A'}`

## Interpretation

The initial state is a strict fixed-Jacobi solution with free mapping time. The
homotopy then moves mapping time toward the thesis fixed-time value while each STM
Newton correction simultaneously enforces map invariance, mean Jacobi, and phase.
Passing requires reaching the target time without relaxing the registered numerical
gates. The exploratory pointwise-Jacobi-span threshold is the Route H generator's
`2e-8`; promotion still requires spectral refinement below `1e-9`. This is a
projection probe for one Jacobi anchor, not yet the complete four-
anchor cold-start family.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--target-jacobi", type=float, default=2.9212)
    parser.add_argument("--initial-time-step-days", type=float, default=5.0e-3)
    parser.add_argument("--minimum-time-step-days", type=float, default=1.0e-5)
    parser.add_argument("--max-steps", type=int, default=120)
    parser.add_argument("--max-iterations", type=int, default=12)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--doc", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_token = f"{args.target_jacobi:.4f}".replace(".", "p")
    csv_path = args.csv or (
        PROJECT_ROOT
        / "data"
        / "computed"
        / f"chapter3_route_h_fixed_time_energy_projection_{target_token}.csv"
    )
    doc_path = args.doc or (
        PROJECT_ROOT
        / "docs"
        / f"chapter3_route_h_fixed_time_energy_projection_{target_token}.md"
    )
    with args.cache.open("rb") as stream:
        fold = tuple(pickle.load(stream))[-1]
    targets = [value for value in (2.9225, 2.9221, 2.9215, 2.9212) if value >= args.target_jacobi]
    states = fold.corrected_states
    mapping_time = fold.seed.orbit_period
    rotation = fold.rotation_angle_rad
    free = None
    for target in targets:
        free = stroboscopic_curve_fixed_jacobi_free_time_rotation_correction(
            fold.seed,
            target_jacobi=target,
            initial_states=states,
            initial_mapping_time=mapping_time,
            initial_rotation_angle_rad=rotation,
            phase_reference_states=states,
            max_iterations=48,
            tolerance=1.0e-10,
            jacobi_tolerance=1.0e-10,
            phase_tolerance=1.0e-10,
            max_step=0.01,
            max_state_step=2.0e-3,
            max_mapping_time_step=0.05,
            max_rotation_step=0.01,
        )
        states = free.corrected_states
        mapping_time = free.mapping_time
        rotation = free.rotation_angle_rad
    if free is None:
        raise RuntimeError("target Jacobi is outside the configured bridge sequence")

    target_time = fold.seed.orbit_period
    system = SYSTEMS["earth_moon"]
    step = np.sign(target_time - mapping_time) * (
        args.initial_time_step_days / system.time_unit_days
    )
    rows: list[dict[str, object]] = []
    initial_metrics = {
        "energy_residual": float(free.energy_residual_history[-1]),
        "curve_jacobi_span": float(
            np.ptp(jacobi_constant(states, fold.seed.mu))
        ),
        "max_map_residual": float(np.max(free.final_residual_norms)),
        "phase_residual": float(free.phase_residual_history[-1]),
        "newton_iterations": 0.0,
        "jacobian_condition": float("nan"),
    }
    rows.append(
        _row(
            step=0,
            mapping_time=mapping_time,
            target_time=target_time,
            rotation=rotation,
            states=states,
            seed=fold.seed,
            metrics=initial_metrics,
        )
    )
    failure = ""
    accepted_steps = 0
    while abs(mapping_time - target_time) > 1.0e-13 and accepted_steps < args.max_steps:
        proposed = mapping_time + step
        if (target_time - mapping_time) * (target_time - proposed) <= 0.0:
            proposed = target_time
        candidate_states, candidate_rotation, metrics = _correct_fixed_time_energy(
            seed=fold.seed,
            states=states,
            rotation=rotation,
            reference=states,
            mapping_time=proposed,
            target_jacobi=args.target_jacobi,
            max_iterations=args.max_iterations,
        )
        candidate_row = _row(
            step=accepted_steps + 1,
            mapping_time=proposed,
            target_time=target_time,
            rotation=candidate_rotation,
            states=candidate_states,
            seed=fold.seed,
            metrics=metrics,
        )
        if candidate_row["status"] != "pass":
            print(
                f"retry time={proposed * system.time_unit_days:.9f} day, "
                f"step={step * system.time_unit_days:.3e} day, "
                f"residual={float(candidate_row['max_map_residual']):.3e}, "
                f"energy={float(candidate_row['energy_residual']):.3e}",
                flush=True,
            )
            step *= 0.5
            if abs(step) * system.time_unit_days < args.minimum_time_step_days:
                failure = "fixed-time energy correction exhausted the minimum time step"
                rows.append(candidate_row)
                break
            continue
        rows.append(candidate_row)
        states = candidate_states
        rotation = candidate_rotation
        mapping_time = proposed
        accepted_steps += 1
        print(
            f"accept step={accepted_steps}, time={mapping_time * system.time_unit_days:.9f} day, "
            f"rho={rotation:.9f}, residual={float(candidate_row['max_map_residual']):.3e}",
            flush=True,
        )
        step *= 1.25
    if accepted_steps >= args.max_steps and abs(mapping_time - target_time) > 1.0e-13:
        failure = "homotopy exhausted max-steps before reaching the target mapping time"

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    _write_doc(doc_path, rows, args.target_jacobi, failure)
    print(
        f"Route H fixed-time energy projection: rows={len(rows)}, "
        f"final_time_error_days={float(rows[-1]['mapping_time_error_days']):.3e}, "
        f"status={rows[-1]['status']}"
    )
    print(f"wrote {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"wrote {doc_path.relative_to(PROJECT_ROOT)}")
    reached = abs(float(rows[-1]["mapping_time_error_days"])) < 1.0e-10
    return 0 if reached and rows[-1]["status"] == "pass" and not failure else 1


if __name__ == "__main__":
    raise SystemExit(main())
