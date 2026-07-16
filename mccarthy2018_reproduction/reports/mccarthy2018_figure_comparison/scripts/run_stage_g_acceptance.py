#!/usr/bin/env python3
"""Run and record the Stage-G acceptance checks that are safe before research Stage 2."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
STAGE_G = PROJECT_ROOT / "stage_g_delivery_review"
LOG_PATH = STAGE_G / "stage_g_acceptance_log.txt"
STATUS_PATH = STAGE_G / "stage_g_acceptance_status.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    run_config = json.loads((STAGE_G / "stage_g_run_config.json").read_text(encoding="utf-8"))
    frozen = run_config["frozen_truth_hashes_before"]
    commands = [
        {
            "label": "unit_tests",
            "argv": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            "cwd": PROJECT_ROOT,
        },
        {
            "label": "reproduction_smoke",
            "argv": [sys.executable, "scripts/validate_reproduction_smoke.py"],
            "cwd": PROJECT_ROOT,
        },
        {
            "label": "target_registry_check",
            "argv": [sys.executable, "scripts/build_reproduction_targets.py", "--check"],
            "cwd": PROJECT_ROOT,
        },
        {
            "label": "git_diff_check",
            "argv": ["git", "diff", "--check"],
            "cwd": WORKSPACE_ROOT,
        },
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    started = datetime.now(timezone.utc)
    status: dict[str, object] = {
        "status": "RUNNING",
        "started_at_utc": started.isoformat(),
        "python": sys.executable,
        "commands": [],
        "tests": {"count": 0, "passed": 0, "failed": 0},
        "deferred_by_required_stage_order": [
            "scripts/run_invariant_bundle_benchmarks.py (belongs to independent scientific validation and rerun stages)",
        ],
    }
    with LOG_PATH.open("w", encoding="utf-8") as log:
        log.write(f"Stage-G acceptance\nstarted_at_utc={started.isoformat()}\nPYTHONPATH={env['PYTHONPATH']}\n")
        try:
            for item in commands:
                tick = time.perf_counter()
                completed = subprocess.run(
                    item["argv"],
                    cwd=item["cwd"],
                    env=env,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                elapsed = time.perf_counter() - tick
                combined = completed.stdout + completed.stderr
                log.write(
                    f"\n=== {item['label']} ===\n"
                    f"command={subprocess.list2cmdline(item['argv'])}\n"
                    f"returncode={completed.returncode}\nelapsed_seconds={elapsed:.6f}\n"
                    f"{combined}"
                )
                if not combined.endswith("\n"):
                    log.write("\n")
                log.flush()
                status["commands"].append(
                    {"label": item["label"], "returncode": completed.returncode, "elapsed_seconds": elapsed}
                )
                if item["label"] == "unit_tests":
                    match = re.search(r"Ran (\d+) tests?", combined)
                    count = int(match.group(1)) if match else 0
                    failed = 0 if completed.returncode == 0 and re.search(r"\nOK\s*$", combined) else 1
                    status["tests"] = {"count": count, "passed": count if failed == 0 else 0, "failed": failed}
                if completed.returncode != 0:
                    raise RuntimeError(f"Acceptance command failed: {item['label']}")

            current = {
                relative_path: sha256(PROJECT_ROOT / relative_path)
                for relative_path in frozen
            }
            if current != frozen:
                raise RuntimeError("Frozen truth hashes changed after acceptance checks")
            status["frozen_truth_hashes_current"] = current
            status["frozen_truth_unchanged"] = True
            status["status"] = "PASS"
            status["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            status["elapsed_seconds"] = (datetime.now(timezone.utc) - started).total_seconds()
            log.write("\nstage_g_acceptance=PASS\nfrozen_truth_unchanged=true\n")
        except Exception as error:
            status["status"] = "FAIL"
            status["failure"] = f"{type(error).__name__}: {error}"
            status["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            log.write(f"\nstage_g_acceptance=FAIL\nerror={type(error).__name__}: {error}\n")
            STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
            raise
    STATUS_PATH.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"stage_g_acceptance=PASS tests={status['tests']['passed']}/{status['tests']['count']} "
        f"elapsed={status['elapsed_seconds']:.3f}s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
