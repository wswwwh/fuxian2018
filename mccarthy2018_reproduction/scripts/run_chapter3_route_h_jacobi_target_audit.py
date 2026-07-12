"""Audit Route H cache coverage of the four Fig. 3.16 Jacobi anchors."""

from __future__ import annotations

import csv
import pickle
from pathlib import Path

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant


TARGETS = (2.9225, 2.9221, 2.9215, 2.9212)
TOLERANCE = 5.0e-7
SOURCES = {
    "historical_canonical": (
        PROJECT_ROOT
        / "data"
        / "computed"
        / "cache"
        / "fixed_mapping_dro_v1_079947170b953a50.pkl"
    ),
    "cold_start_full_checkpoint": (
        PROJECT_ROOT
        / "outputs"
        / "cold_start"
        / "fixed_mapping_full"
        / "fixed_mapping_dro_v1_079947170b953a50.pkl"
    ),
}
CSV_PATH = PROJECT_ROOT / "data" / "computed" / "chapter3_route_h_jacobi_target_audit.csv"
DOC_PATH = PROJECT_ROOT / "docs" / "chapter3_route_h_jacobi_target_audit.md"
FIELDS = (
    "source",
    "cache_path",
    "member_count",
    "minimum_mean_jacobi",
    "maximum_mean_jacobi",
    "target_jacobi",
    "nearest_member",
    "nearest_mean_jacobi",
    "absolute_error",
    "tolerance",
    "status",
)


def _rows() -> list[dict[str, object]]:
    mu = SYSTEMS["earth_moon"].mu
    rows: list[dict[str, object]] = []
    for source, path in SOURCES.items():
        with path.open("rb") as stream:
            family = tuple(pickle.load(stream))
        values = np.asarray(
            [float(np.mean(jacobi_constant(member.corrected_states, mu))) for member in family]
        )
        for target in TARGETS:
            nearest = int(np.argmin(np.abs(values - target)))
            error = float(abs(values[nearest] - target))
            rows.append(
                {
                    "source": source,
                    "cache_path": path.relative_to(PROJECT_ROOT),
                    "member_count": len(family),
                    "minimum_mean_jacobi": float(np.min(values)),
                    "maximum_mean_jacobi": float(np.max(values)),
                    "target_jacobi": target,
                    "nearest_member": nearest,
                    "nearest_mean_jacobi": float(values[nearest]),
                    "absolute_error": error,
                    "tolerance": TOLERANCE,
                    "status": "pass" if error <= TOLERANCE else "fail",
                }
            )
    return rows


def _write_csv(rows: list[dict[str, object]]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _write_doc(rows: list[dict[str, object]]) -> None:
    lines = [
        "# Chapter 3 Route H Jacobi-Target Audit",
        "",
        "## Result",
        "",
    ]
    for source in SOURCES:
        source_rows = [row for row in rows if row["source"] == source]
        passed = sum(row["status"] == "pass" for row in source_rows)
        lines.extend(
            [
                f"### `{source}`",
                "",
                f"- Coverage: `{passed}/{len(TARGETS)}` targets within `{TOLERANCE:.1e}`.",
                f"- Members: `{source_rows[0]['member_count']}`.",
                "- Mean-Jacobi range: "
                f"`{float(source_rows[0]['minimum_mean_jacobi']):.16g}.."
                f"{float(source_rows[0]['maximum_mean_jacobi']):.16g}`.",
                "",
                "| Target | Nearest member | Nearest value | Absolute error | Status |",
                "| ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for row in source_rows:
            lines.append(
                f"| {float(row['target_jacobi']):.7f} | {row['nearest_member']} | "
                f"{float(row['nearest_mean_jacobi']):.12f} | "
                f"{float(row['absolute_error']):.3e} | {row['status']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Boundary",
            "",
            "The historical cache is a valuable high-amplitude source-layer artifact, but",
            "its 69 members do not cover the full Fig. 3.16 Jacobi set. The isolated",
            "cold-start checkpoint also does not cover that set. Consequently, neither",
            "maximum vertical amplitude nor cache length proves thesis-parameter coverage.",
            "All four rows must pass from an isolated cold start before the Fig. 3.16/3.17",
            "parameter-range gate can be promoted.",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = _rows()
    _write_csv(rows)
    _write_doc(rows)
    for source in SOURCES:
        source_rows = [row for row in rows if row["source"] == source]
        passed = sum(row["status"] == "pass" for row in source_rows)
        print(f"{source}: {passed}/{len(TARGETS)} Jacobi targets")
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
