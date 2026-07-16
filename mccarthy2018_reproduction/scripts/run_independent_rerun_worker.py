#!/usr/bin/env python3
"""Fresh-process worker for the isolated invariant-bundle rerun."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import run_invariant_bundle_benchmarks as benchmark  # noqa: E402
import run_invariant_bundle_manifold_convergence as manifold  # noqa: E402


def configure_benchmark(output_root: Path, run_id: str) -> None:
    results = output_root / "results"
    csv_dir = results / "csv"
    npz_dir = results / "npz"
    log_dir = output_root / "logs"
    benchmark.RESULTS = results
    benchmark.CSV_DIR = csv_dir
    benchmark.NPZ_DIR = npz_dir
    benchmark.COCYCLE_DIR = npz_dir / "cocycles"
    benchmark.LOG_DIR = log_dir
    benchmark.METHOD_COMPARISON = csv_dir / "method_comparison.csv"
    benchmark.RESOLUTION_CONVERGENCE = csv_dir / "resolution_convergence.csv"
    benchmark.PHASE_CONTINUITY = csv_dir / "phase_continuity.csv"
    benchmark.MANIFOLD_CONVERGENCE = csv_dir / "manifold_convergence.csv"
    benchmark.RUNTIME_SCALING = csv_dir / "runtime_scaling.csv"
    benchmark.METHOD_NPZ = npz_dir / "method_comparison.npz"
    benchmark.RESOLUTION_NPZ = npz_dir / "resolution_convergence.npz"
    benchmark.PHASE_NPZ = npz_dir / "phase_continuity.npz"
    benchmark.MANIFOLD_NPZ = npz_dir / "manifold_convergence.npz"
    benchmark.RUNTIME_NPZ = npz_dir / "runtime_scaling.npz"
    benchmark.CHECKPOINT = log_dir / "benchmark_campaign_checkpoint.json"
    benchmark.RUN_SUMMARY = log_dir / "benchmark_campaign_summary.json"
    benchmark._run_id = lambda: f"{run_id}-bundle"  # type: ignore[method-assign]


def configure_manifold(output_root: Path, run_id: str) -> None:
    configure_benchmark(output_root, run_id)
    results = output_root / "results"
    log_dir = output_root / "logs"
    manifold.METHOD_CSV = results / "csv" / "method_comparison.csv"
    manifold.METHOD_NPZ = results / "npz" / "method_comparison.npz"
    manifold.OUTPUT_CSV = results / "csv" / "manifold_convergence.csv"
    manifold.OUTPUT_NPZ = results / "npz" / "manifold_convergence.npz"
    manifold.CHECKPOINT = log_dir / "manifold_campaign_checkpoint.json"
    manifold.SUMMARY = log_dir / "manifold_campaign_summary.json"
    manifold.AUDIT = results / "docs" / "manifold_stage_f_audit.md"
    manifold._run_id = lambda: f"{run_id}-manifold"  # type: ignore[method-assign]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("bundle", "manifold"), required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--max-wall-seconds", type=float, required=True)
    args = parser.parse_args()
    output_root = args.output_root.resolve()
    expected_parent = (ROOT / "research" / "invariant_bundles" / "independent_rerun").resolve()
    if output_root != expected_parent:
        raise RuntimeError(f"worker output root escaped the declared rerun directory: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": "independent_rerun_worker_metadata_v1",
        "stage": args.stage,
        "run_id": args.run_id,
        "pid": __import__("os").getpid(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    if args.stage == "bundle":
        configure_benchmark(output_root, args.run_id)
        benchmark.COCYCLE_DIR.mkdir(parents=True, exist_ok=True)
        if any(benchmark.COCYCLE_DIR.iterdir()):
            raise RuntimeError("isolated cocycle cache was not empty at fresh-process start")
        benchmark.run_campaign(
            refresh_cocycle=True,
            max_wall_seconds=args.max_wall_seconds,
        )
        cache_files = sorted(benchmark.COCYCLE_DIR.glob("*.npz"))
        if len(cache_files) != benchmark.MAX_CASES:
            raise RuntimeError(f"fresh cocycle count {len(cache_files)} != {benchmark.MAX_CASES}")
        metadata["fresh_cocycle_files"] = len(cache_files)
    else:
        configure_manifold(output_root, args.run_id)
        if not manifold.METHOD_CSV.is_file() or not manifold.METHOD_NPZ.is_file():
            raise RuntimeError("manifold worker cannot find fresh-process bundle outputs")
        manifold.run_campaign(max_wall_seconds=args.max_wall_seconds)
    metadata["completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    metadata["status"] = "complete"
    path = output_root / "logs" / f"{args.stage}_worker_metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"independent rerun worker PASS stage={args.stage} pid={metadata['pid']}")


if __name__ == "__main__":
    main()
