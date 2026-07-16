#!/usr/bin/env python3
"""Build the audited Stage-G adviser delivery package without changing science results."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import textwrap
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from pypdf import PdfReader


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
STAGE_G = PROJECT_ROOT / "stage_g_delivery_review"
ADVISER_ROOT = PROJECT_ROOT / "reports" / "adviser_delivery"
PENDING = "【待核实】"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
DOCX_NAME = "McCarthy2018_54图逐图复现对照报告.docx"
PDF_NAME = "McCarthy2018_54图逐图复现对照报告.pdf"
ONE_PAGE_NAME = "复现情况一页说明.pdf"
FOCUS_NAME = "导师审阅重点.md"

COORDINATE_EVIDENCE = {
    "5.2": "figures/fig_5_02.py",
    "5.3": "figures/fig_5_03.py",
    "5.4": "figures/fig_5_04.py",
    "5.6": "figures/fig_5_06.py;src/qp_orbits/ephemeris.py;data/computed/chapter5_de421_quasi_dro_scenes.csv",
    "5.7": "figures/fig_5_07.py;src/qp_orbits/ephemeris.py;data/computed/chapter5_de421_quasi_dro_scenes.csv",
    "5.10": "src/qp_orbits/bcr4bp.py;scripts/run_chapter5_fig510_bcr4bp_transfer_audit.py;data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_artifact(path: Path) -> tuple[str, bytes]:
    data = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".txt", ".py", ".js", ".yml", ".yaml"}:
        text = data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        return "utf8_lf_normalized", text.encode("utf-8")
    return "raw_bytes", data


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    return "".join(node.text or "" for node in root.iter(f"{{{W_NS}}}t"))


def extract_pdf_text(path: Path) -> str:
    document = fitz.open(path)
    try:
        return "\n".join(page.get_text("text") for page in document)
    finally:
        document.close()


def build_placeholder_audit() -> tuple[list[dict[str, object]], dict[str, object]]:
    registry = read_csv(REPORT_ROOT / "figure_comparison_registry.csv")
    if len(registry) != 54:
        raise RuntimeError(f"Expected 54 registry rows, found {len(registry)}")
    delivery_fields = json.loads((REPORT_ROOT / "delivery_fields.json").read_text(encoding="utf-8"))
    docx_path = REPORT_ROOT / DOCX_NAME
    pdf_path = REPORT_ROOT / PDF_NAME
    docx_text = extract_docx_text(docx_path)
    pdf_text = extract_pdf_text(pdf_path)
    rows: list[dict[str, object]] = []

    manual = {
        "author_name": delivery_fields["author_name"],
        "affiliation": delivery_fields["affiliation"],
        "adviser": delivery_fields["adviser"],
    }
    identity_confirmed = delivery_fields.get("verification_status") == "confirmed_by_user"
    for field, value in manual.items():
        if not value or PENDING in value or value not in docx_text or value not in pdf_text:
            raise RuntimeError(f"Confirmed identity field is not preserved consistently: {field}")
        rows.append(
            {
                "scope": "cover",
                "target_id": "cover",
                "field": field,
                "status": "confirmed_by_user",
                "current_value": value,
                "evidence_path": "reports/mccarthy2018_figure_comparison/delivery_fields.json",
                "sha256": "",
                "notes": "用户于 2026-07-16 明确确认；配置驱动重建，未在 Word 中手改。",
            }
        )
    if not identity_confirmed:
        raise RuntimeError("Identity fields are populated but verification_status is not confirmed_by_user")

    by_id = {row["target_id"]: row for row in registry}
    for figure_id, evidence in COORDINATE_EVIDENCE.items():
        value = by_id[figure_id]["coordinate_system"]
        if not value or PENDING in value:
            raise RuntimeError(f"Coordinate metadata remains unresolved for Fig. {figure_id}")
        for item in evidence.split(";"):
            if not (PROJECT_ROOT / item).is_file():
                raise FileNotFoundError(item)
        rows.append(
            {
                "scope": "registry",
                "target_id": figure_id,
                "field": "coordinate_system",
                "status": "resolved_from_repository_evidence",
                "current_value": value,
                "evidence_path": evidence,
                "sha256": "",
                "notes": "只补全元数据，不提升复现等级或论文等价状态。",
            }
        )

    for row in registry:
        value = row["comparison_asset"]
        path = PROJECT_ROOT / value
        if PENDING in value or not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Invalid comparison asset for Fig. {row['target_id']}: {value}")
        rows.append(
            {
                "scope": "registry",
                "target_id": row["target_id"],
                "field": "comparison_asset",
                "status": "resolved_existing_asset",
                "current_value": value,
                "evidence_path": value,
                "sha256": sha256(path),
                "notes": "路径存在且哈希已记录。",
            }
        )

    remaining_registry = [
        f"{row['target_id']}:{field}"
        for row in registry
        for field, value in row.items()
        if value and PENDING in value
    ]
    if remaining_registry:
        raise RuntimeError(f"Unexpected registry placeholders: {remaining_registry}")
    summary = {
        "registry_rows": len(registry),
        "manual_fields": len(manual),
        "manual_fields_pending": 0,
        "manual_fields_confirmed": len(manual),
        "resolved_coordinate_fields": len(COORDINATE_EVIDENCE),
        "resolved_comparison_assets": len(registry),
        "remaining_registry_placeholders": len(remaining_registry),
        "docx_pending_occurrences": docx_text.count(PENDING),
        "pdf_pending_occurrences": pdf_text.count(PENDING),
    }
    return rows, summary


def write_manual_checklist(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    manual = [row for row in rows if row["scope"] == "cover"]
    coordinates = [row for row in rows if row["field"] == "coordinate_system"]
    lines = [
        "# 54 图报告最终人工字段检查清单",
        "",
        "状态：**PASS_IDENTITY_CONFIRMED**",
        "",
        "## 已由用户确认的封面字段",
        "",
    ]
    for row in manual:
        lines.append(f"- [x] `{row['field']}`：`{row['current_value']}`。已写入受控配置并完成重建验证。")
    lines.extend(
        [
            "",
            "变更方法：先编辑 `delivery_fields.json`，再完整重跑 Stage-G 构建；不得只在 Word 中手工替换。",
            "",
            "## 已由仓库证据补全的坐标元数据",
            "",
            "| 图号 | 状态 | 当前值 | 证据 |",
            "|---|---:|---|---|",
        ]
    )
    for row in coordinates:
        lines.append(
            f"| Fig. {row['target_id']} | resolved | {row['current_value']} | `{row['evidence_path']}` |"
        )
    lines.extend(
        [
            "",
            "## comparison panel",
            "",
            f"- 54/54 `comparison_asset` 已回写 registry，存在性与 SHA256 均通过。",
            f"- registry 中 `【待核实】`：{summary['remaining_registry_placeholders']} 项。",
            f"- DOCX/PDF 中 `【待核实】` 出现次数：{summary['docx_pending_occurrences']}/{summary['pdf_pending_occurrences']}。",
            "",
            "## 真实性边界复核",
            "",
            "- [x] 54 图仅声明工程覆盖，不声明全文严格数值等价。",
            "- [x] Chapter 4 frozen projection holdout 保持 `0/4`、`paper_projection=fail`、`paper_3d=false`。",
            "- [x] Route H physical corrected-rho 不得写成接受的一维实不变子束。",
            "- [x] 失败、boundary、diagnostic 与 proxy 行均保留。",
            "",
        ]
    )
    (REPORT_ROOT / "final_manual_fields_checklist.md").write_text("\n".join(lines), encoding="utf-8")


def strongest_results() -> dict[str, object]:
    route_rows = read_csv(PROJECT_ROOT / "data/computed/chapter3_fixed_mapping_cache_accepted_family.csv")
    fig510 = read_csv(PROJECT_ROOT / "data/computed/chapter5_fig510_bcr4bp_transfer_audit.csv")
    fig513 = read_csv(PROJECT_ROOT / "data/computed/chapter5_active_geometry_stable_manifold_tight_target_audit.csv")[0]
    fig514 = read_csv(PROJECT_ROOT / "data/computed/chapter5_active_geometry_leo_transfer_audit.csv")[0]
    return {
        "route_h_max_abs_z_km": max(float(row["max_abs_z_km"]) for row in route_rows),
        "route_h_max_map_residual": max(float(row["map_residual_norm"]) for row in route_rows),
        "fig510_numerical_acceptance": sum(row["numerical_acceptance"].lower() == "true" for row in fig510),
        "fig510_paper_equivalence": sum(row["paper_equivalence"].lower() == "true" for row in fig510),
        "fig510_independent_endpoint_max_km": max(float(row["independent_endpoint_error_km"]) for row in fig510),
        "fig513_best_periapsis_km": float(fig513["best_7033_radius_km"]),
        "fig513_error_km": float(fig513["best_7033_error_km"]),
        "fig513_trajectories": int(fig513["manifold_trajectories"]),
        "fig514_periapsis_km": float(fig514["periapsis_radius_km"]),
        "fig514_transfer_days": float(fig514["transfer_time_days"]),
    }


def build_one_page_pdf(validation: dict[str, object], output: Path) -> None:
    results = strongest_results()
    regular = FontProperties(fname="C:/Windows/Fonts/msyh.ttc")
    bold = FontProperties(fname="C:/Windows/Fonts/msyhbd.ttc")
    fig = plt.figure(figsize=(8.27, 11.69), dpi=180, facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.add_patch(plt.Rectangle((0.055, 0.945), 0.89, 0.008, color="#2f6f52", transform=ax.transAxes))
    ax.text(0.065, 0.915, "McCarthy（2018）54图复现情况一页说明", fontproperties=bold, fontsize=18, color="#1f3f31")
    ax.text(0.935, 0.918, date.today().isoformat(), fontproperties=regular, fontsize=8.5, ha="right", color="#5f6b64")
    y = 0.875

    def section(title: str, bullets: list[str]) -> None:
        nonlocal y
        ax.text(0.07, y, title, fontproperties=bold, fontsize=11.5, color="#2f6f52", va="top")
        y -= 0.027
        for bullet in bullets:
            wrapped = textwrap.wrap(bullet, width=54, break_long_words=True, break_on_hyphens=False) or [""]
            for index, line in enumerate(wrapped):
                prefix = "• " if index == 0 else "  "
                ax.text(0.085, y, prefix + line, fontproperties=regular, fontsize=9.2, color="#202724", va="top")
                y -= 0.0225
            y -= 0.006
        y -= 0.006

    grades = validation["grades"]
    section(
        "已完成的核心工作",
        [
            "原论文图、当前复现图和统一 comparison panel 均为 54/54；每图均绑定脚本、数据、等级、差异和限制。",
            "Word/PDF 已重新构建并通过结构、内容、图题、证据表、目录、页码、清晰度和跨引擎检查。",
        ],
    )
    section(
        "复现等级与证据状态",
        [
            f"A/B/C/D={grades['A']}/{grades['B']}/{grades['C']}/{grades['D']}；A 级只表示当前项目门槛内定量通过，不代表原作者节点逐点等价。",
            "总体结论是完整工程覆盖，而非整篇学位论文的严格数值等价。",
        ],
    )
    section(
        "代表性数值证据",
        [
            f"Route H 接受源层最大 |z|={results['route_h_max_abs_z_km']:.6f} km，最大映射残差={results['route_h_max_map_residual']:.3e}。",
            f"Fig. 5.10 项目 BCR4BP 扩展数值接受={results['fig510_numerical_acceptance']}/2，独立端点误差≤{results['fig510_independent_endpoint_max_km']:.3e} km；论文等价={results['fig510_paper_equivalence']}/2。",
            f"Fig. 5.13 的 162 条稳定流形轨迹给出 7033-km 目标近地点 {results['fig513_best_periapsis_km']:.6f} km（误差 {results['fig513_error_km']:.6f} km）。",
        ],
    )
    section(
        "主要客观限制",
        [
            "Chapter 4 frozen projection holdout 保持 0/4、paper_projection=fail、paper_3d=false；后验诊断不进入冻结验收。",
            "原论文多处缺少完整状态、分支节点、相位、投影和优化约束；proxy、diagnostic、boundary 与失败行均未删除。",
            "封面姓名、单位、导师已由用户确认；六项可核实坐标元数据已按脚本和数据补全，但未提升任何复现等级。",
        ],
    )
    section(
        "建议导师优先审阅",
        [
            "确认工程覆盖与严格等价的表述边界；抽查 Chapter 3 Route H、Chapter 4 冻结投影失败和 Chapter 5 BCR4BP/流形代表案例。",
            "抽查封面三项身份信息与受控配置一致。本页只报告当前复现事实，不展开 invariant-bundle 论文计划。",
        ],
    )
    if y < 0.055:
        raise RuntimeError(f"One-page summary overflow: y={y}")
    ax.add_patch(plt.Rectangle((0.055, 0.045), 0.89, 0.002, color="#9ab7a7", transform=ax.transAxes))
    ax.text(0.065, 0.026, "内部导师审阅材料｜权威状态以当前 CSV、NPZ 与冻结门槛为准", fontproperties=regular, fontsize=7.8, color="#68736c")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output,
        format="pdf",
        bbox_inches=None,
        metadata={"Title": "McCarthy 2018 54图复现情况一页说明", "Creator": "Stage-G audited builder"},
    )
    plt.close(fig)
    if len(PdfReader(output).pages) != 1:
        raise RuntimeError("One-page summary is not exactly one PDF page")


def write_adviser_focus() -> None:
    text = """# 导师审阅重点

## 建议先看

1. 报告总论与结论是否始终区分“54 图工程覆盖”和“全文严格数值等价”。
2. Chapter 3 的 Route H source-layer 证据及 q=8 boundary 是否表述准确。
3. Chapter 4 frozen projection holdout 是否明确保持 `0/4`、`paper_projection=fail`、`paper_3d=false`。
4. Chapter 5 的 Fig. 5.10 是否只声明项目 BCR4BP 数值扩展，并保留 `paper_equivalence=0/2`。
5. A/B/C/D=`7/30/5/12` 的等级解释、54 组证据表和失败/代理案例是否足够便于快速抽查。

## 已确认的交付字段

- 姓名：兀文昊；单位：中国科学院大学；导师：张晨。
- 三项信息已写入 `reports/mccarthy2018_figure_comparison/delivery_fields.json` 并通过完整重建进入 Word/PDF。

## 不应升级的结论

- 不声明整篇 McCarthy（2018）已严格数值等价复现。
- 不把后验 Chapter 4 诊断改写为冻结 holdout 通过。
- 不删除 boundary、diagnostic、proxy 或 negative-control 结果。
- 本交付包只报告当前复现事实，不展开原创论文计划。
"""
    (ADVISER_ROOT / FOCUS_NAME).write_text(text, encoding="utf-8")


def artifact_paths() -> list[Path]:
    mutable_stage_g_names = {
        "artifact_hashes.csv",
        "stage_g_acceptance_hashes.json",
        "stage_g_acceptance_log.txt",
        "stage_g_acceptance_status.json",
        "stage_g_execution_log.txt",
        "stage_g_run_config.json",
    }
    paths = [
        REPORT_ROOT / DOCX_NAME,
        REPORT_ROOT / PDF_NAME,
        REPORT_ROOT / "delivery_fields.json",
        REPORT_ROOT / "figure_comparison_registry.csv",
        REPORT_ROOT / "comparison_panel_manifest.csv",
        REPORT_ROOT / "final_manual_fields_checklist.md",
        REPORT_ROOT / "final_placeholder_audit.csv",
        REPORT_ROOT / "document_build_log.md",
        REPORT_ROOT / "review_checklist.md",
        ADVISER_ROOT / DOCX_NAME,
        ADVISER_ROOT / PDF_NAME,
        ADVISER_ROOT / ONE_PAGE_NAME,
        ADVISER_ROOT / FOCUS_NAME,
    ]
    if STAGE_G.is_dir():
        paths.extend(
            path
            for path in STAGE_G.rglob("*")
            if path.is_file() and path.name not in mutable_stage_g_names
        )
    return sorted(set(paths), key=lambda path: relative(path))


def write_artifact_hashes() -> None:
    rows = []
    for path in artifact_paths():
        if not path.is_file():
            continue
        mode, canonical = canonical_artifact(path)
        rows.append(
            {
                "path": relative(path),
                "source_bytes": path.stat().st_size,
                "hash_mode": mode,
                "canonical_bytes": len(canonical),
                "sha256": hashlib.sha256(canonical).hexdigest(),
            }
        )
    write_csv(
        STAGE_G / "artifact_hashes.csv",
        rows,
        ["path", "source_bytes", "hash_mode", "canonical_bytes", "sha256"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hash-only", action="store_true")
    args = parser.parse_args()
    STAGE_G.mkdir(parents=True, exist_ok=True)
    ADVISER_ROOT.mkdir(parents=True, exist_ok=True)
    if args.hash_only:
        write_artifact_hashes()
        print(f"stage_g_hashes=PASS rows={len(read_csv(STAGE_G / 'artifact_hashes.csv'))}")
        return 0

    validation_path = STAGE_G / "delivery_validation.json"
    if not validation_path.is_file():
        raise FileNotFoundError(validation_path)
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if validation.get("status") != "PASS":
        raise RuntimeError(f"Delivery validation did not pass: {validation.get('status')}")

    rows, summary = build_placeholder_audit()
    write_csv(
        REPORT_ROOT / "final_placeholder_audit.csv",
        rows,
        ["scope", "target_id", "field", "status", "current_value", "evidence_path", "sha256", "notes"],
    )
    write_manual_checklist(rows, summary)

    source_docx = REPORT_ROOT / DOCX_NAME
    source_pdf = REPORT_ROOT / PDF_NAME
    shutil.copy2(source_docx, ADVISER_ROOT / DOCX_NAME)
    shutil.copy2(source_pdf, ADVISER_ROOT / PDF_NAME)
    build_one_page_pdf(validation, ADVISER_ROOT / ONE_PAGE_NAME)
    write_adviser_focus()

    preview_pdf = fitz.open(ADVISER_ROOT / ONE_PAGE_NAME)
    try:
        pixmap = preview_pdf[0].get_pixmap(dpi=150, alpha=False)
        pixmap.save(STAGE_G / "one_page_summary_preview.png")
    finally:
        preview_pdf.close()

    package_config = {
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation": relative(validation_path),
        "placeholder_summary": summary,
        "delivery_files": [
            relative(ADVISER_ROOT / DOCX_NAME),
            relative(ADVISER_ROOT / PDF_NAME),
            relative(ADVISER_ROOT / ONE_PAGE_NAME),
            relative(ADVISER_ROOT / FOCUS_NAME),
        ],
        "truth_boundaries": {
            "engineering_coverage_not_strict_equivalence": True,
            "chapter4_frozen_projection_holdout": "0/4",
            "chapter4_paper_projection": "fail",
            "chapter4_paper_3d": False,
        },
    }
    (STAGE_G / "stage_g_delivery_config.json").write_text(
        json.dumps(package_config, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_artifact_hashes()
    print(
        "stage_g_package=PASS "
        f"manual={summary['manual_fields']} coordinates={summary['resolved_coordinate_fields']} "
        f"panels={summary['resolved_comparison_assets']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
