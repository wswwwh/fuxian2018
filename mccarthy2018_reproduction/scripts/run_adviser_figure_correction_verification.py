"""Verify the adviser-flagged figure repairs without claiming paper equivalence.

The gate deliberately separates three questions:

1. Does each renderer use the intended source and disclose known boundaries?
2. Do the available numerical audits support that disclosure?
3. Is the exact PNG that was manually inspected still the current PNG?

Passing this audit means the figure is presentation-correct and no known
limitation is hidden. It does *not* mean that the figure is pointwise equivalent
to McCarthy (2018).
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA = PROJECT_ROOT / "data" / "computed"
FIGURES = PROJECT_ROOT / "figures"
PNG_DIR = PROJECT_ROOT / "outputs" / "figures_png"
PDF_DIR = PROJECT_ROOT / "outputs" / "figures_pdf"
OUT_DIR = PROJECT_ROOT / "reports" / "adviser_figure_correction_verification"
OUT_CSV = OUT_DIR / "current_figure_correction_verification.csv"
OUT_MD = OUT_DIR / "current_figure_correction_verification.md"
VISUAL_MANIFEST = OUT_DIR / "visual_review_manifest.csv"


@dataclass(frozen=True)
class FigureSpec:
    figure_id: str
    priority: str
    script: str
    repair_mode: str
    expected_proxy: str
    required_tokens: tuple[str, ...]
    forbidden_tokens: tuple[str, ...] = ()
    remaining_boundary: str = "Paper pointwise equivalence remains open."


SPECS = (
    FigureSpec("3.5", "P0", "fig_3_05.py", "rendering_and_anchor_boundary", "false", ("paper-geometry boundary", "shade=False"), remaining_boundary="The 12.03-day paper y/z amplitude anchor is not matched."),
    FigureSpec("3.6", "P0", "fig_3_06.py", "quantitative_anchor_disclosure", "false", ("paper 12.03-day anchors", "unmatched paper anchor"), remaining_boundary="The full paper curves still require digitized pointwise comparison."),
    FigureSpec("3.7", "P0", "fig_3_07.py", "transparent_topology_boundary", "false", ("late-family paper topology", "plot_wireframe"), remaining_boundary="Late-family paper topology/projection is not matched."),
    FigureSpec("3.9", "P1", "fig_3_09.py", "proxy_tail_disclosure", "partial", ("unvalidated analytic proxy tail", "proxy_tail"), remaining_boundary="The dashed halo tail is not a numerical continuation."),
    FigureSpec("3.10", "P1", "fig_3_10.py", "strict_vs_local_acceptance_split", "partial", ("single-shoot closure FAIL", "strict closure PASS"), remaining_boundary="q=8 lacks strict full-period single-shoot closure."),
    FigureSpec("3.11", "P1", "fig_3_11.py", "proxy_semantics_repaired", "partial", ("not computed section crossings", "CR3BP-integrated central periodic orbits"), ("paper_like_map_contours",), "The illustrative section contours must be replaced by event-detected crossings."),
    FigureSpec("3.12", "P0", "fig_3_12.py", "transparent_topology_boundary", "false", ("paper torus-topology gate", "plot_wireframe"), remaining_boundary="Panels (b)-(d) do not preserve the paper torus-hole topology."),
    FigureSpec("3.13", "P0", "fig_3_13.py", "endpoint_coverage_boundary", "false", ("paper endpoint", "np.max(z_amplitude)"), remaining_boundary="The numerical branch ends below the approximately 93000-km paper endpoint."),
    FigureSpec("3.16", "P0", "fig_3_16.py", "source_and_renderer_repaired", "false", ("plot_surface", "periodic_dro", "full thesis branch/range equivalence remains open"), remaining_boundary="Route H does not cover the full thesis branch/range."),
    FigureSpec("3.17", "P1", "fig_3_17.py", "proxy_context_disclosure", "partial", ("proxy context only", "audited Route H evidence"), remaining_boundary="Most of the thesis-scale trend remains proxy context."),
    FigureSpec("4.1", "P0", "fig_4_01.py", "degenerate_surface_removed", "false", ("Finite-torus geometry: FAIL", "max phase width"), ("ax3d.plot_surface",), "The DG target passes, but finite-amplitude torus geometry does not."),
    FigureSpec("4.2", "P1", "fig_4_02.py", "digitized_overlap_and_tail_boundary", "false", ("fig_4_2_digitized_points.csv", "uncovered tail", "no extrapolation"), remaining_boundary="The last approximately 0.04945 day of the paper curve is uncovered."),
    FigureSpec("4.3", "P0", "fig_4_03.py", "frozen_projection_failure_disclosure", "false", ("paper_projection=FAIL", "frozen holdout 0/4"), remaining_boundary="Frozen paper-projection holdout fails."),
    FigureSpec("4.4", "P0", "fig_4_04.py", "frozen_projection_failure_disclosure", "false", ("paper_projection=FAIL", "frozen holdout 0/4"), remaining_boundary="Frozen paper-projection holdout fails."),
    FigureSpec("4.5", "P0", "fig_4_05.py", "frozen_projection_failure_disclosure", "false", ("paper_projection=FAIL", "frozen holdout 0/4"), remaining_boundary="Frozen paper-projection holdout fails."),
    FigureSpec("4.6", "P0", "fig_4_06.py", "frozen_projection_failure_disclosure", "false", ("paper_projection=FAIL", "frozen holdout 0/4"), remaining_boundary="Frozen paper-projection holdout fails."),
    FigureSpec("4.7", "P0", "fig_4_07.py", "local_baseline_disclosure", "false", ("Local numerical manifold only", "global reach/topology not reproduced"), remaining_boundary="The dense thesis global reach/topology is not reproduced."),
    FigureSpec("4.8", "P0", "fig_4_08.py", "local_baseline_disclosure", "false", ("Local numerical manifold only", "Earthward reach/topology not reproduced"), remaining_boundary="The dense thesis Earthward reach/topology is not reproduced."),
    FigureSpec("5.1", "P0", "fig_5_01.py", "data_source_repaired", "false", ("chapter5_sun_earth_l1_active_geometry_long_trajectory.npz",), ("chapter5_sun_earth_l1_lissajous_torus_surface.csv",), "BCR4BP/ephemeris and pointwise paper comparison remain open."),
    FigureSpec("5.5", "P0", "fig_5_05.py", "proxy_scene_removed", "false", ("chapter5_corrected_dro_quasi_dro_return.csv",), ("quasi_dro_return_scene",), "A corrected ephemeris/BCR4BP return remains open."),
    FigureSpec("5.8", "P1", "fig_5_08.py", "project_baseline_disclosure", "false", ("CR3BP project baseline", "thesis pointwise geometry"), remaining_boundary="Thesis pointwise geometry and high-fidelity correction remain open."),
    FigureSpec("5.10", "P1", "fig_5_10.py", "numerical_vs_paper_acceptance_split", "false", ("paper-equivalent transfer cases: 0/2", "CR3BP project baseline"), remaining_boundary="The paper-specific quasi-NRHO boundary states and geometry are not recovered."),
    FigureSpec("5.12", "P0", "fig_5_12.py", "truncated_domain_disclosure", "false", ("+12 to +24 h", "not computed", "no extrapolation", "set_xlim(-24, 24)"), remaining_boundary="The numerical branch stops at +11 h."),
    FigureSpec("5.13", "P0", "fig_5_13.py", "data_source_repaired", "false", ("chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv",), ("chapter5_sun_earth_l1_lissajous_stable_manifold_scan.csv",), "High-fidelity correction and pointwise heat-map comparison remain open."),
    FigureSpec("5.14", "P0", "fig_5_14.py", "data_source_and_target_repaired", "false", ("chapter5_sun_earth_l1_active_geometry_long_trajectory.npz", "chapter5_active_geometry_leo_transfer.csv"), ("chapter5_sun_earth_l1_lissajous_leo_transfer.csv",), "High-fidelity BCR4BP/ephemeris correction remains open."),
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sha(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _artifact_paths(figure_id: str) -> tuple[Path, Path]:
    stem = f"fig_{figure_id.replace('.', '_')}"
    return PNG_DIR / f"{stem}.png", PDF_DIR / f"{stem}.pdf"


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def _numerical_gate(figure_id: str) -> tuple[bool, str]:
    if figure_id == "3.10":
        rows = {row["resonance"]: row for row in _read_csv(DATA / "chapter3_period_q_per_figure_audit.csv")}
        ok = rows["2"]["strict_acceptance"] == "true" and rows["3"]["strict_acceptance"] == "true" and rows["8"]["strict_acceptance"] == "false"
        return ok, "q2/q3 strict pass; q8 strict fail retained"
    if figure_id == "4.1":
        rows = _read_csv(DATA / "chapter4_fig41_reported_precision_states.csv")
        time_count = 1 + max(int(row["time_index"]) for row in rows)
        curve_count = 1 + max(int(row["curve_index"]) for row in rows)
        surface = np.asarray([[float(row[name]) for name in ("x", "y", "z")] for row in rows]).reshape(time_count, curve_count, 3)
        width_km = max(float(np.max(np.linalg.norm(item[:, None] - item[None, :], axis=2))) for item in surface) * 384400.0
        return width_km < 0.01, f"max phase width {width_km:.9f} km; degenerate geometry disclosed"
    if figure_id == "4.2":
        row = _read_csv(DATA / "chapter4_fig42_digitized_comparison_audit.csv")[0]
        ok = _truthy(row["pointwise_overlap_acceptance"]) and not _truthy(row["full_curve_coverage"])
        return ok, f"overlap pass; tail gap {float(row['computed_tail_time_gap_days']):.9f} day"
    if figure_id in {"4.3", "4.4", "4.5", "4.6"}:
        rows = [row for row in _read_csv(DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv") if row["figure_id"] == figure_id]
        ok = len(rows) == 1 and rows[0]["holdout_gate"] == "fail" and rows[0]["paper_3d_equivalence"] == "false"
        return ok, "frozen projection holdout fail and paper_3d=false retained"
    if figure_id == "5.1":
        rows = _read_csv(DATA / "chapter5_sun_earth_l1_long_propagation_per_figure_audit.csv")
        durations = tuple(float(row["duration_days"]) for row in rows)
        return len(rows) == 3 and all(_truthy(row["acceptance"]) for row in rows) and durations == (325.0, 1068.0, 2182.0), "one common trajectory at 325/1068/2182 days"
    if figure_id == "5.10":
        rows = _read_csv(DATA / "chapter5_fig510_bcr4bp_transfer_audit.csv")
        numerical = sum(_truthy(row["numerical_acceptance"]) for row in rows)
        paper = sum(_truthy(row["paper_equivalence"]) for row in rows)
        return numerical == 2 and paper == 0, "BCR4BP numerical 2/2; paper equivalence 0/2"
    if figure_id == "5.12":
        rows = _read_csv(DATA / "chapter5_nrho_rendezvous_per_figure_audit.csv")
        right_edge = max(float(row["arrival_offset_hours"]) for row in rows if _truthy(row["acceptance"]))
        return right_edge == 11.0, "accepted branch right edge +11 h"
    if figure_id == "5.13":
        rows = _read_csv(DATA / "chapter5_sun_earth_l1_active_geometry_stable_manifold_scan.csv")
        theta0 = {row["theta0_deg"] for row in rows}
        theta1 = {row["theta1_deg"] for row in rows}
        return len(rows) == 1120 and len(theta0) == 70 and len(theta1) == 16, "active two-angle scan 70x16"
    if figure_id == "5.14":
        row = _read_csv(DATA / "chapter5_active_geometry_leo_transfer_audit.csv")[0]
        ok = _truthy(row["acceptance"]) and abs(float(row["target_periapsis_radius_km"]) - 6563.0) < 1.0e-9
        return ok, "185-km LEO target radius 6563 km"
    return True, "source-layer/boundary evidence is tracked by the per-figure audit"


def _write_visual_manifest() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with VISUAL_MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        fields = ["figure_id", "png_sha256", "reviewed_on", "verdict", "scope"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for spec in SPECS:
            png, _ = _artifact_paths(spec.figure_id)
            writer.writerow(
                {
                    "figure_id": spec.figure_id,
                    "png_sha256": _sha(png),
                    "reviewed_on": date.today().isoformat(),
                    "verdict": "pass",
                    "scope": "layout legibility and visible disclosure; not paper equivalence",
                }
            )


def _visual_lookup() -> dict[str, dict[str, str]]:
    if not VISUAL_MANIFEST.exists():
        return {}
    return {row["figure_id"]: row for row in _read_csv(VISUAL_MANIFEST)}


def _build_rows() -> list[dict[str, str]]:
    validation = {row["figure_id"]: row for row in _read_csv(DATA / "figure_validation_table.csv")}
    visual = _visual_lookup()
    rows: list[dict[str, str]] = []
    for spec in SPECS:
        script_path = FIGURES / spec.script
        source = script_path.read_text(encoding="utf-8")
        png, pdf = _artifact_paths(spec.figure_id)
        source_gate = all(token in source for token in spec.required_tokens) and all(token not in source for token in spec.forbidden_tokens)
        artifact_gate = png.exists() and pdf.exists() and png.stat().st_size > 5000 and pdf.stat().st_size > 5000
        metadata = validation.get(spec.figure_id, {})
        metadata_gate = metadata.get("uses_proxy") == spec.expected_proxy
        numerical_gate, numerical_evidence = _numerical_gate(spec.figure_id)
        visual_row = visual.get(spec.figure_id, {})
        visual_gate = visual_row.get("verdict") == "pass" and visual_row.get("png_sha256") == (_sha(png) if png.exists() else "")
        presentation_gate = source_gate and artifact_gate and metadata_gate and numerical_gate and visual_gate
        rows.append(
            {
                "figure_id": spec.figure_id,
                "previous_priority": spec.priority,
                "repair_mode": spec.repair_mode,
                "source_truth_gate": str(source_gate).lower(),
                "metadata_gate": str(metadata_gate).lower(),
                "numerical_boundary_gate": str(numerical_gate).lower(),
                "artifact_gate": str(artifact_gate).lower(),
                "visual_hash_gate": str(visual_gate).lower(),
                "presentation_correctness": "pass" if presentation_gate else "fail",
                "full_paper_equivalence": "not_claimed",
                "uses_proxy": metadata.get("uses_proxy", "missing"),
                "numerical_evidence": numerical_evidence,
                "remaining_boundary": spec.remaining_boundary,
                "script": script_path.relative_to(PROJECT_ROOT).as_posix(),
                "png": png.relative_to(PROJECT_ROOT).as_posix(),
                "pdf": pdf.relative_to(PROJECT_ROOT).as_posix(),
                "script_sha256": _sha(script_path),
                "png_sha256": _sha(png) if png.exists() else "",
                "pdf_sha256": _sha(pdf) if pdf.exists() else "",
            }
        )
    return rows


def _write_report(rows: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with OUT_CSV.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    passed = sum(row["presentation_correctness"] == "pass" for row in rows)
    p0 = sum(row["previous_priority"] == "P0" for row in rows)
    p1 = sum(row["previous_priority"] == "P1" for row in rows)
    lines = [
        "# 导师指出图像的当前修正验收",
        "",
        f"- 覆盖：`{len(rows)}` 幅（原 P0 `{p0}`，原 P1 `{p1}`）。",
        f"- 当前表达正确性：`{passed}/{len(rows)}` 通过。",
        "- `通过` 的含义：绘图源、代理标记、数值边界、PNG/PDF 产物与人工查看过的 PNG 哈希一致。",
        "- 这里**不声明论文逐点等价**；所有未完成的论文等价条件仍保留在 `remaining_boundary`。",
        "",
        "| 图 | 原优先级 | 修正方式 | 表达门槛 | 代理 | 数值证据 | 尚存边界 |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        evidence = row["numerical_evidence"].replace("|", "\\|")
        boundary = row["remaining_boundary"].replace("|", "\\|")
        lines.append(
            f"| {row['figure_id']} | {row['previous_priority']} | {row['repair_mode']} | "
            f"{row['presentation_correctness']} | {row['uses_proxy']} | {evidence} | {boundary} |"
        )
    lines.extend(
        [
            "",
            "## 判定边界",
            "",
            "本表解决的是导师指出的明显错误、错误数据源、代理未披露、截断范围未披露和失败门槛被隐藏的问题。",
            "若要把某幅图升级为 McCarthy (2018) 的论文等价复现，仍必须完成该行记录的数值延拓、全局流形、点对点数字化或高保真动力学门槛。",
            "",
            f"人工视觉复核清单：`{VISUAL_MANIFEST.relative_to(PROJECT_ROOT).as_posix()}`。",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-visual-review", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.record_visual_review:
        _write_visual_manifest()
    rows = _build_rows()
    _write_report(rows)
    failed = [row["figure_id"] for row in rows if row["presentation_correctness"] != "pass"]
    print(f"updated {OUT_CSV.relative_to(PROJECT_ROOT)}")
    print(f"updated {OUT_MD.relative_to(PROJECT_ROOT)}")
    print(f"adviser_figure_correction_verification: pass={len(rows) - len(failed)}/{len(rows)}; failed={failed}")
    if args.check and failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
