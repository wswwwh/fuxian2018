"""Build and audit the finite-amplitude Sun-Earth L1 Lissajous source torus."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    corrected_l1_vertical_lissajous_torus,
    resample_corrected_torus_surface,
)


SURFACE = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_torus_surface.csv"
AUDIT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_torus_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_lissajous_torus_audit.md"


def main() -> None:
    system = SYSTEMS["sun_earth"]
    torus = corrected_l1_vertical_lissajous_torus(
        system.mu,
        vertical_orbit_amplitude=0.00628,
        samples=11,
        time_samples=60,
    )
    surface, _ = resample_corrected_torus_surface(torus, phase_samples=60)
    length = float(system.length_unit_km)
    max_abs_y_km = float(np.max(np.abs(surface[:, :, 1])) * length)
    max_abs_z_km = float(np.max(np.abs(surface[:, :, 2])) * length)
    residual = float(np.max(torus.correction.final_residual_norms))
    jacobi_span = float(np.ptp(torus.jacobi_values))
    z_error = max_abs_z_km - 940_000.0
    y_error = max_abs_y_km - 660_000.0
    accepted_source = residual <= 1.0e-8 and jacobi_span <= 1.0e-8 and surface.shape[0] * surface.shape[1] >= 3500

    with SURFACE.open("w", newline="", encoding="utf-8") as stream:
        fields = ("time_phase_index", "curve_phase_index", "x_nd", "y_nd", "z_nd")
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for i in range(surface.shape[0]):
            for j in range(surface.shape[1]):
                writer.writerow(
                    {
                        "time_phase_index": i,
                        "curve_phase_index": j,
                        "x_nd": f"{surface[i, j, 0]:.16g}",
                        "y_nd": f"{surface[i, j, 1]:.16g}",
                        "z_nd": f"{surface[i, j, 2]:.16g}",
                    }
                )

    row = {
        "figure_id": "5.13",
        "source_model": "Sun-Earth L1 CR3BP corrected quasi-vertical Lissajous torus",
        "vertical_boundary_amplitude_nd": 0.00628,
        "invariant_curve_samples": 11,
        "rendered_torus_points": int(surface.shape[0] * surface.shape[1]),
        "mapping_time_days": torus.correction.seed.orbit_period * system.time_unit_days,
        "curve_residual_norm": residual,
        "torus_jacobi_span": jacobi_span,
        "max_abs_y_km": max_abs_y_km,
        "max_abs_z_km": max_abs_z_km,
        "paper_y_target_km": 660_000.0,
        "paper_z_target_km": 940_000.0,
        "y_target_error_km": y_error,
        "z_target_error_km": z_error,
        "source_acceptance": str(accepted_source).lower(),
        "stable_manifold_map_acceptance": "pending",
    }
    with AUDIT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    REPORT.write_text(
        f"""# Chapter 5 Sun-Earth L1 Lissajous source-torus audit

- Corrected invariant-curve residual: `{residual:.6e}`
- Torus Jacobi span: `{jacobi_span:.6e}`
- Resampled torus points: `{surface.shape[0] * surface.shape[1]}`
- Maximum absolute y: `{max_abs_y_km:.3f}` km (paper target `660000` km)
- Maximum absolute z: `{max_abs_z_km:.3f}` km (paper target `940000` km)
- Source-layer acceptance: `{'pass' if accepted_source else 'fail'}`
- Stable-manifold periapsis-map acceptance: `pending`

The torus is generated from a continued L1 vertical periodic boundary and a
corrected planar elliptic invariant curve. It is a genuine two-frequency CR3BP
source layer, not the analytic display torus previously used by Fig. 5.13.
The z scale is close to the reported target, while the y amplitude remains a
quantitative geometry boundary. Figure 5.13 must not be promoted until a
two-angle stable-manifold periapsis scan is generated from this source and the
y-amplitude discrepancy is resolved or explicitly accepted as a model boundary.
""",
        encoding="utf-8",
    )
    print(AUDIT)
    print(SURFACE)
    print(REPORT)
    print(f"source_acceptance={accepted_source}")


if __name__ == "__main__":
    main()
