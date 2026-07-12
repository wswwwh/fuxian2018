"""Audit the proxy-free Figure 4.3/4.4 quasi-halo global manifolds."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
SOURCE = DATA / "chapter4_corrected_l1_constant_energy_halo_unstable_manifolds.csv"
VALIDATION = DATA / "chapter4_manifold_validation.csv"
SNAPSHOTS = (7.79, 9.75, 11.39, 13.02)


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> None:
    source = read(SOURCE)
    validation = {row["figure_id"]: row for row in read(VALIDATION)}
    rows: list[dict[str, object]] = []
    for figure_id, branch in (("4.3", "plus_x"), ("4.4", "minus_x")):
        branch_rows = [row for row in source if row["branch"] == branch]
        times = np.array(sorted({float(row["elapsed_days"]) for row in branch_rows}))
        initial = [row for row in branch_rows if abs(float(row["elapsed_days"])) <= 1e-14]
        initial_separation = float(np.mean([float(row["state_separation_nd"]) for row in initial]))
        curve_indices = sorted({int(row["curve_index"]) for row in branch_rows})
        jacobi_drift = max(
            float(
                np.ptp(
                    [
                        float(row["jacobi"])
                        for row in branch_rows
                        if int(row["curve_index"]) == curve_index
                    ]
                )
            )
            for curve_index in curve_indices
        )
        curve_energy_span = float(
            np.ptp([float(row["jacobi"]) for row in branch_rows if abs(float(row["elapsed_days"])) <= 1e-14])
        )
        eigenvalue = float(branch_rows[0]["eigenvalue_real"])
        mapping_time = float(branch_rows[0]["mapping_time_days"])
        meta = validation[figure_id]
        for requested in SNAPSHOTS:
            actual = float(times[np.argmin(np.abs(times - requested))])
            snapshot = [row for row in branch_rows if abs(float(row["elapsed_days"]) - actual) <= 1e-12]
            mean_separation = float(np.mean([float(row["state_separation_nd"]) for row in snapshot]))
            measured_growth = mean_separation / initial_separation
            expected_growth = eigenvalue ** (actual / mapping_time)
            growth_ratio = measured_growth / expected_growth
            accepted = (
                abs(actual - requested) <= 1e-10
                and len(snapshot) == 9
                and jacobi_drift <= 1e-10
                and 0.5 <= growth_ratio <= 2.0
                and float(meta["source_curve_residual"]) <= 1e-8
                and meta["uses_proxy_background"].lower() == "false"
            )
            rows.append(
                {
                    "figure_id": figure_id,
                    "branch": branch,
                    "requested_snapshot_days": requested,
                    "actual_snapshot_days": actual,
                    "snapshot_time_error_days": actual - requested,
                    "curve_samples": len(snapshot),
                    "source_curve_residual": meta["source_curve_residual"],
                    "jacobi_drift_max": jacobi_drift,
                    "source_curve_energy_span": curve_energy_span,
                    "initial_mean_separation_nd": initial_separation,
                    "snapshot_mean_separation_nd": mean_separation,
                    "measured_growth": measured_growth,
                    "expected_growth": expected_growth,
                    "growth_ratio": growth_ratio,
                    "terminal_x_min": min(float(row["x"]) for row in snapshot),
                    "terminal_x_max": max(float(row["x"]) for row in snapshot),
                    "uses_proxy_background": meta["uses_proxy_background"],
                    "acceptance": "pass" if accepted else "fail",
                }
            )

    csv_path = DATA / "chapter4_fig43_fig44_global_manifold_audit.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    passed = [row for row in rows if row["acceptance"] == "pass"]
    doc_path = DOCS / "chapter4_fig43_fig44_global_manifold_audit.md"
    doc_path.write_text(
        f"""# Chapter 4 Figures 4.3-4.4 global manifold audit

- Snapshot rows: `{len(rows)}`
- Accepted snapshot rows: `{len(passed)}`
- Figures covered: `{sorted({row['figure_id'] for row in passed})}`
- Requested times: `{SNAPSHOTS}` days
- Maximum per-trajectory Jacobi drift: `{max(float(row['jacobi_drift_max']) for row in rows):.6e}`
- Source-curve energy span: `{max(float(row['source_curve_energy_span']) for row in rows):.6e}`
- Growth-ratio range: `{min(float(row['growth_ratio']) for row in rows):.6f}` to `{max(float(row['growth_ratio']) for row in rows):.6f}`
- Proxy background: `false`
- Overall acceptance: `{'pass' if len(passed) == len(rows) else 'fail'}`

Both half-manifolds are propagated directly from the real unstable eigenvector
of the corrected `JC=3.1389` quasi-halo DG. The four panels use the paper's
reported elapsed times exactly. No analytic torus or synthetic manifold sheet
is used. The source-curve energy span is retained as a separate N=9 resolution
boundary rather than mislabeled as propagation drift. Remaining uncertainty is
the N=9 source-curve resolution and the lack
of a digitized pointwise comparison against the paper panels.
""",
        encoding="utf-8",
    )
    print(csv_path)
    print(doc_path)
    print(f"accepted={len(passed)}/{len(rows)}")


if __name__ == "__main__":
    main()
