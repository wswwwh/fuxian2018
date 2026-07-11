"""Cold-start the fixed-mapping quasi-DRO family in an isolated cache."""

from __future__ import annotations

import argparse
import csv
import hashlib
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.quasi_torus import corrected_dro_fixed_mapping_full_corrections


SMOKE_TARGETS = (2.92249,)
FULL_TARGETS = (2.9221, 2.9215, 2.9212)
FIELDS = (
    "mode",
    "cache_path",
    "cache_sha256",
    "member_count",
    "target_jacobi_values",
    "worst_target_error",
    "first_mean_jacobi",
    "last_mean_jacobi",
    "max_map_residual",
    "max_curve_jacobi_span",
    "rho_monotone",
    "jacobi_monotone",
    "elapsed_seconds",
    "status",
    "failure_reason",
)
ATTEMPT_FIELDS = (
    "attempt",
    "mode",
    "starting_member_count",
    "ending_member_count",
    "elapsed_seconds",
    "cache_sha256",
    "status",
    "failure_reason",
)


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.16g}" if np.isfinite(value) else "N/A"
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_partial_cache(cache_directory: Path) -> tuple[Any, ...]:
    candidates = sorted(cache_directory.glob("fixed_mapping_dro_v1_*.pkl"))
    if len(candidates) != 1:
        return ()
    try:
        with candidates[0].open("rb") as stream:
            value = pickle.load(stream)
    except (OSError, pickle.PickleError, EOFError):
        return ()
    return value if isinstance(value, tuple) else ()


def _write_audit(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow({field: _fmt(row.get(field, "")) for field in FIELDS})


def _append_attempt(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_rows: list[dict[str, str]] = []
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as stream:
            existing_rows = list(csv.DictReader(stream))
    attempt_row = {
        "attempt": len(existing_rows) + 1,
        **row,
    }
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=ATTEMPT_FIELDS)
        if not existing_rows:
            writer.writeheader()
        writer.writerow(
            {field: _fmt(attempt_row.get(field, "")) for field in ATTEMPT_FIELDS}
        )


def _write_doc(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Chapter 3 Fixed-Mapping Cold-Start Audit

## Result

- Mode: `{row['mode']}`
- Status: `{row['status']}`
- Members: `{row['member_count']}`
- Target Jacobi values: `{row['target_jacobi_values']}`
- Worst target error: `{_fmt(row['worst_target_error'])}`
- First / last mean Jacobi: `{_fmt(row['first_mean_jacobi'])}` / `{_fmt(row['last_mean_jacobi'])}`
- Max map residual: `{_fmt(row['max_map_residual'])}`
- Max curve Jacobi span: `{_fmt(row['max_curve_jacobi_span'])}`
- Rho monotone: `{_fmt(row['rho_monotone'])}`
- Jacobi monotone: `{_fmt(row['jacobi_monotone'])}`
- Cache SHA-256: `{row['cache_sha256']}`
- Elapsed seconds: `{_fmt(row['elapsed_seconds'])}`
- Failure reason: `{row['failure_reason'] or 'N/A'}`

## Boundary

`smoke` mode proves that the generator can start from equations/initial conditions,
advance the branch, target a nearby Jacobi value, and persist a deterministic cache
outside the canonical project cache. It does not reproduce the full Route H family.
Only `full` mode with all thesis targets and the downstream seven-gate audit can
close the Route H cold-start requirement.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument(
        "--cache-directory",
        type=Path,
        help="Isolated cache directory (defaults under outputs/cold_start).",
    )
    parser.add_argument("--audit-csv", type=Path)
    parser.add_argument("--audit-doc", type=Path)
    parser.add_argument("--attempt-log", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    system = SYSTEMS["earth_moon"]
    targets = SMOKE_TARGETS if args.mode == "smoke" else FULL_TARGETS
    cache_directory = (
        args.cache_directory
        or PROJECT_ROOT / "outputs" / "cold_start" / f"fixed_mapping_{args.mode}"
    ).resolve()
    audit_csv = args.audit_csv or (
        PROJECT_ROOT
        / "data"
        / "computed"
        / f"chapter3_fixed_mapping_cold_start_{args.mode}_audit.csv"
    )
    audit_doc = args.audit_doc or (
        PROJECT_ROOT / "docs" / f"chapter3_fixed_mapping_cold_start_{args.mode}_audit.md"
    )
    attempt_log = args.attempt_log or (
        PROJECT_ROOT
        / "data"
        / "computed"
        / f"chapter3_fixed_mapping_cold_start_{args.mode}_attempts.csv"
    )
    starting_member_count = len(_load_partial_cache(cache_directory))
    start = time.perf_counter()
    failure_reason = ""
    try:
        family = corrected_dro_fixed_mapping_full_corrections(
            system.mu,
            x0=1.0 - system.mu - 73800.0 / float(system.length_unit_km),
            thesis_jacobi_targets=targets,
            initial_samples=21,
            initial_half_period=14.75 / (2.0 * float(system.time_unit_days)),
            persistent_cache=True,
            cache_directory=cache_directory,
        )
    except Exception as error:  # Preserve a bounded failure audit and any atomic checkpoint.
        failure_reason = f"{type(error).__name__}: {error}"
        family = _load_partial_cache(cache_directory)
    elapsed = time.perf_counter() - start
    cache_paths = sorted(cache_directory.glob("fixed_mapping_dro_v1_*.pkl"))
    cache_path = cache_paths[0] if len(cache_paths) == 1 else None
    mean_jacobi = [
        float(np.mean(jacobi_constant(member.corrected_states, system.mu)))
        for member in family
    ]
    rho = [float(member.rotation_angle_rad) for member in family]
    residuals = [float(np.max(member.final_residual_norms)) for member in family]
    spans = [
        float(np.ptp(jacobi_constant(member.corrected_states, system.mu)))
        for member in family
    ]
    target_errors = [
        min((abs(value - target) for value in mean_jacobi), default=float("inf"))
        for target in targets
    ]
    worst_target_error = max(target_errors, default=float("inf"))
    rho_monotone = all(a < b for a, b in zip(rho, rho[1:]))
    jacobi_monotone = all(a > b for a, b in zip(mean_jacobi, mean_jacobi[1:]))
    status = "pass" if (
        not failure_reason
        and cache_path is not None
        and cache_path.resolve().is_relative_to(cache_directory)
        and len(family) >= 2
        and worst_target_error < 5.0e-7
        and max(residuals, default=float("inf")) < 1.0e-8
        and max(spans, default=float("inf")) < 2.0e-8
        and rho_monotone
        and jacobi_monotone
    ) else "fail"
    row = {
        "mode": args.mode,
        "cache_path": cache_path or "N/A",
        "cache_sha256": _sha256(cache_path) if cache_path else "N/A",
        "member_count": len(family),
        "target_jacobi_values": ";".join(_fmt(value) for value in targets),
        "worst_target_error": worst_target_error,
        "first_mean_jacobi": mean_jacobi[0] if mean_jacobi else float("nan"),
        "last_mean_jacobi": mean_jacobi[-1] if mean_jacobi else float("nan"),
        "max_map_residual": max(residuals, default=float("nan")),
        "max_curve_jacobi_span": max(spans, default=float("nan")),
        "rho_monotone": rho_monotone,
        "jacobi_monotone": jacobi_monotone,
        "elapsed_seconds": elapsed,
        "status": status,
        "failure_reason": failure_reason,
    }
    _write_audit(audit_csv, row)
    _write_doc(audit_doc, row)
    _append_attempt(
        attempt_log,
        {
            "mode": args.mode,
            "starting_member_count": starting_member_count,
            "ending_member_count": len(family),
            "elapsed_seconds": elapsed,
            "cache_sha256": row["cache_sha256"],
            "status": status,
            "failure_reason": failure_reason,
        },
    )
    print(
        f"cold-start {args.mode}: status={status}, members={len(family)}, "
        f"target_error={worst_target_error:.3e}, elapsed={elapsed:.3f}s",
        flush=True,
    )
    print(f"cache={cache_path or 'N/A'}", flush=True)
    print(f"audit={audit_csv}", flush=True)
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
