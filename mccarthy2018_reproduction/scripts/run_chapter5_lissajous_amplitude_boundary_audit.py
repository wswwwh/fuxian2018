"""Audit the planar-mode amplitude boundary of the Figure 5.13 source torus."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.quasi_torus import corrected_l1_vertical_lissajous_torus, resample_corrected_torus_surface  # noqa: E402


OUTPUT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_lissajous_amplitude_boundary_audit.csv"
REPORT = ROOT / "docs" / "chapter5_sun_earth_l1_lissajous_amplitude_boundary_audit.md"


def main() -> None:
    system = SYSTEMS["sun_earth"]
    rows: list[dict[str, object]] = []
    for amplitude in (1.0e-5, 2.0e-4, 3.0e-4):
        torus = corrected_l1_vertical_lissajous_torus(
            system.mu,
            vertical_orbit_amplitude=0.00628,
            planar_mode_amplitude=amplitude,
            samples=11,
            time_samples=24,
        )
        surface, _ = resample_corrected_torus_surface(torus, phase_samples=48)
        max_y = float(np.max(np.abs(surface[:, :, 1])) * system.length_unit_km)
        max_z = float(np.max(np.abs(surface[:, :, 2])) * system.length_unit_km)
        residual = float(np.max(torus.correction.final_residual_norms))
        jacobi_span = float(np.ptp(torus.jacobi_values))
        geometry_valid = (
            residual <= 1.0e-8
            and jacobi_span <= 1.0e-8
            and 500_000.0 <= max_z <= 1_500_000.0
            and max_y <= 2_000_000.0
        )
        rows.append(
            {
                "planar_mode_amplitude_nd": amplitude,
                "curve_residual_norm": residual,
                "torus_jacobi_span": jacobi_span,
                "max_abs_y_km": max_y,
                "max_abs_z_km": max_z,
                "paper_y_target_km": 660_000.0,
                "paper_z_target_km": 940_000.0,
                "y_target_error_km": max_y - 660_000.0,
                "z_target_error_km": max_z - 940_000.0,
                "geometry_valid": str(geometry_valid).lower(),
                "target_pair_accepted": str(
                    geometry_valid
                    and abs(max_y - 660_000.0) <= 50_000.0
                    and abs(max_z - 940_000.0) <= 50_000.0
                ).lower(),
            }
        )
    with OUTPUT.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    valid = [row for row in rows if row["geometry_valid"] == "true"]
    REPORT.write_text(
        f"""# Chapter 5 Lissajous amplitude boundary audit

- Tested planar-mode amplitudes: `{[row['planar_mode_amplitude_nd'] for row in rows]}`
- Geometry-valid rows: `{len(valid)}` / `{len(rows)}`
- Target-pair accepted rows: `{sum(row['target_pair_accepted'] == 'true' for row in rows)}`
- Best valid y amplitude: `{min(float(row['max_abs_y_km']) for row in valid):.3f}` km
- Corresponding paper target: `660000` km

Increasing the fixed-rotation planar-mode seed through `2e-4` does not reduce
the y amplitude materially. At `3e-4` the Newton correction enters a degenerate
branch with near-zero z scale and enormous y scale despite a small algebraic
residual. This demonstrates why residual-only acceptance is insufficient.
Resolving the remaining geometry discrepancy requires a constrained
free-rotation/free-mapping-time continuation, not a larger fixed-rotation seed.
""",
        encoding="utf-8",
    )
    print(OUTPUT)
    print(REPORT)
    print(f"valid={len(valid)}/{len(rows)}")


if __name__ == "__main__":
    main()
