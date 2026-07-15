#!/usr/bin/env python3
"""Validate the final McCarthy 54-figure DOCX/PDF against the project registry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
NS = {"w": W_NS, "a": A_NS, "m": M_NS}
PENDING = "【待核实】"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def word_text(root: ET.Element) -> str:
    return "".join(node.text or "" for node in root.findall(".//w:t", NS))


def figure_token_present(text: str, figure_id: str) -> bool:
    return re.search(rf"Fig\.\s*{re.escape(figure_id)}(?!\d)", text) is not None


def add_check(checks: dict[str, dict[str, object]], name: str, passed: bool, detail: object) -> None:
    checks[name] = {"pass": bool(passed), "detail": detail}


def inspect_docx(path: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        names = archive.namelist()
        document_bytes = archive.read("word/document.xml")
        document_root = ET.fromstring(document_bytes)
        document_text = word_text(document_root)
        styles_root = ET.fromstring(archive.read("word/styles.xml"))
        style_names: dict[str, str] = {}
        for style in styles_root.findall("./w:style", NS):
            style_id = style.get(f"{{{W_NS}}}styleId", "")
            name = style.find("./w:name", NS)
            style_names[style_id] = "" if name is None else name.get(f"{{{W_NS}}}val", "")
        heading_style_ids = {
            style_id for style_id, name in style_names.items() if name.lower().startswith("heading ")
        }
        instruction_text = " ".join(
            node.text or "" for node in document_root.findall(".//w:instrText", NS)
        )
        footer_instruction = ""
        for name in names:
            if name.startswith("word/footer") and name.endswith(".xml"):
                footer = ET.fromstring(archive.read(name))
                footer_instruction += " ".join(
                    node.text or "" for node in footer.findall(".//w:instrText", NS)
                )
        paragraph_styles: Counter[str] = Counter()
        numbered_headings = 0
        for paragraph in document_root.findall(".//w:p", NS):
            style = paragraph.find("./w:pPr/w:pStyle", NS)
            if style is not None:
                value = style.get(f"{{{W_NS}}}val", "")
                paragraph_styles[value] += 1
                if value in heading_style_ids and paragraph.find("./w:pPr/w:numPr", NS) is not None:
                    numbered_headings += 1
        media = [
            name
            for name in names
            if name.startswith("word/media/") and not name.endswith("/")
        ]
        result.update(
            {
                "zip_test_member": bad_member,
                "package_member_count": len(names),
                "media_count": len(media),
                "media_files": media,
                "drawing_count": len(document_root.findall(".//w:drawing", NS)),
                "blip_count": len(document_root.findall(".//a:blip", NS)),
                "table_count": len(document_root.findall(".//w:tbl", NS)),
                "math_count": len(document_root.findall(".//m:oMath", NS)),
                "math_paragraph_count": len(document_root.findall(".//m:oMathPara", NS)),
                "paragraph_styles": dict(paragraph_styles),
                "heading_style_ids": sorted(heading_style_ids),
                "numbered_heading_count": numbered_headings,
                "toc_field": "TOC" in instruction_text.upper(),
                "page_field": "PAGE" in footer_instruction.upper(),
                "text": document_text,
                "instruction_text": instruction_text,
            }
        )
    return result


def inspect_pdf(path: Path) -> dict[str, object]:
    document = fitz.open(path)
    page_records: list[dict[str, object]] = []
    texts: list[str] = []
    for index, page in enumerate(document):
        text = page.get_text("text")
        texts.append(text)
        images = page.get_images(full=True)
        drawings = page.get_drawings()
        page_records.append(
            {
                "page": index + 1,
                "text_characters": len(text.strip()),
                "image_count": len(images),
                "drawing_count": len(drawings),
                "width_pt": page.rect.width,
                "height_pt": page.rect.height,
            }
        )
    document.close()
    blank_pages = [
        item["page"]
        for item in page_records
        if item["text_characters"] < 5
        and item["image_count"] == 0
        and item["drawing_count"] == 0
    ]
    sparse_text_pages = [
        item["page"]
        for item in page_records
        if item["text_characters"] < 80 and item["image_count"] == 0
    ]
    return {
        "page_count": len(page_records),
        "page_records": page_records,
        "blank_pages": blank_pages,
        "sparse_text_pages": sparse_text_pages,
        "text": "\n".join(texts),
    }


def build_markdown(result: dict[str, object]) -> str:
    checks = result["checks"]
    lines = [
        f"# {result['label']} 报告自动审计",
        "",
        f"- 状态：**{result['status']}**",
        f"- 生成时间：`{result['generated_at_utc']}`",
        f"- DOCX：`{result['docx']['path']}`",
        f"- PDF：`{result['pdf']['path']}`",
        f"- PDF 页数：{result['pdf']['page_count']}",
        f"- 图号覆盖：DOCX {result['coverage']['docx_figure_ids']}/54；PDF {result['coverage']['pdf_figure_ids']}/54",
        "",
        "## 门槛检查",
        "",
        "| 检查项 | 结果 | 细节 |",
        "|---|---:|---|",
    ]
    for name, item in checks.items():
        detail = json.dumps(item["detail"], ensure_ascii=False)
        if len(detail) > 260:
            detail = detail[:257] + "..."
        lines.append(f"| {name} | {'PASS' if item['pass'] else 'FAIL'} | `{detail}` |")
    lines.extend(
        [
            "",
            "## 版面提示",
            "",
            f"- 空白页：{result['pdf']['blank_pages'] or '无'}",
            f"- 低文本且无位图页（需结合矢量内容人工复核）：{result['pdf']['sparse_text_pages'] or '无'}",
            f"- `【待核实】`：registry 字段 {result['pending']['registry_field_count']} 项；DOCX 文本 {result['pending']['docx_occurrences']} 处；PDF 文本 {result['pending']['pdf_occurrences']} 处。",
            "",
            "说明：自动审计验证结构、覆盖、字段、错误字符串和空白页；分页美观与图片可读性仍须结合渲染总览人工复核。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--label", default="阶段E预验收")
    args = parser.parse_args()

    root = args.report_root.resolve()
    output_dir = (args.output_dir or root / "stage_e").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    docx_path = root / "McCarthy2018_54图逐图复现对照报告.docx"
    pdf_path = root / "McCarthy2018_54图逐图复现对照报告.pdf"
    registry_path = root / "figure_comparison_registry.csv"
    metrics_path = root / "quantitative_metrics_registry.csv"
    source_manifest_path = root / "source_figure_manifest.csv"
    reproduction_manifest_path = root / "reproduction_figure_manifest.csv"
    comparison_manifest_path = root / "comparison_panel_manifest.csv"

    required = [
        docx_path,
        pdf_path,
        registry_path,
        metrics_path,
        source_manifest_path,
        reproduction_manifest_path,
        comparison_manifest_path,
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing required files: " + "; ".join(missing))

    registry = read_csv(registry_path)
    metrics = read_csv(metrics_path)
    source_manifest = read_csv(source_manifest_path)
    reproduction_manifest = read_csv(reproduction_manifest_path)
    comparison_manifest = read_csv(comparison_manifest_path)
    figure_ids = [row["target_id"] for row in registry]
    docx = inspect_docx(docx_path)
    pdf = inspect_pdf(pdf_path)
    docx_text = str(docx.pop("text"))
    pdf_text = str(pdf.pop("text"))

    docx_ids = [figure_id for figure_id in figure_ids if figure_token_present(docx_text, figure_id)]
    pdf_ids = [figure_id for figure_id in figure_ids if figure_token_present(pdf_text, figure_id)]
    required_registry_fields = [
        "target_id",
        "paper_asset",
        "reproduction_asset",
        "comparison_asset",
        "research_object",
        "model",
        "numerical_method",
        "script",
        "data_source",
        "status",
        "quantitative_validation",
        "consistency_cn",
        "difference_cn",
        "limitation_cn",
        "reproduction_grade",
    ]
    empty_registry_fields = [
        f"{row.get('target_id', '?')}:{field}"
        for row in registry
        for field in required_registry_fields
        if not row.get(field, "").strip()
    ]
    missing_assets = []
    for row in registry:
        for field in ("paper_asset", "reproduction_asset", "comparison_asset"):
            value = row.get(field, "").strip()
            candidate_paths = (
                (root / value).resolve(),
                (root.parents[1] / value).resolve(),
            ) if value else (Path("__missing__"),)
            if not any(path.is_file() for path in candidate_paths):
                missing_assets.append(f"{row['target_id']}:{field}:{value}")
    pending_fields = [
        {"target_id": row["target_id"], "field": field, "value": value}
        for row in registry
        for field, value in row.items()
        if value and PENDING in value
    ]
    grade_counts = Counter(row["reproduction_grade"] for row in registry)
    status_counts = Counter(row["status"] for row in registry)
    metric_rows_by_id: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in metrics:
        metric_rows_by_id[row["target_id"]].append(row)
    core_ids = sorted({row["target_id"] for row in metrics if row["priority_core"].lower() == "true"})
    core_failures = [
        figure_id
        for figure_id in core_ids
        if len(metric_rows_by_id[figure_id]) < 2
        or any(not row["project_result"].strip() for row in metric_rows_by_id[figure_id])
    ]
    bad_strings = [
        "MERGEFORMAT",
        "Error! Reference source not found",
        "Error! Bookmark not defined",
        "错误!未找到引用源",
        "错误!未定义书签",
    ]
    bad_docx = [token for token in bad_strings if token.lower() in docx_text.lower()]
    bad_pdf = [token for token in bad_strings if token.lower() in pdf_text.lower()]

    checks: dict[str, dict[str, object]] = {}
    add_check(checks, "DOCX ZIP 可读", docx["zip_test_member"] is None, docx["zip_test_member"])
    add_check(checks, "registry 54 行且图号唯一", len(registry) == 54 and len(set(figure_ids)) == 54, {"rows": len(registry), "unique": len(set(figure_ids))})
    add_check(checks, "三份资产 manifest 均为 54 行", all(len(rows) == 54 for rows in (source_manifest, reproduction_manifest, comparison_manifest)), {"source": len(source_manifest), "reproduced": len(reproduction_manifest), "comparison": len(comparison_manifest)})
    add_check(checks, "registry 必填字段完整", not empty_registry_fields, empty_registry_fields)
    add_check(checks, "registry 三类资产路径有效", not missing_assets, missing_assets)
    add_check(checks, "DOCX 54 图号覆盖", len(docx_ids) == 54, {"count": len(docx_ids), "missing": sorted(set(figure_ids) - set(docx_ids))})
    add_check(checks, "PDF 54 图号覆盖", len(pdf_ids) == 54, {"count": len(pdf_ids), "missing": sorted(set(figure_ids) - set(pdf_ids))})
    add_check(checks, "DOCX 54 张嵌入图", docx["media_count"] == 54 and docx["drawing_count"] == 54 and docx["blip_count"] == 54, {"media": docx["media_count"], "drawing": docx["drawing_count"], "blip": docx["blip_count"]})
    add_check(checks, "DOCX 54 个中文逐图图题", docx_text.count("McCarthy 原文结果与本文复现结果对照") == 54, docx_text.count("McCarthy 原文结果与本文复现结果对照"))
    add_check(checks, "DOCX 54 个英文逐图图题", docx_text.count("Comparison between the original result of McCarthy") == 54, docx_text.count("Comparison between the original result of McCarthy"))
    add_check(checks, "PDF 54 个中文逐图图题", pdf_text.count("McCarthy 原文结果与本文复现结果对照") == 54, pdf_text.count("McCarthy 原文结果与本文复现结果对照"))
    add_check(checks, "PDF 54 个英文逐图图题", pdf_text.count("Comparison between the original result of McCarthy") == 54, pdf_text.count("Comparison between the original result of McCarthy"))
    add_check(checks, "核心数值图 28 张且指标完整", len(core_ids) == 28 and not core_failures, {"core_ids": len(core_ids), "failures": core_failures})
    add_check(checks, "自动目录字段存在", bool(docx["toc_field"]), docx["instruction_text"])
    add_check(checks, "页码字段存在", bool(docx["page_field"]), docx["page_field"])
    add_check(checks, "标题自动编号存在", docx["numbered_heading_count"] >= 60, docx["numbered_heading_count"])
    add_check(checks, "公式对象与式号完整", docx["math_count"] >= 6 and all(f"({number})" in docx_text for number in range(1, 7)), {"math": docx["math_count"], "math_paragraphs": docx["math_paragraph_count"]})
    labelled_tables = sum(f"Table {number} " in docx_text for number in range(1, 117))
    add_check(checks, "表格与双语编号符合构建记录", docx["table_count"] == 121 and labelled_tables == 116, {"table_objects": docx["table_count"], "labelled_tables": labelled_tables})
    add_check(checks, "无 Word 域错误或 MERGEFORMAT 泄漏", not bad_docx and not bad_pdf, {"docx": bad_docx, "pdf": bad_pdf})
    add_check(checks, "PDF 无真正空白页", not pdf["blank_pages"], pdf["blank_pages"])
    add_check(checks, "PDF 无近空白孤页", not pdf["sparse_text_pages"], pdf["sparse_text_pages"])
    export_status_path = root / "stage_e" / "pdf_export_status.json"
    export_page_count = None
    if export_status_path.is_file():
        export_page_count = json.loads(export_status_path.read_text(encoding="utf-8"))["pdf_pages"]
    page_count_ok = 100 <= pdf["page_count"] <= 160 and (
        export_page_count is None or pdf["page_count"] == export_page_count
    )
    add_check(checks, "PDF 页数与 Word 导出状态一致", page_count_ok, {"pdf": pdf["page_count"], "export_status": export_page_count})
    add_check(checks, "待核实字段集中且未被消隐", len(pending_fields) == 6 and docx_text.count(PENDING) >= 6 and pdf_text.count(PENDING) >= 6, {"registry_fields": len(pending_fields), "docx": docx_text.count(PENDING), "pdf": pdf_text.count(PENDING)})
    add_check(checks, "等级统计符合审计", grade_counts == Counter({"A": 7, "B": 30, "C": 5, "D": 12}), dict(grade_counts))
    add_check(checks, "证据状态统计符合审计", status_counts == Counter({"accepted": 7, "boundary": 30, "diagnostic": 5, "proxy": 12}), dict(status_counts))

    status = "PASS" if all(item["pass"] for item in checks.values()) else "FAIL"
    result = {
        "label": args.label,
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report_root": str(root),
        "docx": {"path": str(docx_path), "bytes": docx_path.stat().st_size, "sha256": sha256(docx_path), **docx},
        "pdf": {"path": str(pdf_path), "bytes": pdf_path.stat().st_size, "sha256": sha256(pdf_path), **pdf},
        "coverage": {"registry": len(registry), "docx_figure_ids": len(docx_ids), "pdf_figure_ids": len(pdf_ids)},
        "grades": dict(grade_counts),
        "statuses": dict(status_counts),
        "pending": {"registry_field_count": len(pending_fields), "items": pending_fields, "docx_occurrences": docx_text.count(PENDING), "pdf_occurrences": pdf_text.count(PENDING)},
        "checks": checks,
    }
    slug = re.sub(r"[^0-9A-Za-z_-]+", "_", args.label).strip("_") or "validation"
    json_path = output_dir / f"{slug}_validation.json"
    md_path = output_dir / f"{slug}_validation.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(result), encoding="utf-8")
    print(f"final_report_validation={status} checks={len(checks)} pages={pdf['page_count']} docx_figures={len(docx_ids)} pdf_figures={len(pdf_ids)}")
    print(json_path)
    print(md_path)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
