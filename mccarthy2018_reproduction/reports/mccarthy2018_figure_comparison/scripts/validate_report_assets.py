"""Validate report manifests, hashes, dimensions, naming, and one-to-one figure mapping."""

from __future__ import annotations

import collections
import csv
import hashlib
import json
from pathlib import Path

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
STAGE_B = REPORT_ROOT / "stage_b"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def figure_key(figure_id: str) -> tuple[int, int]:
    return tuple(int(part) for part in figure_id.split("."))


def main() -> int:
    source_rows = read_csv(REPORT_ROOT / "source_figure_manifest.csv")
    reproduction_rows = read_csv(REPORT_ROOT / "reproduction_figure_manifest.csv")
    source = {row["target_id"]: row for row in source_rows}
    reproduction = {row["target_id"]: row for row in reproduction_rows}
    expected = {
        *(f"2.{number}" for number in range(1, 16)),
        *(f"3.{number}" for number in range(1, 18)),
        *(f"4.{number}" for number in range(1, 9)),
        *(f"5.{number}" for number in range(1, 15)),
    }
    issues: list[str] = []
    if set(source) != expected:
        issues.append(f"source ID set mismatch: missing={sorted(expected-set(source), key=figure_key)} extra={sorted(set(source)-expected, key=figure_key)}")
    if set(reproduction) != expected:
        issues.append(f"reproduction ID set mismatch: missing={sorted(expected-set(reproduction), key=figure_key)} extra={sorted(set(reproduction)-expected, key=figure_key)}")

    audit_rows: list[dict[str, object]] = []
    source_hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    reproduction_hashes: collections.defaultdict[str, list[str]] = collections.defaultdict(list)
    for figure_id in sorted(expected, key=figure_key):
        if figure_id not in source or figure_id not in reproduction:
            continue
        original = source[figure_id]
        reproduced = reproduction[figure_id]
        original_path = PROJECT_ROOT / original["asset"]
        reproduced_path = PROJECT_ROOT / reproduced["asset"]
        row_issues: list[str] = []
        expected_original_name = f"fig_{figure_id.replace('.', '_')}_original.png"
        expected_reproduction_name = f"fig_{figure_id.replace('.', '_')}_reproduced.png"
        if original_path.name != expected_original_name:
            row_issues.append("original_name")
        if reproduced_path.name != expected_reproduction_name:
            row_issues.append("reproduction_name")
        if not original_path.is_file():
            row_issues.append("original_missing")
        if not reproduced_path.is_file():
            row_issues.append("reproduction_missing")
        original_hash_ok = reproduced_hash_ok = False
        original_dims = reproduced_dims = ""
        if original_path.is_file():
            current_hash = sha256(original_path)
            original_hash_ok = current_hash == original["asset_sha256"]
            source_hashes[current_hash].append(figure_id)
            with Image.open(original_path) as image:
                original_dims = f"{image.width}x{image.height}"
                if image.width < 800 or image.height < 300:
                    row_issues.append("original_dimensions")
            if not original_hash_ok:
                row_issues.append("original_hash")
        if reproduced_path.is_file():
            current_hash = sha256(reproduced_path)
            reproduced_hash_ok = current_hash == reproduced["asset_sha256"]
            reproduction_hashes[current_hash].append(figure_id)
            with Image.open(reproduced_path) as image:
                reproduced_dims = f"{image.width}x{image.height}"
                if image.width < 1000 or image.height < 600:
                    row_issues.append("reproduction_dimensions")
            if not reproduced_hash_ok:
                row_issues.append("reproduction_hash")
        if original.get("caption_status") != "pdf_caption_block":
            row_issues.append("caption_unverified")
        audit_rows.append(
            {
                "target_id": figure_id,
                "original_asset": original.get("asset", ""),
                "original_dimensions": original_dims,
                "original_hash_ok": original_hash_ok,
                "caption_status": original.get("caption_status", ""),
                "crop_status": original.get("crop_status", ""),
                "reproduction_asset": reproduced.get("asset", ""),
                "reproduction_dimensions": reproduced_dims,
                "reproduction_hash_ok": reproduced_hash_ok,
                "reexported_in_report_build": reproduced.get("reexported_in_report_build", ""),
                "issues": ";".join(row_issues),
                "mapping_status": "pass" if not row_issues else "review",
            }
        )

    source_duplicates = [ids for ids in source_hashes.values() if len(ids) > 1]
    reproduction_duplicates = [ids for ids in reproduction_hashes.values() if len(ids) > 1]
    if source_duplicates:
        issues.append(f"source duplicate hashes: {source_duplicates}")
    if reproduction_duplicates:
        issues.append(f"reproduction duplicate hashes: {reproduction_duplicates}")
    review_rows = [row for row in audit_rows if row["mapping_status"] != "pass"]
    if review_rows:
        issues.append(f"per-figure review rows: {[row['target_id'] for row in review_rows]}")
    STAGE_B.mkdir(parents=True, exist_ok=True)
    visual_review = STAGE_B / "visual_mapping_review.md"
    if not visual_review.is_file():
        issues.append("manual visual mapping review is missing")
    status = "PASS" if not issues and len(audit_rows) == 54 else "FAIL"
    write_csv(STAGE_B / "asset_mapping_audit.csv", audit_rows)
    summary = {
        "status": status,
        "figures": len(audit_rows),
        "original_assets": sum((PROJECT_ROOT / row["original_asset"]).is_file() for row in audit_rows),
        "reproduction_assets": sum((PROJECT_ROOT / row["reproduction_asset"]).is_file() for row in audit_rows),
        "original_unique_hashes": len(source_hashes),
        "reproduction_unique_hashes": len(reproduction_hashes),
        "review_rows": len(review_rows),
        "visual_review": visual_review.is_file(),
        "issues": issues,
    }
    (STAGE_B / "asset_mapping_audit.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    markdown = [
        "# 阶段 B 图形资产映射审计",
        "",
        f"- 状态：`{status}`",
        f"- 原论文图：`{summary['original_assets']}/54`；唯一哈希：`{summary['original_unique_hashes']}`。",
        f"- 复现图：`{summary['reproduction_assets']}/54`；唯一哈希：`{summary['reproduction_unique_hashes']}`。",
        f"- 需复核行：`{summary['review_rows']}`。",
        "- 原图均从 137 页主 PDF 以 4.2 倍页面渲染重新提取；名义 302.4 dpi 不代表提升原 PDF 内嵌栅格的固有分辨率。",
        "- 复现图采用当前脚本生成的非空 PNG/PDF 权威输出做哈希保持复制；本阶段不覆盖旧图，也不声称重新计算 54 个数值任务。",
        "",
        "## 映射表",
        "",
        "| 图号 | 原图尺寸 | 复现图尺寸 | 图题 | 裁切 | 状态 |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in audit_rows:
        markdown.append(
            f"| {row['target_id']} | {row['original_dimensions']} | {row['reproduction_dimensions']} | "
            f"{row['caption_status']} | {row['crop_status']} | {row['mapping_status']} |"
        )
    if issues:
        markdown.extend(["", "## 问题", ""] + [f"- {issue}" for issue in issues])
    (STAGE_B / "asset_mapping_audit.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    gate = f"""# 阶段 B 验收门槛

- [{'x' if status == 'PASS' else ' '}] 54/54 原论文图已重新提取到统一命名目录。
- [{'x' if status == 'PASS' else ' '}] 54/54 复现 PNG 已从当前权威输出复制到统一命名目录。
- [{'x' if status == 'PASS' else ' '}] 图号一一对应，文件名统一。
- [{'x' if status == 'PASS' else ' '}] 图像尺寸、非空、哈希和重复项检查通过。
- [{'x' if status == 'PASS' else ' '}] 缺失、重复和错误映射均为 0。
- [{'x' if visual_review.is_file() else ' '}] 54 图接触表人工映射复核记录存在。

状态：`{status}`
"""
    (STAGE_B / "stage_b_gate.md").write_text(gate, encoding="utf-8")
    print(
        f"stage_b={status} figures={len(audit_rows)} original_unique={len(source_hashes)} "
        f"reproduction_unique={len(reproduction_hashes)} review={len(review_rows)}"
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
