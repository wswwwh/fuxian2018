"""Audit the proxy-free Figure 4.5/4.6/4.8 quasi-vertical manifold source."""

from __future__ import annotations

import csv
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.torus_stability import (  # noqa: E402
    corrected_l1_constant_energy_vertical_unstable_manifolds,
)


SNAPSHOTS = (8.05, 10.08, 11.77, 13.46)


def main() -> None:
    system = SYSTEMS["earth_moon"]
    plus_x, minus_x = corrected_l1_constant_energy_vertical_unstable_manifolds(
        system.mu,
        time_unit_days=system.time_unit_days,
        snapshot_times_days=SNAPSHOTS,
    )
    rows: list[dict[str, object]] = []
    for figure_id, branch, sheet in (
        ("4.5", "plus_x", plus_x),
        ("4.6", "minus_x", minus_x),
    ):
        elapsed_days = sheet.times * system.time_unit_days
        jacobi = jacobi_constant(
            sheet.manifold_states.reshape(-1, 6), system.mu
        ).reshape(sheet.manifold_states.shape[:2])
        jacobi_drift = float(np.max(np.ptp(jacobi, axis=0)))
        source_jacobi = jacobi_constant(sheet.dg.correction.corrected_states, system.mu)
        source_energy_span = float(np.ptp(source_jacobi))
        initial_separation = float(np.mean(sheet.state_separation_norms[0]))
        multiplier = float(abs(sheet.eigenvalue))
        for requested in SNAPSHOTS:
            time_index = int(np.argmin(abs(elapsed_days - requested)))
            actual = float(elapsed_days[time_index])
            separation = float(np.mean(sheet.state_separation_norms[time_index]))
            measured_growth = separation / initial_separation
            expected_growth = multiplier ** (actual / (sheet.dg.mapping_time * system.time_unit_days))
            growth_ratio = measured_growth / expected_growth
            accepted = (
                abs(actual - requested) <= 1.0e-10
                and sheet.surface.shape[1] == 33
                and sheet.dg.correction.final_residual_norms.max() <= 1.0e-8
                and jacobi_drift <= 1.0e-10
                and 0.5 <= growth_ratio <= 2.0
            )
            rows.append(
                {
                    "figure_id": figure_id,
                    "branch": branch,
                    "requested_snapshot_days": requested,
                    "actual_snapshot_days": actual,
                    "snapshot_time_error_days": actual - requested,
                    "curve_samples": sheet.surface.shape[1],
                    "source_mapping_time_days": sheet.dg.mapping_time * system.time_unit_days,
                    "source_curve_residual": sheet.dg.correction.final_residual_norms.max(),
                    "jacobi_drift_max": jacobi_drift,
                    "source_curve_energy_span": source_energy_span,
                    "unstable_multiplier": multiplier,
                    "measured_growth": measured_growth,
                    "expected_growth": expected_growth,
                    "growth_ratio": growth_ratio,
                    "snapshot_x_min": float(np.min(sheet.surface[time_index, :, 0])),
                    "snapshot_x_max": float(np.max(sheet.surface[time_index, :, 0])),
                    "uses_proxy_background": "false",
                    "dynamics_acceptance": "pass" if accepted else "fail",
                    "paper_projection_acceptance": "not_run_or_fail",
                    "paper_geometry_boundary": (
                        "single-view 3D projection not calibrated; contact sheet shows "
                        "material global-reach/topology mismatch"
                    ),
                    "acceptance": "pass" if accepted else "fail",
                }
            )

    data = ROOT / "data" / "computed" / "chapter4_fig45_fig48_vertical_manifold_audit.csv"
    with data.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed = sum(row["acceptance"] == "pass" for row in rows)
    report = ROOT / "docs" / "chapter4_fig45_fig48_vertical_manifold_audit.md"
    report.write_text(
        f"""# Chapter 4 Figures 4.5-4.8 quasi-vertical manifold audit

- Audited snapshot rows: `{len(rows)}`
- Accepted snapshot rows: `{passed}`
- Source: validated `JC=3.1389`, 33-node, 12.66-day staged quasi-vertical endpoint
- Requested snapshot times: `{SNAPSHOTS}` days
- Maximum per-trajectory Jacobi drift: `{max(float(row['jacobi_drift_max']) for row in rows):.6e}`
- Source-curve energy span: `{max(float(row['source_curve_energy_span']) for row in rows):.6e}`
- Growth-ratio range: `{min(float(row['growth_ratio']) for row in rows):.6f}` to `{max(float(row['growth_ratio']) for row in rows):.6f}`
- Proxy background: `false`
- Internal dynamics acceptance: `{'pass' if passed == len(rows) else 'fail'}`
- Paper projection acceptance: `not_run_or_fail`

Figures 4.5 and 4.6 propagate both signs of the real unstable eigenvector and
label them by terminal mean x. Figure 4.8 reuses the audited Earthward branch
for comparison with the independently integrated periodic-halo manifold.

The `acceptance` column is an internal dynamics gate only. It does not validate
the paper geometry. The current comparison contact sheets show a material
global-reach/topology mismatch: Fig. 4.5 ends at x=0.889300..0.916987 and Fig.
4.6/4.8 use an Earthward branch ending at x=0.784378..0.837716, whereas the
thesis panels show much larger folded Moon-side and Earthward structures. A
static single-view 3D bitmap cannot yield a defensible 3D pointwise error. The
paper-facing task is to extend the manifolds and perform a locked-camera
projection-space geometry audit; digitization will measure the gap rather than
automatically close it.
""",
        encoding="utf-8",
    )
    print(data)
    print(report)
    print(f"accepted={passed}/{len(rows)}")


if __name__ == "__main__":
    main()
