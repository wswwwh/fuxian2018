"""Resolve Figure 4.1 within the paper-reported Jacobi precision."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    _sweep_corrected_curve_correction,
    corrected_constant_energy_curve_family,
    stroboscopic_spatial_jacobi_seed,
)
from qp_orbits.torus_stability import corrected_curve_dg


ROOT = Path(__file__).resolve().parents[1]
PAPER_JACOBI = 3.044
PAPER_NU = 1.3837
COARSE_TARGETS = (3.0436, 3.0438, 3.0440, 3.0442, 3.0444)


def evaluate(target_jacobi: float):
    system = SYSTEMS["earth_moon"]
    seed = stroboscopic_spatial_jacobi_seed(
        system.mu,
        target_jacobi=target_jacobi,
        family_label="halo",
        point="L2",
        mode_component=1,
        mode_amplitude=1e-8,
        samples=25,
        curve_samples=120,
    )
    correction = corrected_constant_energy_curve_family(
        seed,
        target_jacobi=target_jacobi,
        mode_amplitudes=(1e-8,),
        max_iterations=24,
    )[0]
    dg = corrected_curve_dg(correction)
    magnitudes = np.sort(np.abs(dg.eigenvalues))[::-1]
    ring = magnitudes[:25]
    radius = float(np.median(ring))
    nu = 0.5 * (radius + 1.0 / radius)
    jacobi = jacobi_constant(correction.corrected_states, system.mu)
    row = {
        "target_jacobi": target_jacobi,
        "reported_jacobi_3dp": f"{target_jacobi:.3f}",
        "base_z0_nd": seed.base_orbit_amplitude,
        "base_orbit_jacobi": seed.orbit_jacobi,
        "spectral_samples": 25,
        "dg_dimension": dg.map_jacobian.shape[0],
        "mapping_time_nd": dg.mapping_time,
        "mapping_time_days": dg.mapping_time * (system.time_unit_days or 1.0),
        "rotation_angle_rad": dg.rotation_angle_rad,
        "frequency_ratio": 2.0 * np.pi / dg.rotation_angle_rad,
        "mean_jacobi": float(np.mean(jacobi)),
        "curve_jacobi_span": float(np.ptp(jacobi)),
        "curve_residual_norm": float(correction.final_residual_norms.max()),
        "determinant_error": abs(dg.determinant - 1.0),
        "unstable_ring_radius": radius,
        "unstable_ring_relative_span": float(np.ptp(ring) / radius),
        "stability_index": nu,
        "stability_index_error": nu - PAPER_NU,
    }
    row["acceptance"] = (
        "pass"
        if row["reported_jacobi_3dp"] == f"{PAPER_JACOBI:.3f}"
        and abs(float(row["stability_index_error"])) <= 5e-4
        and float(row["curve_residual_norm"]) <= 1e-8
        and float(row["curve_jacobi_span"]) <= 1e-8
        and float(row["unstable_ring_relative_span"]) <= 5e-3
        else "fail"
    )
    print(
        f"JC={target_jacobi:.9f} z0={seed.base_orbit_amplitude:.9f} "
        f"Ru={radius:.9f} nu={nu:.9f} residual={row['curve_residual_norm']:.3e}"
    )
    return row, correction, dg


def main() -> None:
    results = [evaluate(value) for value in COARSE_TARGETS]
    rows = [result[0] for result in results]
    ordered = sorted(rows, key=lambda row: float(row["target_jacobi"]))
    bracket = None
    for left, right in zip(ordered[:-1], ordered[1:]):
        if float(left["stability_index_error"]) * float(right["stability_index_error"]) <= 0.0:
            bracket = left, right
            break
    if bracket is None:
        raise RuntimeError("reported-precision scan did not bracket the paper stability index")
    left, right = bracket
    x0, x1 = float(left["target_jacobi"]), float(right["target_jacobi"])
    y0, y1 = float(left["stability_index_error"]), float(right["stability_index_error"])
    refined_target = x0 - y0 * (x1 - x0) / (y1 - y0)
    results.append(evaluate(refined_target))
    rows.append(results[-1][0])

    csv_path = ROOT / "data" / "computed" / "chapter4_fig41_reported_precision_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    best_result = min(results, key=lambda result: abs(float(result[0]["stability_index_error"])))
    best, correction, dg = best_result
    torus = _sweep_corrected_curve_correction(correction, time_samples=48, max_step=0.01)
    states_path = ROOT / "data" / "computed" / "chapter4_fig41_reported_precision_states.csv"
    with states_path.open("w", newline="", encoding="utf-8") as stream:
        fields = ["time_index", "curve_index", "time_nd", "x", "y", "z", "xdot", "ydot", "zdot", "jacobi"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for time_index, (time, state_slice) in enumerate(zip(torus.normalized_times, torus.states)):
            jacobi_slice = jacobi_constant(state_slice, correction.seed.mu)
            for curve_index, (state, value) in enumerate(zip(state_slice, jacobi_slice)):
                writer.writerow(dict(zip(fields, [time_index, curve_index, time, *state, value])))

    spectrum_path = ROOT / "data" / "computed" / "chapter4_fig41_reported_precision_spectrum.csv"
    magnitudes = np.abs(dg.eigenvalues)
    with spectrum_path.open("w", newline="", encoding="utf-8") as stream:
        fields = ["eigen_index", "real", "imag", "magnitude", "angle_rad", "classification"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for index, value in enumerate(dg.eigenvalues):
            magnitude = float(magnitudes[index])
            writer.writerow({
                "eigen_index": index,
                "real": float(np.real(value)),
                "imag": float(np.imag(value)),
                "magnitude": magnitude,
                "angle_rad": float(np.angle(value)),
                "classification": "unstable" if magnitude > 1.001 else "stable" if magnitude < 0.999 else "unit",
            })
    doc_path = ROOT / "docs" / "chapter4_fig41_reported_precision_audit.md"
    doc_path.write_text(
        f"""# Chapter 4 Figure 4.1 reported-precision audit

- Paper target: `JC={PAPER_JACOBI:.3f}`, `N=25`, `nu={PAPER_NU}`
- Refined internal Jacobi: `{best['target_jacobi']}`
- Refined Jacobi at paper precision: `{best['reported_jacobi_3dp']}`
- Unstable-ring radius: `{best['unstable_ring_radius']}`
- Stability index: `{best['stability_index']}`
- Stability-index error: `{best['stability_index_error']}`
- Curve residual: `{best['curve_residual_norm']}`
- Curve Jacobi span: `{best['curve_jacobi_span']}`
- DG determinant error: `{best['determinant_error']}`
- Unstable-ring relative span: `{best['unstable_ring_relative_span']}`
- Acceptance: `{best['acceptance']}`

The paper reports the Jacobi constant to three decimal places. This audit keeps
that reported-precision boundary explicit: it does not claim that the internal
target is exactly `3.044000...`. Acceptance requires the internally resolved
member to round to the paper value while independently satisfying the DG,
invariance, energy-span, and ring-reducibility gates.
""",
        encoding="utf-8",
    )
    print(csv_path)
    print(states_path)
    print(spectrum_path)
    print(doc_path)


if __name__ == "__main__":
    main()
