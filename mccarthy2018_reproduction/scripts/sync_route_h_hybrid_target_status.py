"""Synchronize Fig. 3.16/3.17 status from the hybrid target-state audit."""

from __future__ import annotations

import csv
from pathlib import Path

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS


DATA = PROJECT_ROOT / "data" / "computed"
TABLE_PATH = DATA / "figure_validation_table.csv"
STATE_PATH = DATA / "chapter3_route_h_fixed_time_target_states.csv"
COVERAGE_PATH = DATA / "chapter3_route_h_fixed_time_target_coverage_audit.csv"
HYBRID_PATH = DATA / "chapter3_route_h_hybrid_cold_start_audit.csv"
GATE_PATH = DATA / "mccarthy2018_staged_goal_gate_status.csv"


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    table = _read(TABLE_PATH)
    states = _read(STATE_PATH)
    coverage = _read(COVERAGE_PATH)
    hybrid = _read(HYBRID_PATH)
    if len(coverage) != 4 or len(hybrid) != 1 or hybrid[0].get("status") != "pass":
        raise RuntimeError("hybrid target evidence is incomplete")
    targets = sorted({float(row["target_jacobi"]) for row in states}, reverse=True)
    if len(targets) != 4:
        raise RuntimeError("hybrid target-state table must contain four Jacobi groups")
    length_unit = SYSTEMS["earth_moon"].length_unit_km
    rho = [
        float(next(row for row in states if float(row["target_jacobi"]) == target)["rotation_angle_rad"])
        for target in targets
    ]
    max_z_by_target = [
        max(abs(float(row["z"])) for row in states if float(row["target_jacobi"]) == target)
        * length_unit
        for target in targets
    ]
    max_residual = max(float(row["best_map_residual"]) for row in coverage)
    max_span = max(float(row["best_curve_jacobi_span"]) for row in coverage)
    strict = sum(row["strict_fixed_time_status"] == "pass" for row in coverage)
    paper = sum(row["paper_reported_precision_status"] == "pass" for row in coverage)
    sources = ";".join(
        str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
        for path in (STATE_PATH, COVERAGE_PATH, HYBRID_PATH, GATE_PATH)
    )
    quantities = (
        f"four fixed-time quasi-DRO anchors at JC={','.join(f'{value:.4f}' for value in targets)}; "
        f"rho {min(rho):.12g}..{max(rho):.12g} rad; max abs z "
        f"{min(max_z_by_target):.6g}..{max(max_z_by_target):.6g} km; "
        f"paper-precision coverage {paper}/4; internally strict fixed-time coverage {strict}/4"
    )
    for row in table:
        if row["figure_id"] == "3.16":
            row.update(
                {
                    "current_repro_level": "numerical reproduction",
                    "uses_proxy": "false",
                    "main_data_source": sources,
                    "key_physical_quantities": quantities,
                    "residual_norm": f"target max map residual {max_residual:.16g}",
                    "jacobi_drift": f"target max curve Jacobi span {max_span:.16g}",
                    "periodicity_error": "four target invariant curves satisfy their registered map gates",
                    "visual_status": "four panels render the four audited Fig. 3.16 fixed-time Jacobi target tori directly",
                    "next_action": "independently revalidate the target-state family and compare rendered geometry with the thesis panels",
                }
            )
        elif row["figure_id"] == "3.17":
            row.update(
                {
                    "current_repro_level": "hybrid fixed-time target anchors with Route H context",
                    "uses_proxy": "partial",
                    "main_data_source": sources,
                    "key_physical_quantities": quantities,
                    "residual_norm": f"target max map residual {max_residual:.16g}",
                    "jacobi_drift": f"target max curve Jacobi span {max_span:.16g}",
                    "periodicity_error": "four target invariant curves satisfy their registered map gates",
                    "visual_status": "four audited target anchors are explicit; historical Route H and faint reference trends remain contextual layers",
                    "next_action": "digitize thesis uncertainty bands if a quantitative full-curve equivalence claim is required",
                }
            )
    with TABLE_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    print(
        f"synced Fig. 3.16/3.17 hybrid targets: paper={paper}/4, strict={strict}/4, "
        f"max_residual={max_residual:.3e}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
