"""Independently re-integrate the four Route H fixed-time target curves."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import integrate_cr3bp, jacobi_constant
from qp_orbits.quasi_torus import _trigonometric_interpolation_matrix


DATA = PROJECT_ROOT / "data" / "computed"
STATE_PATH = DATA / "chapter3_route_h_fixed_time_target_states.csv"
CSV_PATH = DATA / "chapter3_route_h_target_state_revalidation.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_target_state_revalidation.md"
FIELDS = (
    "target_jacobi",
    "curve_samples",
    "mapping_time_days",
    "rotation_angle_rad",
    "mean_initial_jacobi",
    "target_jacobi_error",
    "initial_jacobi_span",
    "max_endpoint_map_residual",
    "max_endpoint_jacobi_drift",
    "mean_endpoint_jacobi_drift",
    "status",
)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def build_rows() -> list[dict[str, object]]:
    source = _read(STATE_PATH)
    grouped: dict[float, list[dict[str, str]]] = {}
    for row in source:
        grouped.setdefault(float(row["target_jacobi"]), []).append(row)
    system = SYSTEMS["earth_moon"]
    results: list[dict[str, object]] = []
    for target in sorted(grouped, reverse=True):
        rows = sorted(grouped[target], key=lambda row: int(row["phase_index"]))
        phases = np.asarray([float(row["phase_rad"]) for row in rows])
        states = np.asarray(
            [
                [float(row[field]) for field in ("x", "y", "z", "xdot", "ydot", "zdot")]
                for row in rows
            ]
        )
        mapping_days = float(rows[0]["mapping_time_days"])
        mapping_time = mapping_days / system.time_unit_days
        rotation = float(rows[0]["rotation_angle_rad"])
        mapped = np.empty_like(states)
        for index, state in enumerate(states):
            solution = integrate_cr3bp(
                state,
                (0.0, mapping_time),
                system.mu,
                t_eval=np.array([mapping_time]),
                rtol=2.0e-11,
                atol=2.0e-13,
                max_step=5.0e-3,
            )
            if not solution.success or solution.y.shape[1] != 1:
                raise RuntimeError(f"independent integration failed at JC={target}, node={index}")
            mapped[index] = solution.y[:, -1]
        interpolation = _trigonometric_interpolation_matrix(phases, phases + rotation)
        expected = interpolation @ states
        residual = float(np.max(np.linalg.norm(mapped - expected, axis=1)))
        initial_jacobi = jacobi_constant(states, system.mu)
        endpoint_jacobi = jacobi_constant(mapped, system.mu)
        drift = np.abs(endpoint_jacobi - initial_jacobi)
        target_error = abs(float(np.mean(initial_jacobi)) - target)
        span = float(np.ptp(initial_jacobi))
        status = bool(
            residual < 2.0e-9
            and float(np.max(drift)) < 1.0e-9
            and span < 2.0e-8
            and target_error < 5.0e-5
        )
        results.append(
            {
                "target_jacobi": target,
                "curve_samples": states.shape[0],
                "mapping_time_days": mapping_days,
                "rotation_angle_rad": rotation,
                "mean_initial_jacobi": float(np.mean(initial_jacobi)),
                "target_jacobi_error": target_error,
                "initial_jacobi_span": span,
                "max_endpoint_map_residual": residual,
                "max_endpoint_jacobi_drift": float(np.max(drift)),
                "mean_endpoint_jacobi_drift": float(np.mean(drift)),
                "status": "pass" if status else "fail",
            }
        )
    return results


def _write(rows: list[dict[str, object]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    passed = sum(row["status"] == "pass" for row in rows)
    DOC_PATH.write_text(
        f"""# Chapter 3 Route H Target-State Independent Revalidation

## Result

- Passed targets: `{passed}/4`
- Total independently propagated curve nodes: `{sum(int(row['curve_samples']) for row in rows)}`
- Worst endpoint map residual: `{max(float(row['max_endpoint_map_residual']) for row in rows):.6e}`
- Worst endpoint Jacobi drift: `{max(float(row['max_endpoint_jacobi_drift']) for row in rows):.6e}`
- Worst initial curve Jacobi span: `{max(float(row['initial_jacobi_span']) for row in rows):.6e}`

## Method

Every stored curve node is re-integrated for one mapping time with `rtol=2e-11`,
`atol=2e-13`, and `max_step=5e-3`. The endpoint is compared with an independently
constructed trigonometric rotation target. This audit does not read cached mapped
states or accept the Newton solver's own residual history.

The paper-precision target tolerance remains `5e-5` in Jacobi; numerical endpoint
map and Jacobi-drift gates are `2e-9` and `1e-9`, respectively.
""",
        encoding="utf-8",
    )


def main() -> int:
    rows = build_rows()
    _write(rows)
    passed = sum(row["status"] == "pass" for row in rows)
    print(f"Route H target-state revalidation: pass={passed}/4")
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0 if passed == 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
