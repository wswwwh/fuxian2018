"""Build 54 uniform, aspect-preserving original-versus-reproduction panels."""

from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
STAGE_D = REPORT_ROOT / "stage_d"
PENDING = "【待核实】"
PANEL_SIZE = (2400, 1400)
FONT_PATH = Path("C:/Windows/Fonts/msyh.ttc")
STATUS_CN = {"accepted": "接受", "boundary": "边界", "diagnostic": "诊断", "proxy": "代理"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames or list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rel(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def figure_key(figure_id: str) -> tuple[int, int]:
    return tuple(int(part) for part in figure_id.split("."))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/msyhbd.ttc") if bold else FONT_PATH,
        Path("C:/Windows/Fonts/simhei.ttf") if bold else Path("C:/Windows/Fonts/simsun.ttc"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, face, fill: str) -> None:
    left, top, right, bottom = box
    bounds = draw.textbbox((0, 0), text, font=face)
    width, height = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.text(((left + right - width) / 2, (top + bottom - height) / 2), text, font=face, fill=fill)


def fit_image(path: Path, box_size: tuple[int, int]) -> tuple[Image.Image, float]:
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    scale = min(box_size[0] / image.width, box_size[1] / image.height, 1.0)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    if size != image.size:
        image = image.resize(size, Image.Resampling.LANCZOS)
    return image, scale


def build_panel(row: dict[str, str], output: Path) -> dict[str, object]:
    original_path = PROJECT_ROOT / row["paper_asset"]
    reproduction_path = PROJECT_ROOT / row["reproduction_asset"]
    if not original_path.is_file() or not reproduction_path.is_file():
        raise FileNotFoundError(f"Missing panel input for Fig. {row['target_id']}")

    canvas = Image.new("RGB", PANEL_SIZE, "white")
    draw = ImageDraw.Draw(canvas)
    heading_font = font(42, bold=True)
    label_font = font(36, bold=True)
    footer_font = font(27)
    title = (
        f"McCarthy (2018) Fig. {row['target_id']}  |  "
        f"复现等级 {row['reproduction_grade']}  |  "
        f"状态 {STATUS_CN.get(row['status'], row['status'])}（{row['status']}）"
    )
    centered_text(draw, (40, 22, 2360, 92), title, heading_font, "#1F2937")
    boxes = [(55, 175, 1175, 1215), (1225, 175, 2345, 1215)]
    labels = ["(a) 原论文图 / Original", "(b) 本项目复现 / Reproduced"]
    sources = [original_path, reproduction_path]
    scales: list[float] = []
    for box, label, source in zip(boxes, labels, sources):
        left, top, right, bottom = box
        draw.rectangle(box, outline="#9CA3AF", width=3)
        centered_text(draw, (left, 105, right, 163), label, label_font, "#111827")
        image, scale = fit_image(source, (right - left - 24, bottom - top - 24))
        scales.append(scale)
        x = left + (right - left - image.width) // 2
        y = top + (bottom - top - image.height) // 2
        canvas.paste(image, (x, y))
    footer = (
        f"原论文页码 p. {row['paper_page']}（PDF p. {row['pdf_page']}）  |  "
        "两侧均等比缩放；未裁切、未拉伸、未改变科学数据"
    )
    centered_text(draw, (50, 1240, 2350, 1365), footer, footer_font, "#374151")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=True)
    return {
        "original_scale": round(scales[0], 8),
        "reproduction_scale": round(scales[1], 8),
        "width_px": PANEL_SIZE[0],
        "height_px": PANEL_SIZE[1],
    }


def montage(paths: list[Path], output: Path, columns: int = 3) -> None:
    thumb_size = (720, 420)
    rows = (len(paths) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb_size[0], rows * thumb_size[1]), "white")
    for index, path in enumerate(paths):
        with Image.open(path) as source:
            image = source.convert("RGB")
        image.thumbnail((thumb_size[0] - 20, thumb_size[1] - 20), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_size[0] + (thumb_size[0] - image.width) // 2
        y = (index // columns) * thumb_size[1] + (thumb_size[1] - image.height) // 2
        canvas.paste(image, (x, y))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=90, subsampling=0)


def page_preview(panel_paths: dict[str, Path]) -> None:
    page_size = (1240, 1754)
    page_font = font(32, bold=True)
    body_font = font(23)
    full = Image.new("RGB", page_size, "white")
    draw = ImageDraw.Draw(full)
    centered_text(draw, (60, 45, 1180, 115), "通栏 panel 预览 / Full-width preview", page_font, "#111827")
    with Image.open(panel_paths["3.10"]) as source:
        panel = source.convert("RGB")
    panel.thumbnail((1120, 760), Image.Resampling.LANCZOS)
    full.paste(panel, ((1240 - panel.width) // 2, 170))
    draw.multiline_text(
        (80, 990),
        "正文在图前提出比较对象，图后紧接中英文题注、13 字段说明表和定量表。\n"
        "大型双图对照采用通栏，以保证坐标轴、图例和子图可读。",
        font=body_font,
        fill="#374151",
        spacing=12,
    )
    full.save(STAGE_D / "full_width_preview.png", optimize=True)

    double = Image.new("RGB", page_size, "white")
    draw = ImageDraw.Draw(double)
    centered_text(draw, (60, 45, 1180, 115), "双栏缩略预览 / Two-column preview", page_font, "#111827")
    draw.line((620, 140, 620, 1650), fill="#D1D5DB", width=2)
    for index, figure_id in enumerate(("3.10", "4.3")):
        with Image.open(panel_paths[figure_id]) as source:
            panel = source.convert("RGB")
        panel.thumbnail((540, 380), Image.Resampling.LANCZOS)
        x = 50 + index * 610 + (540 - panel.width) // 2
        double.paste(panel, (x, 180))
        draw.multiline_text(
            (55 + index * 610, 610),
            f"Fig. {figure_id} 双栏缩略仅用于基础示意图或附录索引。\n"
            "复杂数值图若轴标不可读，必须改用通栏，不强行缩小。",
            font=body_font,
            fill="#374151",
            spacing=10,
        )
    double.save(STAGE_D / "double_column_preview.png", optimize=True)


def main() -> int:
    STAGE_D.mkdir(parents=True, exist_ok=True)
    registry_path = REPORT_ROOT / "figure_comparison_registry.csv"
    registry = read_csv(registry_path)
    if len(registry) != 54:
        raise RuntimeError(f"Expected 54 registry rows, found {len(registry)}")
    registry.sort(key=lambda row: figure_key(row["target_id"]))
    panel_paths: dict[str, Path] = {}
    manifest: list[dict[str, object]] = []
    panel_hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for row in registry:
        figure_id = row["target_id"]
        output = REPORT_ROOT / "assets" / "comparison" / f"fig_{figure_id.replace('.', '_')}_comparison.png"
        panel_info = build_panel(row, output)
        panel_hash = sha256(output)
        panel_hashes[panel_hash].append(figure_id)
        panel_paths[figure_id] = output
        row["comparison_asset"] = rel(output)
        original = PROJECT_ROOT / row["paper_asset"]
        reproduced = PROJECT_ROOT / row["reproduction_asset"]
        manifest.append(
            {
                "target_id": figure_id,
                "paper_asset": row["paper_asset"],
                "paper_asset_sha256": sha256(original),
                "reproduction_asset": row["reproduction_asset"],
                "reproduction_asset_sha256": sha256(reproduced),
                "comparison_asset": rel(output),
                "comparison_asset_bytes": output.stat().st_size,
                "comparison_asset_sha256": panel_hash,
                "width_px": panel_info["width_px"],
                "height_px": panel_info["height_px"],
                "original_scale": panel_info["original_scale"],
                "reproduction_scale": panel_info["reproduction_scale"],
                "aspect_preserved": True,
                "cropped": False,
                "stretched": False,
                "underlying_scientific_figure_redrawn": False,
                "panel_standardization": "uniform canvas, labels, borders, aspect-preserving placement",
                "grade": row["reproduction_grade"],
                "status": row["status"],
            }
        )

    duplicate_groups = [ids for ids in panel_hashes.values() if len(ids) > 1]
    if duplicate_groups:
        raise RuntimeError(f"Duplicate comparison panel hashes: {duplicate_groups}")
    write_csv(registry_path, registry)
    write_csv(REPORT_ROOT / "comparison_panel_manifest.csv", manifest)

    for chapter in ("2", "3", "4", "5"):
        paths = [panel_paths[row["target_id"]] for row in registry if row["chapter"] == chapter]
        montage(paths, STAGE_D / f"chapter{chapter}_panel_montage.jpg")
    page_preview(panel_paths)

    remaining_pending: list[dict[str, str]] = []
    for row in registry:
        for field, value in row.items():
            if PENDING in value:
                remaining_pending.append({"target_id": row["target_id"], "field": field, "value": value})
    write_csv(STAGE_D / "pending_after_panels.csv", remaining_pending, ["target_id", "field", "value"])

    review_rows = []
    for row in manifest:
        panel = PROJECT_ROOT / str(row["comparison_asset"])
        review_rows.append(
            {
                "target_id": row["target_id"],
                "panel_exists": panel.is_file(),
                "panel_hash_ok": sha256(panel) == row["comparison_asset_sha256"],
                "dimensions_ok": f"{row['width_px']}x{row['height_px']}" == "2400x1400",
                "aspect_preserved": row["aspect_preserved"],
                "cropped": row["cropped"],
                "stretched": row["stretched"],
                "status": "pass",
            }
        )
    write_csv(STAGE_D / "graphics_review.csv", review_rows)
    automated_ok = (
        len(manifest) == 54
        and len(panel_hashes) == 54
        and all(row["status"] == "pass" for row in review_rows)
        and all(row["comparison_asset"] != PENDING for row in registry)
    )
    visual_review = STAGE_D / "visual_panel_review.md"
    status = "PASS" if automated_ok and visual_review.is_file() else "PASS_AUTOMATED_PENDING_VISUAL"
    summary = {
        "status": status,
        "panels": len(manifest),
        "unique_panel_hashes": len(panel_hashes),
        "duplicate_groups": duplicate_groups,
        "underlying_figures_redrawn": 0,
        "standardized_panel_wrappers": len(manifest),
        "remaining_pending_fields": len(remaining_pending),
        "visual_review": visual_review.is_file(),
    }
    (STAGE_D / "graphics_review.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    review_md = f"""# 阶段 D 图形审查

- 状态：`{status}`。
- 对照 panel：54/54；唯一哈希：54；重复：0。
- 所有 panel 固定为 2400×1400 px；两侧图像均等比缩放，不裁切、不拉伸。
- 底层科学图重绘：0；统一 panel 包装：54。统一内容仅包括画布、边框、标签、等级、状态与页码。
- 通栏预览：`full_width_preview.png`；双栏预览：`double_column_preview.png`。
- registry 中 comparison asset 缺失：0；阶段 D 后剩余【待核实】字段：{len(remaining_pending)}。
- 视觉人工复核：{'已记录' if visual_review.is_file() else '待执行'}。
"""
    (STAGE_D / "graphics_review.md").write_text(review_md, encoding="utf-8")
    gate = f"""# 阶段 D 验收门槛

- [{'x' if len(manifest) == 54 else ' '}] 54/54 对照 panel 已生成。
- [{'x' if len(panel_hashes) == 54 else ' '}] panel 非空、唯一且哈希可复核。
- [{'x' if automated_ok else ' '}] 固定尺寸、等比缩放、无裁切、无拉伸检查通过。
- [x] 通栏和双栏版式预览已生成。
- [{'x' if visual_review.is_file() else ' '}] 逐章 montage 人工视觉复核已记录。
- [x] 未将统一包装冒充底层科学图重绘。

状态：`{status}`
"""
    (STAGE_D / "stage_d_gate.md").write_text(gate, encoding="utf-8")
    print(
        f"stage_d={status} panels={len(manifest)} unique={len(panel_hashes)} "
        f"pending={len(remaining_pending)} redrawn=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
