"""Prepare audited JSON input and invoke the docx-js report builder."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import zipfile
from datetime import date
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
STAGE_E = REPORT_ROOT / "stage_e"
DEFAULT_OUTPUT = REPORT_ROOT / "McCarthy2018_54图逐图复现对照报告.docx"
NODE = Path("C:/Users/wwh20/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe")
NODE_MODULES = Path("C:/Users/wwh20/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--node", type=Path, default=NODE)
    args = parser.parse_args()
    STAGE_E.mkdir(parents=True, exist_ok=True)

    registry_path = REPORT_ROOT / "figure_comparison_registry.csv"
    metrics_path = REPORT_ROOT / "quantitative_metrics_registry.csv"
    delivery_fields_path = REPORT_ROOT / "delivery_fields.json"
    pending_path = REPORT_ROOT / "stage_d" / "pending_after_panels.csv"
    summary_path = REPORT_ROOT / "stage_c" / "stage_c_summary.json"
    manifest_paths = [
        REPORT_ROOT / "source_figure_manifest.csv",
        REPORT_ROOT / "reproduction_figure_manifest.csv",
        REPORT_ROOT / "comparison_panel_manifest.csv",
        registry_path,
        metrics_path,
        delivery_fields_path,
    ]
    registry = read_csv(registry_path)
    metrics = read_csv(metrics_path)
    pending = read_csv(pending_path)
    delivery_fields = json.loads(delivery_fields_path.read_text(encoding="utf-8"))
    required_delivery_fields = {"author_name", "affiliation", "adviser", "verification_status"}
    missing_delivery_fields = sorted(required_delivery_fields - set(delivery_fields))
    if missing_delivery_fields:
        raise RuntimeError(f"Missing delivery fields: {missing_delivery_fields}")
    if len(registry) != 54:
        raise RuntimeError(f"Expected 54 registry rows, found {len(registry)}")
    if not metrics:
        raise RuntimeError("Quantitative metrics registry is empty")
    if any(row.get("comparison_asset") == "【待核实】" for row in registry):
        raise RuntimeError("Comparison panels are incomplete")
    missing_panels = [row["target_id"] for row in registry if not (PROJECT_ROOT / row["comparison_asset"]).is_file()]
    if missing_panels:
        raise FileNotFoundError(f"Missing comparison panels: {missing_panels}")

    build_input = {
        "registry": registry,
        "metrics": metrics,
        "pending": pending,
        "delivery_fields": delivery_fields,
        "summary": json.loads(summary_path.read_text(encoding="utf-8")),
        "build_meta": {
            "build_date": date.today().isoformat(),
            "git_head": git("rev-parse", "HEAD"),
            "git_log": git("log", "-8", "--pretty=format:%h %s").splitlines(),
            "project_root": str(PROJECT_ROOT.resolve()),
            "report_root": str(REPORT_ROOT.resolve()),
            "python": str(Path(os.environ.get("PYTHON_EXECUTABLE", os.sys.executable)).resolve()),
            "node": str(args.node.resolve()),
            "node_modules": str(NODE_MODULES.resolve()),
            "manifest_hashes": {path.name: sha256(path) for path in manifest_paths},
        },
    }
    input_path = STAGE_E / "word_build_input.json"
    input_path.write_text(json.dumps(build_input, ensure_ascii=False, indent=2), encoding="utf-8")

    env = os.environ.copy()
    env["NODE_PATH"] = str(NODE_MODULES)
    command = [
        str(args.node),
        "--max-old-space-size=4096",
        str(SCRIPT_DIR / "build_word_report.js"),
        str(input_path),
        str(args.output),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, encoding="utf-8")
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.returncode != 0:
        if completed.stderr:
            print(completed.stderr, end="", file=os.sys.stderr)
        raise RuntimeError(f"docx-js builder failed with exit code {completed.returncode}")
    if not args.output.is_file() or args.output.stat().st_size == 0:
        raise RuntimeError("DOCX builder did not produce a nonempty output")
    with zipfile.ZipFile(args.output) as archive:
        required = {"[Content_Types].xml", "word/document.xml", "word/styles.xml", "word/numbering.xml"}
        missing_parts = sorted(required - set(archive.namelist()))
        if missing_parts:
            raise RuntimeError(f"Generated DOCX is missing parts: {missing_parts}")
        embedded_media = sum(name.startswith("word/media/") for name in archive.namelist())
    if embedded_media < 54:
        raise RuntimeError(f"Generated DOCX has too few embedded media parts: {embedded_media}")

    status = {
        "status": "PASS",
        "output": str(args.output.resolve()),
        "output_bytes": args.output.stat().st_size,
        "output_sha256": sha256(args.output),
        "registry_rows": len(registry),
        "metric_rows": len(metrics),
        "pending_rows": len(pending),
        "embedded_media_parts": embedded_media,
        "build_input": str(input_path.resolve()),
        "build_input_sha256": sha256(input_path),
        "git_head": build_input["build_meta"]["git_head"],
        "command": command,
    }
    (STAGE_E / "word_build_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"word_build=PASS figures={len(registry)} metrics={len(metrics)} "
        f"media={embedded_media} bytes={args.output.stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
