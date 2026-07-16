#!/usr/bin/env python3
"""Run the complete Stage-G report rebuild, validation, rendering, and packaging pipeline."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy
import scipy


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
STAGE_G = PROJECT_ROOT / "stage_g_delivery_review"
LOG_PATH = STAGE_G / "stage_g_execution_log.txt"
RUN_CONFIG_PATH = STAGE_G / "stage_g_run_config.json"
GOAL_PATH = WORKSPACE_ROOT / "计划与目标" / "codex_goal_paper_validation_and_adviser_delivery.md"
FROZEN_TRUTH_PATHS = [
    PROJECT_ROOT / "docs/mccarthy2018_staged_goal_gate_status.md",
    PROJECT_ROOT / "data/computed/mccarthy2018_staged_goal_gate_status.csv",
    PROJECT_ROOT / "data/computed/figure_validation_table.csv",
    PROJECT_ROOT / "data/computed/chapter4_fig43_fig46_projection_holdout_audit.csv",
    PROJECT_ROOT / "src/qp_orbits/chapter4_reproduction_lock.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=WORKSPACE_ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return completed.stdout.strip()


def truth_hashes() -> dict[str, str]:
    missing = [str(path) for path in FROZEN_TRUTH_PATHS if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing frozen truth files: " + "; ".join(missing))
    return {path.relative_to(PROJECT_ROOT).as_posix(): sha256(path) for path in FROZEN_TRUTH_PATHS}


def command(label: str, script: str, *args: str) -> dict[str, object]:
    return {
        "label": label,
        "argv": [sys.executable, str(PROJECT_ROOT / script), *args],
    }


def main() -> int:
    STAGE_G.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    before = truth_hashes()
    commands = [
        command("stage_c_evidence", "reports/mccarthy2018_figure_comparison/scripts/build_stage_c_evidence.py"),
        command("stage_d_panels", "reports/mccarthy2018_figure_comparison/scripts/build_comparison_panels.py"),
        command("asset_validation", "reports/mccarthy2018_figure_comparison/scripts/validate_report_assets.py"),
        command("word_build", "reports/mccarthy2018_figure_comparison/scripts/build_word_report.py"),
        command("pdf_export", "reports/mccarthy2018_figure_comparison/scripts/export_report_pdf.py"),
        command(
            "delivery_validation",
            "reports/mccarthy2018_figure_comparison/scripts/validate_final_report.py",
            "--output-dir",
            str(STAGE_G),
            "--label",
            "delivery",
        ),
        command(
            "delivery_render",
            "reports/mccarthy2018_figure_comparison/scripts/render_report_review.py",
            "--output-dir",
            str(STAGE_G),
        ),
        command("delivery_package", "reports/mccarthy2018_figure_comparison/scripts/build_stage_g_delivery_package.py"),
    ]
    config: dict[str, object] = {
        "status": "RUNNING",
        "started_at_utc": started_at.isoformat(),
        "goal_path": str(GOAL_PATH),
        "goal_sha256": sha256(GOAL_PATH),
        "source_git_head": git("rev-parse", "HEAD"),
        "python": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "environment_lock_sha256": sha256(PROJECT_ROOT / "environment-lock.yml"),
        "frozen_truth_hashes_before": before,
        "commands": commands,
        "steps": [],
    }
    RUN_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    with LOG_PATH.open("w", encoding="utf-8") as log:
        log.write(f"Stage-G delivery pipeline\nstarted_at_utc={started_at.isoformat()}\n")
        log.write(f"python={sys.executable}\nsource_git_head={config['source_git_head']}\n")
        log.flush()
        try:
            for item in commands:
                label = str(item["label"])
                argv = [str(part) for part in item["argv"]]
                step_start = time.perf_counter()
                log.write(f"\n=== {label} ===\ncommand={subprocess.list2cmdline(argv)}\n")
                log.flush()
                max_attempts = 3 if label == "word_build" else 1
                completed = None
                for attempt in range(1, max_attempts + 1):
                    completed = subprocess.run(
                        argv,
                        cwd=PROJECT_ROOT,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if completed.returncode == 0 or attempt == max_attempts:
                        break
                    log.write(
                        f"attempt={attempt}/{max_attempts} returncode={completed.returncode}; "
                        "retrying after transient report-file lock\n"
                    )
                    if completed.stderr:
                        log.write(completed.stderr)
                        if not completed.stderr.endswith("\n"):
                            log.write("\n")
                    log.flush()
                    time.sleep(2.0)
                assert completed is not None
                elapsed = time.perf_counter() - step_start
                log.write(f"returncode={completed.returncode}\nelapsed_seconds={elapsed:.6f}\n")
                if completed.stdout:
                    log.write("--- stdout ---\n" + completed.stdout)
                    if not completed.stdout.endswith("\n"):
                        log.write("\n")
                if completed.stderr:
                    log.write("--- stderr ---\n" + completed.stderr)
                    if not completed.stderr.endswith("\n"):
                        log.write("\n")
                log.flush()
                config["steps"].append(
                    {
                        "label": label,
                        "returncode": completed.returncode,
                        "elapsed_seconds": elapsed,
                        "attempts": attempt,
                    }
                )
                RUN_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
                if completed.returncode != 0:
                    raise RuntimeError(f"Stage-G step failed: {label} ({completed.returncode})")
                if label == "delivery_render":
                    shutil.copy2(STAGE_G / "all_pages_contact_sheet.png", STAGE_G / "final_pages_contact_sheet.png")

            after = truth_hashes()
            if before != after:
                changed = [key for key in before if before[key] != after.get(key)]
                raise RuntimeError(f"Frozen truth artifacts changed during Stage-G: {changed}")
            config["frozen_truth_hashes_after"] = after
            config["frozen_truth_unchanged"] = True
            config["status"] = "PASS"
            config["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            config["elapsed_seconds"] = (datetime.now(timezone.utc) - started_at).total_seconds()
            RUN_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            log.write("\nstage_g_pipeline=PASS\nfrozen_truth_unchanged=true\n")
            print("stage_g_pipeline=PASS frozen_truth_unchanged=true")
            return 0
        except Exception as error:
            config["status"] = "FAIL"
            config["failure"] = f"{type(error).__name__}: {error}"
            config["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            RUN_CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
            log.write(f"\nstage_g_pipeline=FAIL\nerror={type(error).__name__}: {error}\n")
            raise


if __name__ == "__main__":
    raise SystemExit(main())
