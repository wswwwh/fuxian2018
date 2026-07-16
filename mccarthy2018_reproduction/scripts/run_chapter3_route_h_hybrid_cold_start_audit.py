"""Audit the hybrid Route H cold-start reconstruction chain."""

from __future__ import annotations

import csv
import hashlib
import pickle
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np

from _paths import PROJECT_ROOT
from qp_orbits.constants import SYSTEMS
from qp_orbits.cr3bp import jacobi_constant


DATA = PROJECT_ROOT / "data" / "computed"
DOCS = PROJECT_ROOT / "docs"
ATTEMPTS_PATH = DATA / "chapter3_fixed_mapping_cold_start_full_attempts.csv"
COLD_AUDIT_PATH = DATA / "chapter3_fixed_mapping_cold_start_full_audit.csv"
COVERAGE_PATH = DATA / "chapter3_route_h_fixed_time_target_coverage_audit.csv"
TARGET_STATES_PATH = DATA / "chapter3_route_h_fixed_time_target_states.csv"
REVALIDATION_PATH = DATA / "chapter3_route_h_target_state_revalidation.csv"
CHECKPOINT_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "cold_start"
    / "fixed_mapping_full"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
CSV_PATH = DATA / "chapter3_route_h_hybrid_cold_start_audit.csv"
DOC_PATH = DOCS / "chapter3_route_h_hybrid_cold_start_audit.md"
FIELDS = (
    "status",
    "zero_start_attempt_present",
    "controlled_fold_checkpoint_present",
    "checkpoint_member_count",
    "checkpoint_sha256",
    "checkpoint_hash_matches_attempt",
    "checkpoint_max_map_residual",
    "checkpoint_max_jacobi_span",
    "paper_precision_target_count",
    "strict_fixed_time_target_count",
    "projection_artifact_count",
    "state_target_count",
    "independently_revalidated_target_count",
    "chain_reproducible",
    "boundary",
)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _project_path(reference: str) -> Path:
    """Resolve a repository-relative artifact path on Windows or POSIX."""

    windows_path = PureWindowsPath(reference)
    relative = PurePosixPath(reference.replace("\\", "/"))
    if (
        windows_path.drive
        or windows_path.is_absolute()
        or relative.is_absolute()
        or ".." in relative.parts
    ):
        raise ValueError(f"invalid project-relative artifact path: {reference}")
    return PROJECT_ROOT.joinpath(*relative.parts)


def build_row() -> dict[str, object]:
    attempts = _read(ATTEMPTS_PATH)
    cold_audit = _read(COLD_AUDIT_PATH)
    coverage = _read(COVERAGE_PATH)
    zero_attempts = [
        row
        for row in attempts
        if row.get("mode") == "full" and int(row.get("starting_member_count", -1)) == 0
    ]
    controlled_fold = bool(
        zero_attempts
        and int(zero_attempts[0]["ending_member_count"]) >= 19
        and "lost monotonic direction" in zero_attempts[0].get("failure_reason", "")
    )
    with CHECKPOINT_PATH.open("rb") as stream:
        family = tuple(pickle.load(stream))
    mu = SYSTEMS["earth_moon"].mu
    max_residual = max(float(np.max(member.final_residual_norms)) for member in family)
    max_span = max(
        float(np.ptp(jacobi_constant(member.corrected_states, mu)))
        for member in family
    )
    digest = _sha256(CHECKPOINT_PATH)
    recorded_hashes = {
        row.get("cache_sha256", "").upper()
        for row in [*attempts, *cold_audit]
        if row.get("cache_sha256")
    }
    paper_count = sum(
        row.get("paper_reported_precision_status") == "pass" for row in coverage
    )
    strict_count = sum(row.get("strict_fixed_time_status") == "pass" for row in coverage)
    projection_paths = [_project_path(row["projection_artifact"]) for row in coverage]
    projection_count = sum(path.is_file() for path in projection_paths)
    target_states = _read(TARGET_STATES_PATH)
    state_target_count = len({row["target_jacobi"] for row in target_states})
    revalidation = _read(REVALIDATION_PATH)
    revalidated_count = sum(row.get("status") == "pass" for row in revalidation)
    chain_reproducible = bool(
        zero_attempts
        and controlled_fold
        and len(family) >= 19
        and digest in recorded_hashes
        and max_residual < 1.0e-8
        and max_span < 2.0e-8
        and len(coverage) == 4
        and paper_count == 4
        and strict_count >= 3
        and projection_count == 4
        and state_target_count == 4
        and len(revalidation) == 4
        and revalidated_count == 4
    )
    return {
        "status": "pass" if chain_reproducible else "fail",
        "zero_start_attempt_present": bool(zero_attempts),
        "controlled_fold_checkpoint_present": controlled_fold,
        "checkpoint_member_count": len(family),
        "checkpoint_sha256": digest,
        "checkpoint_hash_matches_attempt": digest in recorded_hashes,
        "checkpoint_max_map_residual": max_residual,
        "checkpoint_max_jacobi_span": max_span,
        "paper_precision_target_count": paper_count,
        "strict_fixed_time_target_count": strict_count,
        "projection_artifact_count": projection_count,
        "state_target_count": state_target_count,
        "independently_revalidated_target_count": revalidated_count,
        "chain_reproducible": chain_reproducible,
        "boundary": (
            "The monolithic natural/rotation continuation still terminates at its fold. "
            "Pass applies to the explicit hybrid chain: zero-start checkpoint, free-time "
            "fixed-Jacobi bridge, pointwise-energy time homotopy, and spectral lifts."
        ),
    }


def _write(row: dict[str, object]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)
    DOC_PATH.write_text(
        f"""# Chapter 3 Route H Hybrid Cold-Start Audit

## Result

- Status: `{row['status']}`
- Zero-cache start recorded: `{row['zero_start_attempt_present']}`
- Controlled fold checkpoint: `{row['controlled_fold_checkpoint_present']}`
- Checkpoint members: `{row['checkpoint_member_count']}`
- Checkpoint SHA-256: `{row['checkpoint_sha256']}`
- Hash matches attempt ledger: `{row['checkpoint_hash_matches_attempt']}`
- Checkpoint max map residual: `{float(row['checkpoint_max_map_residual']):.6e}`
- Checkpoint max Jacobi span: `{float(row['checkpoint_max_jacobi_span']):.6e}`
- Fixed-time anchors at paper precision: `{row['paper_precision_target_count']}/4`
- Internally strict fixed-time anchors: `{row['strict_fixed_time_target_count']}/4`
- Projection artifacts present: `{row['projection_artifact_count']}/4`
- Curve-state target groups present: `{row['state_target_count']}/4`
- Independently revalidated targets: `{row['independently_revalidated_target_count']}/4`

## Reproduction Chain

1. Start the fixed-mapping Route H generator with an empty isolated cache.
2. Preserve the validated 19-member checkpoint when natural/rotation continuation
   reaches the controlled `JC≈2.9222828` fold.
3. Solve the four requested Jacobi anchors with the fixed-Jacobi free-time bridge.
4. Return each anchor to the thesis mapping time using pointwise-energy STM Newton
   homotopy, applying spectral lifts where the collocation floor is reached.
5. Audit all four anchors against the paper-reported precision and residual gates.

## Boundary

{row['boundary']}
""",
        encoding="utf-8",
    )


def main() -> int:
    row = build_row()
    _write(row)
    print(
        f"Route H hybrid cold start: status={row['status']}, "
        f"targets={row['paper_precision_target_count']}/4, "
        f"strict={row['strict_fixed_time_target_count']}/4"
    )
    print(f"wrote {CSV_PATH.relative_to(PROJECT_ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(PROJECT_ROOT)}")
    return 0 if row["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
