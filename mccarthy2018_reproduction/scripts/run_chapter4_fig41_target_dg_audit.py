"""Audit the original Figure 4.1 L2 quasi-halo target and its DG spectrum."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import (
    corrected_l2_constant_frequency_halo_energy_corrections,
    stroboscopic_curve_fixed_frequency_energy_correction,
)
from qp_orbits.torus_stability import corrected_curve_dg


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"
TARGET_JACOBI = 3.044
TARGET_STABILITY = 1.3837
def main() -> None:
    system = SYSTEMS["earth_moon"]
    family = corrected_l2_constant_frequency_halo_energy_corrections(system.mu)
    reference = min(family, key=lambda item: abs(item.target_jacobi - 3.0426))
    correction = stroboscopic_curve_fixed_frequency_energy_correction(
        reference,
        target_jacobi=TARGET_JACOBI,
        tolerance=1.0e-7,
        energy_tolerance=5.0e-8,
    )
    dg = corrected_curve_dg(correction)
    states = correction.corrected_states
    jacobi = jacobi_constant(states, system.mu)
    max_multiplier = dg.max_multiplier
    inferred_radius = TARGET_STABILITY + np.sqrt(TARGET_STABILITY**2 - 1.0)
    rows = []
    magnitudes = np.abs(dg.eigenvalues)
    for index, value in enumerate(dg.eigenvalues):
        rows.append(
            {
                "eigen_index": index,
                "classification": (
                    "unstable" if magnitudes[index] > 1.0 + 1e-3
                    else "stable" if magnitudes[index] < 1.0 - 1e-3
                    else "unit"
                ),
                "real": float(np.real(value)),
                "imag": float(np.imag(value)),
                "magnitude": float(magnitudes[index]),
                "angle_rad": float(np.angle(value)),
                "target_jacobi": TARGET_JACOBI,
                "mean_jacobi": float(np.mean(jacobi)),
                "curve_jacobi_span": float(np.ptp(jacobi)),
                "curve_residual_norm": float(correction.final_residual_norms.max()),
                "spectral_samples": int(states.shape[0]),
                "dg_dimension": int(dg.map_jacobian.shape[0]),
                "mapping_time_days": float(dg.mapping_time * system.time_unit_days),
                "rotation_angle_rad": float(dg.rotation_angle_rad),
                "determinant": dg.determinant,
                "max_multiplier": max_multiplier,
                "stability_index": dg.stability_index,
                "paper_stability_index": TARGET_STABILITY,
                "stability_index_error": dg.stability_index - TARGET_STABILITY,
                "paper_implied_unstable_radius": float(inferred_radius),
            }
        )

    csv_path = DATA / "chapter4_fig41_target_dg_audit.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    status = "pass" if abs(dg.stability_index - TARGET_STABILITY) <= 5e-4 else "fail"
    doc_path = DOCS / "chapter4_fig41_target_dg_audit.md"
    doc_path.write_text(
        f"""# Chapter 4 Figure 4.1 target DG audit

## Target

- Earth-Moon L2 fixed-frequency quasi-halo
- Jacobi constant: `{TARGET_JACOBI}`
- Paper discretization label: `N=25`
- Paper stability index: `nu={TARGET_STABILITY}`

## Direct numerical result

- acceptance: `{status}`
- corrected curve samples: `{states.shape[0]}`
- DG dimension: `{dg.map_jacobian.shape[0]}`
- mean Jacobi constant: `{np.mean(jacobi):.16g}`
- curve Jacobi span: `{np.ptp(jacobi):.6e}`
- map residual: `{correction.final_residual_norms.max():.6e}`
- determinant error: `{abs(dg.determinant - 1.0):.6e}`
- maximum multiplier magnitude: `{max_multiplier:.16g}`
- computed stability index: `{dg.stability_index:.16g}`
- stability-index error: `{dg.stability_index - TARGET_STABILITY:.6e}`
- paper `nu` implies unstable radius: `{inferred_radius:.16g}`

## Interpretation boundary

The stability definition is `nu = 0.5*(R_u + 1/R_u)`.  The earlier local
curve result (`nu` about 1337) is therefore not a scaling-definition error; it
belongs to a different small-amplitude source curve.  Likewise, projecting its
eigenvalues to a display radius near 2.35 cannot be used as numerical stability
evidence.  This audit uses the thesis-scale fixed-frequency energy branch at the
requested Jacobi constant without display rescaling.

The current collocation uses `{states.shape[0]}` physical phase samples, not the
paper's `N=25` label.  The stability value may only be promoted when it passes
the numerical tolerance and the paper's discretization convention is reconciled
or an `N=25` convergence comparison is supplied.
""",
        encoding="utf-8",
    )
    print(doc_path)
    print(csv_path)
    print(f"status={status} N={states.shape[0]} nu={dg.stability_index:.12g}")


if __name__ == "__main__":
    main()
