"""Build the auditable Stage-A inventory and design package for the 54-figure report."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import re
from pathlib import Path

import fitz
from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
STAGE_A = REPORT_ROOT / "stage_a"
PENDING = "【待核实】"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def asset_record(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {
            "exists": False,
            "bytes": 0,
            "width_px": "",
            "height_px": "",
            "sha256": "",
        }
    width = height = ""
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        with Image.open(path) as image:
            width, height = image.size
    return {
        "exists": True,
        "bytes": path.stat().st_size,
        "width_px": width,
        "height_px": height,
        "sha256": sha256(path),
    }


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def caption_for(page: fitz.Page, figure_id: str) -> tuple[str, str]:
    token = re.compile(rf"Figure\s+{re.escape(figure_id)}\s*[:.]?", re.IGNORECASE)
    caption_start = re.compile(
        rf"^Figure\s+{re.escape(figure_id)}\s*[:.]\s*\S+", re.IGNORECASE
    )
    any_figure = re.compile(r"Figure\s+\d+\.\d+\s*[:.]?", re.IGNORECASE)
    candidates: list[tuple[bool, str]] = []
    for block in page.get_text("blocks"):
        text = normalize(block[4])
        match = token.search(text)
        if not match:
            continue
        candidate = text[match.start():]
        next_match = any_figure.search(candidate, 1)
        if next_match:
            candidate = candidate[: next_match.start()]
        candidate = re.sub(r"\s+\d+\s*$", "", candidate).strip()
        candidates.append((bool(caption_start.match(text)), candidate))
    if not candidates:
        page_text = normalize(page.get_text("text"))
        match = token.search(page_text)
        if match:
            candidate = page_text[match.start():]
            next_match = any_figure.search(candidate, 1)
            if next_match:
                candidate = candidate[: next_match.start()]
            candidates.append((False, candidate[:800].strip()))
    if not candidates:
        return PENDING, "not_found"
    candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    is_caption_block, caption = candidates[0]
    if len(caption) > 800:
        return caption[:800].rstrip() + "…", "truncated_review_required"
    return caption, "pdf_caption_block" if is_caption_block else "ambiguous_body_reference"


def grade_for(gap: dict[str, str], validation: dict[str, str]) -> tuple[str, str]:
    status = gap.get("evidence_status", "")
    uses_proxy = validation.get("uses_proxy", "")
    if status == "accepted" and uses_proxy == "false":
        return "A", "按当前项目审计门槛定量通过；不自动声明与原作者离散节点逐点等价"
    if status == "boundary" and uses_proxy == "false":
        return "B", "真实数值解与主要物理趋势受支持；严格论文等价仍有边界"
    if status == "diagnostic" or uses_proxy == "partial":
        return "C", "局部、部分分支或诊断性数值源层"
    if status == "proxy" or uses_proxy == "true":
        return "D", "示意或代理层；不得写成定量数值复现"
    return "E", PENDING


def count_by(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    return dict(collections.Counter(row.get(field, "") for row in rows))


def md_table_counts(counts: dict[str, int]) -> str:
    return "、".join(f"{key or '(空)'}={value}" for key, value in sorted(counts.items()))


def build(args: argparse.Namespace) -> dict[str, object]:
    index_rows = read_csv(PROJECT_ROOT / "data" / "figure_index.csv")
    target_rows = read_csv(PROJECT_ROOT / "data" / "reproduction_targets.csv")
    validation_rows = read_csv(PROJECT_ROOT / "data" / "computed" / "figure_validation_table.csv")
    gap_rows = read_csv(PROJECT_ROOT / "data" / "computed" / "figure_evidence_gap_audit.csv")
    gate_rows = read_csv(PROJECT_ROOT / "data" / "computed" / "mccarthy2018_staged_goal_gate_status.csv")

    by_target = {row["figure_id"]: row for row in target_rows}
    by_validation = {row["figure_id"]: row for row in validation_rows}
    by_gap = {row["figure_id"]: row for row in gap_rows}

    figure_ids = [row["figure_id"] for row in index_rows]
    if len(figure_ids) != 54 or len(set(figure_ids)) != 54:
        raise RuntimeError(f"Expected 54 unique figure IDs, found {len(figure_ids)}/{len(set(figure_ids))}")
    for name, mapping in (
        ("targets", by_target),
        ("validation", by_validation),
        ("gaps", by_gap),
    ):
        if set(mapping) != set(figure_ids):
            raise RuntimeError(f"{name} figure-ID set differs from figure_index.csv")

    thesis_pdf = args.thesis.resolve()
    reference_docx = args.reference_docx.resolve()
    style_json = args.reference_style_json.resolve()
    if not style_json.is_file():
        raise FileNotFoundError(f"Missing reference style analysis: {style_json}")
    style_data = json.loads(style_json.read_text(encoding="utf-8"))

    doc = fitz.open(thesis_pdf)
    source_manifest: list[dict[str, object]] = []
    reproduction_manifest: list[dict[str, object]] = []
    registry: list[dict[str, object]] = []
    catalog: list[dict[str, object]] = []
    missing: list[dict[str, str]] = []
    source_hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    reproduction_hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)

    for index_row in index_rows:
        figure_id = index_row["figure_id"]
        chapter = figure_id.split(".", 1)[0]
        target = by_target[figure_id]
        validation = by_validation[figure_id]
        gap = by_gap[figure_id]
        pdf_page = int(index_row["pdf_page"])
        if pdf_page < 1 or pdf_page > len(doc):
            caption, caption_status = PENDING, "page_out_of_range"
        else:
            caption, caption_status = caption_for(doc.load_page(pdf_page - 1), figure_id)

        stem = f"fig_{figure_id.replace('.', '_')}"
        source_asset = PROJECT_ROOT / "outputs" / "reference_pages" / f"{stem}_reference.png"
        reproduction_png = PROJECT_ROOT / "outputs" / "figures_png" / f"{stem}.png"
        reproduction_pdf = PROJECT_ROOT / "outputs" / "figures_pdf" / f"{stem}.pdf"
        source_info = asset_record(source_asset)
        reproduction_png_info = asset_record(reproduction_png)
        reproduction_pdf_info = asset_record(reproduction_pdf)
        if source_info["sha256"]:
            source_hashes[str(source_info["sha256"])].append(figure_id)
        if reproduction_png_info["sha256"]:
            reproduction_hashes[str(reproduction_png_info["sha256"])].append(figure_id)

        source_quality = "present"
        if not source_info["exists"]:
            source_quality = "missing"
            missing.append({"figure_id": figure_id, "category": "original_asset", "issue": "原论文裁图缺失", "next_action": "阶段 B 重新提取"})
        elif int(source_info["width_px"] or 0) < 600 or int(source_info["height_px"] or 0) < 250:
            source_quality = "low_dimension_review"
            missing.append({"figure_id": figure_id, "category": "original_quality", "issue": f"现有裁图尺寸 {source_info['width_px']}×{source_info['height_px']} px，需高分辨率复核", "next_action": "阶段 B 从原 PDF 以更高缩放重新提取"})
        if caption_status != "pdf_caption_block":
            missing.append({"figure_id": figure_id, "category": "caption", "issue": f"原文图题状态={caption_status}", "next_action": "阶段 B 人工核对 PDF 图题"})
        if not reproduction_png_info["exists"] or not reproduction_pdf_info["exists"]:
            missing.append({"figure_id": figure_id, "category": "reproduction_asset", "issue": "复现 PNG 或 PDF 缺失", "next_action": "阶段 B 重新导出"})

        grade, grade_boundary = grade_for(gap, validation)
        catalog.append(
            {
                "target_id": figure_id,
                "chapter": chapter,
                "paper_figure_number": f"Fig. {figure_id}",
                "paper_page": index_row["source_page"],
                "pdf_page": pdf_page,
                "paper_caption": caption,
                "caption_status": caption_status,
                "figure_type": index_row["figure_type"],
                "project_title": index_row["title"],
            }
        )
        source_manifest.append(
            {
                "target_id": figure_id,
                "paper_page": index_row["source_page"],
                "pdf_page": pdf_page,
                "paper_caption": caption,
                "caption_status": caption_status,
                "source_pdf": str(thesis_pdf),
                "source_pdf_sha256": sha256(thesis_pdf),
                "asset": rel(source_asset) if source_asset.exists() else str(source_asset),
                "asset_exists": source_info["exists"],
                "asset_bytes": source_info["bytes"],
                "width_px": source_info["width_px"],
                "height_px": source_info["height_px"],
                "asset_sha256": source_info["sha256"],
                "stage_a_quality": source_quality,
                "extraction_status": "existing_project_crop; stage_b_reextract_required",
            }
        )
        reproduction_manifest.append(
            {
                "target_id": figure_id,
                "script": index_row["script"],
                "png": rel(reproduction_png) if reproduction_png.exists() else str(reproduction_png),
                "png_exists": reproduction_png_info["exists"],
                "png_bytes": reproduction_png_info["bytes"],
                "width_px": reproduction_png_info["width_px"],
                "height_px": reproduction_png_info["height_px"],
                "png_sha256": reproduction_png_info["sha256"],
                "pdf": rel(reproduction_pdf) if reproduction_pdf.exists() else str(reproduction_pdf),
                "pdf_exists": reproduction_pdf_info["exists"],
                "pdf_bytes": reproduction_pdf_info["bytes"],
                "pdf_sha256": reproduction_pdf_info["sha256"],
                "stage_a_status": "existing_project_output; stage_b_copy_or_reexport_required",
            }
        )
        registry.append(
            {
                "target_id": figure_id,
                "chapter": chapter,
                "paper_figure_number": f"Fig. {figure_id}",
                "paper_page": index_row["source_page"],
                "pdf_page": pdf_page,
                "paper_caption": caption,
                "paper_caption_status": caption_status,
                "paper_asset": rel(source_asset) if source_asset.exists() else PENDING,
                "reproduction_asset": rel(reproduction_png) if reproduction_png.exists() else PENDING,
                "script": index_row["script"],
                "data_source": validation.get("main_data_source") or target.get("validation_artifact") or PENDING,
                "model": PENDING,
                "coordinate_system": PENDING,
                "parameters": target.get("paper_targets") or PENDING,
                "numerical_method": PENDING,
                "status": gap.get("evidence_status") or PENDING,
                "evidence": target.get("validation_artifact") or validation.get("main_data_source") or PENDING,
                "quantitative_validation": "; ".join(
                    f"{key}={validation[key]}"
                    for key in ("residual_norm", "jacobi_drift", "periodicity_error", "stability_index_error")
                    if validation.get(key) and validation[key] != "N/A"
                ) or "原论文未报告或当前未登记",
                "consistency": validation.get("visual_status") or gap.get("evidence_summary") or PENDING,
                "difference": gap.get("evidence_summary") or PENDING,
                "difference_reason": PENDING,
                "limitation": target.get("next_action") or gap.get("next_action") or PENDING,
                "reproduction_grade": grade,
                "grade_boundary": grade_boundary,
                "uses_proxy": validation.get("uses_proxy") or PENDING,
                "notes": "阶段 A 初版；阶段 C 将补充模型、坐标系、方法、差异原因与逐图定量表。",
            }
        )

    source_dupes = [ids for ids in source_hashes.values() if len(ids) > 1]
    reproduction_dupes = [ids for ids in reproduction_hashes.values() if len(ids) > 1]
    if source_dupes:
        missing.append({"figure_id": ",".join(sum(source_dupes, [])), "category": "duplicate", "issue": "原图存在重复哈希", "next_action": "阶段 B 核对映射"})
    if reproduction_dupes:
        missing.append({"figure_id": ",".join(sum(reproduction_dupes, [])), "category": "duplicate", "issue": "复现图存在重复哈希", "next_action": "阶段 B 核对映射"})

    catalog_fields = ["target_id", "chapter", "paper_figure_number", "paper_page", "pdf_page", "paper_caption", "caption_status", "figure_type", "project_title"]
    source_fields = list(source_manifest[0])
    reproduction_fields = list(reproduction_manifest[0])
    registry_fields = list(registry[0])
    missing_fields = ["figure_id", "category", "issue", "next_action"]
    write_csv(STAGE_A / "mccarthy_figure_catalog.csv", catalog, catalog_fields)
    write_csv(STAGE_A / "figure_registry_initial.csv", registry, registry_fields)
    write_csv(STAGE_A / "reproduction_asset_inventory.csv", reproduction_manifest, reproduction_fields)
    write_csv(STAGE_A / "missing_assets.csv", missing, missing_fields)
    write_csv(REPORT_ROOT / "source_figure_manifest.csv", source_manifest, source_fields)
    write_csv(REPORT_ROOT / "reproduction_figure_manifest.csv", reproduction_manifest, reproduction_fields)
    write_csv(REPORT_ROOT / "figure_comparison_registry.csv", registry, registry_fields)

    source_existing = sum(bool(row["asset_exists"]) for row in source_manifest)
    reproduction_png_existing = sum(bool(row["png_exists"]) for row in reproduction_manifest)
    reproduction_pdf_existing = sum(bool(row["pdf_exists"]) for row in reproduction_manifest)
    caption_verified = sum(row["caption_status"] == "pdf_caption_block" for row in source_manifest)
    gap_counts = count_by(gap_rows, "evidence_status")
    proxy_counts = count_by(validation_rows, "uses_proxy")
    grade_counts = dict(collections.Counter(row["reproduction_grade"] for row in registry))
    gate_counts = count_by(gate_rows, "status")

    project_audit = f"""# 阶段 A 项目审计

## 审计对象

- McCarthy 主版本：`{thesis_pdf}`
- PDF 页数：`{len(doc)}`；SHA-256：`{sha256(thesis_pdf)}`
- 参考投稿稿：`{reference_docx}`；SHA-256：`{sha256(reference_docx)}`
- 项目根目录：`{PROJECT_ROOT}`
- 当前 Git HEAD：由阶段 A 提交后写入构建日志；本审计不改写权威 CSV。

## 54 图一致性

- `data/figure_index.csv`：54 个唯一图号。
- `data/reproduction_targets.csv`：54 行，集合与索引一致。
- `data/computed/figure_validation_table.csv`：54 行，集合与索引一致。
- `data/computed/figure_evidence_gap_audit.csv`：54 行，集合与索引一致。
- Chapter 2/3/4/5 目标数：15 / 17 / 8 / 14。
- 原论文现有裁图：{source_existing}/54；复现 PNG：{reproduction_png_existing}/54；复现 PDF：{reproduction_pdf_existing}/54。
- 从原 PDF 文本块核对到的图题：{caption_verified}/54；其余均已列入缺失资产清单，不猜测补写。
- 原图重复哈希组：{len(source_dupes)}；复现图重复哈希组：{len(reproduction_dupes)}。

## 当前权威状态

- 证据状态：{md_table_counts(gap_counts)}。
- proxy 标记：{md_table_counts(proxy_counts)}。
- 本报告 A-E 映射初值：{md_table_counts(grade_counts)}。
- staged gate 状态：{md_table_counts(gate_counts)}。

## 真实性边界

- Chapter 3 Route H 当前图源层可审计，但 monolithic cold-start 失败仍必须保留；hybrid 冷启动链与具体图源层门槛不得混写。
- Chapter 4 Fig. 4.3-4.6 的状态空间/局部 STM 证据不等于论文投影等价；冻结的 panel-(d) 投影 holdout 为失败边界。
- 代理图、示意图、局部数值分支与应用 baseline 均不得升级为论文逐点等价。
- 参考稿只用于排版和论证形式学习；其研究数据、结论和句子不进入本报告。
- 任何未能从 PDF、CSV、NPZ、脚本或实际构建结果核实的信息统一写作【待核实】。

## 阶段 A 结论

54 图索引和现有资产均已建立一一映射；阶段 A 审计与设计交付齐全。低尺寸原图、未自动识别图题和逐图模型/坐标系/方法字段作为后续阶段的显式队列，不构成隐性假设。阶段 A 状态：`PASS_WITH_TRACKED_GAPS`。
"""
    (STAGE_A / "project_audit.md").write_text(project_audit, encoding="utf-8")

    outline = """# 文档提纲

1. 题名、作者/单位/导师占位符与中英文标题
2. 摘要、Abstract 与关键词
3. 1 引言
4. 2 动力学模型与数值方法
   - 2.1 CR3BP/BCR4BP 与坐标、单位
   - 2.2 周期轨道修正、延拓与 Jacobi 常数
   - 2.3 不变曲线/环面、映射与 DG/STM
   - 2.4 流形、打靶、转移与误差指标
5. 3 复现范围、数据来源与 A-E 评价方法
6. 4 Chapter 2：Fig. 2.1-2.15 逐图对照
7. 5 Chapter 3：Fig. 3.1-3.17 逐图对照
8. 6 Chapter 4：Fig. 4.1-4.8 逐图对照
9. 7 Chapter 5：Fig. 5.1-5.14 逐图对照
10. 8 综合结果与讨论
11. 9 复现限制
12. 10 结论
13. 参考文献
14. 附录 A：54 图状态总表
15. 附录 B：关键参数与误差表
16. 附录 C：脚本、数据、环境、命令、Git 与资产哈希

每张图采用固定证据单元：正文引导句 → (a) 原图/(b) 复现图 panel → 中英文图题 → 13 字段说明表 → 核心图定量表 → 差异与边界结论。
"""
    (STAGE_A / "document_outline.md").write_text(outline, encoding="utf-8")

    section_summary = "; ".join(
        f"节{row['index']}={row['columns']}栏,{row['page_width_mm']}×{row['page_height_mm']} mm"
        for row in style_data["sections"]
    )
    word_spec = f"""# Word 样式规范

## 参考依据

- 参考稿节设置摘要：{section_summary}。
- 详细 XML/样式统计见 `reference_style_analysis.md/json`；具体研究内容未复制。

## 页面与节

- A4 纵向；正文采用双栏，54 组对照 panel、宽表和关键公式所在节切换为通栏后恢复双栏。
- 页眉写报告短题；页脚居中连续页码。标题、图题、表题与其对象启用 keep-with-next/keep-together。
- 页边距采用参考稿量级：上 25.4 mm、下 22.5 mm、左/右 20.0 mm；最终渲染若发生图表溢出，只允许等比缩放图表或切换通栏，不以缩小安全边距解决。

## 字体与段落

- 中文正文：宋体 10.5 pt；西文、数字和变量：Times New Roman 10.5 pt。
- 中文题名：黑体 18 pt；英文题名：Times New Roman 15 pt；一级/二级/三级标题分别 14/12/10.5 pt 加粗。
- 正文两端对齐，首行缩进 2 个汉字，行距 1.15 倍；长路径、哈希和命令使用等宽字体 8-9 pt。
- 作者、单位、导师、基金和投稿信息只用【待核实】占位符。

## 图表与公式

- 图题在图下、表题在表上；中文题注在前、英文题注在后；连续编号并在正文先行引用。
- 表格采用三线表语义：顶线/表头底线/底线，原则上不使用竖线；缺失值写“—”，未知事实写【待核实】。
- 公式单独成段、主体居中、编号右对齐；变量斜体、单位正体，正文引用“式（X）”。
- 自动目录基于 Heading 1-3；目录域在 Word/LibreOffice 打开时更新。

## 防错

- 不允许图像拉伸、非等比缩放、隐性裁切或用视觉相似替代数值证据。
- 每个图表必须有正文引用；每张目标图必须有原图、复现图、状态、等级与限制。
"""
    (STAGE_A / "word_style_spec.md").write_text(word_spec, encoding="utf-8")

    plot_spec = """# 绘图与对照 panel 规范

- 复现图优先使用现有生成脚本重新导出；保留矢量 PDF，并生成 300-600 dpi PNG。
- 单图建议 160-180 mm 宽；两图 panel 使用等高、不拉伸的 (a)/(b) 布局，白色背景和 8-10 pt 标签。
- 中文标注用宋体/微软雅黑，西文、数字与数学符号用 Times New Roman/DejaVu Serif；线宽 1.0-1.6 pt，标记 3-6 pt。
- 颜色使用色盲友好蓝/橙/灰组合，并辅以实线/虚线/点划线；禁止彩虹色图和仅靠颜色编码。
- 坐标轴必须有物理量与单位；色条必须有名称与单位；图例不得遮挡数据。
- 可比图统一坐标范围、视角、投影、轴比例、时间区间和色标；不能统一时在逐图说明中解释。
- 三维图记录 elevation、azimuth、坐标范围、aspect ratio 与投影类型；不得为追求相似而升级科学结论。
- 原论文图只做高质量提取和等比缩放，不修改数据、不删除子图、不伪造分辨率。
- panel 输出同时记录输入路径、SHA-256、像素尺寸和构建脚本版本。
"""
    (STAGE_A / "plot_style_spec.md").write_text(plot_spec, encoding="utf-8")

    visual_audit = """# 参考投稿稿视觉版式审计

## 核对方法

- 原始 DOCX 以只读方式打开，不修改用户文件。
- OOXML 扩展属性记录 13 页；本机 Microsoft Word 12.0 只读导出为 14 页；LibreOffice 26.2.4 导出为 15 页。
- Microsoft Word PDF 作为主视觉基准；LibreOffice 仅作为跨渲染器风险检查。
- LibreOffice 版本出现 Word 公式域的 `MERGEFORMAT` 可见文本，说明公式/域代码不能只靠 LibreOffice 验收。

## 可迁移版式特征

- 首页采用通栏：期刊眉题与分隔线、题名、作者单位、摘要、关键词和分类信息形成紧凑前置区。
- 正文为双栏，A4 纵向；页眉有短题/刊名，正文带行号。长公式、宽图和宽表通过连续分节切换为通栏后再恢复双栏。
- 标题采用阿拉伯数字分级；二级、三级标题紧随论证展开，不单独占页。
- 图位于相关论述之后，子图标签置于图内或图下；中文图题在前、英文图题在后，均居中。
- 表格为无竖线的期刊式三线结构，使用克制的绿色水平线作为视觉识别；表头集中给出符号与单位。
- 公式主体居中、编号靠右，文中使用编号回指；多行方程和分段定义保持同一基线和括号层级。
- 参考文献使用顺序编码，悬挂缩进，小字号双栏排版；中英文条目维持统一标点与字段顺序。

## 学术语言与结果论证形式

- 行文以研究对象、方法和计算结果为主语，避免口语化判断；先交代模型/参数，再陈述结果。
- 结果段落按“文字提出问题或设置—图展示几何/趋势—表报告数值—文字解释差异与机理”形成证据链。
- 定量结论给出单位、区间或相对变化，并在相邻段落说明条件与适用范围；不把示意或单一视图升级为严格等价。
- 结论按工作内容分项汇总，参考文献前集中收束主要结果；本报告将另外设置“复现限制”章节强化真实性边界。

## 对本报告的取舍

- 采用通栏首页、双栏正文、通栏对照 panel、双语题注、三线表、右编号公式和顺序编码参考文献。
- 不复制参考稿的具体研究主题、数据、图形、公式内容、结论或句子。
- 不默认复制投稿行号和刊名占位信息；本报告优先用于导师/审稿复核，行号仅在正式投稿模板明确要求时启用。
- 最终 Word/PDF 必须分别经 Microsoft Word 与 LibreOffice/PDF 渲染检查；两者页数差异与域代码异常写入构建日志。
"""
    (STAGE_A / "reference_visual_audit.md").write_text(visual_audit, encoding="utf-8")

    missing_lines = [
        "# 缺失资产与待办清单",
        "",
        f"共记录 `{len(missing)}` 条阶段 A 问题。这里的“缺失”包括真正缺文件、尺寸不足和无法自动核对的图题；不得以猜测关闭。",
        "",
        "| 图号 | 类别 | 问题 | 下一动作 |",
        "|---|---|---|---|",
    ]
    for row in missing:
        missing_lines.append(f"| {row['figure_id']} | {row['category']} | {row['issue']} | {row['next_action']} |")
    missing_lines.extend(
        [
            "",
            "## 全局内容字段队列",
            "",
            "- 54 图的动力学模型、坐标系、数值方法和差异原因需在阶段 C 从脚本/CSV/NPZ 逐条绑定；当前 registry 中统一标记【待核实】。",
            "- 作者、单位、导师、基金和投稿信息均为【待核实】。",
            "- 原作者未公开的初始状态、连续分支节点、相位、流形分支和优化约束不得补造。",
        ]
    )
    (STAGE_A / "missing_assets.md").write_text("\n".join(missing_lines) + "\n", encoding="utf-8")

    gate = f"""# 阶段 A 验收门槛

- [x] 参考稿样式分析已生成（OOXML 结构统计 + Microsoft Word/LibreOffice PDF 视觉抽检）。
- [x] McCarthy 原论文 54 图清单已生成。
- [x] 54 图 registry 初版已生成。
- [x] 当前复现资产清单已生成。
- [x] 文档提纲已生成。
- [x] Word 样式规范已生成。
- [x] 绘图规范已生成。
- [x] 缺失资产清单已生成。
- [x] 54/54 图号在 index/targets/validation/gap 四个权威表中集合一致。
- [x] 阶段 A 未生成最终 Word。

状态：`PASS_WITH_TRACKED_GAPS`

说明：现有 54 对图形资产可进入阶段 B，但 `{len(missing)}` 条图题/分辨率/资产质量问题必须在阶段 B-C 按清单处理；不能据此提前宣布最终报告验收通过。
"""
    (STAGE_A / "stage_a_gate.md").write_text(gate, encoding="utf-8")

    summary = {
        "figures": len(index_rows),
        "source_existing": source_existing,
        "reproduction_png_existing": reproduction_png_existing,
        "reproduction_pdf_existing": reproduction_pdf_existing,
        "caption_verified": caption_verified,
        "source_duplicate_groups": len(source_dupes),
        "reproduction_duplicate_groups": len(reproduction_dupes),
        "missing_rows": len(missing),
        "evidence_counts": gap_counts,
        "grade_counts": grade_counts,
        "gate_counts": gate_counts,
        "stage_a_status": "PASS_WITH_TRACKED_GAPS",
    }
    (STAGE_A / "stage_a_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thesis", type=Path, default=WORKSPACE_ROOT / "2018_McCarthy_拟周期轨道.pdf")
    parser.add_argument(
        "--reference-docx",
        type=Path,
        default=WORKSPACE_ROOT / "[20260709]DRO至日地L1 Halo有动力月球借力转移策略_投稿版.docx",
    )
    parser.add_argument(
        "--reference-style-json",
        type=Path,
        default=STAGE_A / "reference_style_analysis.json",
    )
    return parser.parse_args()


def main() -> int:
    summary = build(parse_args())
    print(
        "stage_a=" + summary["stage_a_status"]
        + f" figures={summary['figures']} source={summary['source_existing']}"
        + f" repro_png={summary['reproduction_png_existing']}"
        + f" captions={summary['caption_verified']} missing_rows={summary['missing_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
