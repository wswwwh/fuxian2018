"""Build the isolated Stage-H submission-candidate preregistration registry.

This generator reads frozen reproduction and Stage-C research artifacts.  It
never writes those authorities.  Its outputs describe only the new Stage-H
campaign, bind every source state to a portable fingerprint, and preserve the
failed Chapter-4 and paper-equivalence boundaries.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.artifact_fingerprints import (  # noqa: E402
    artifact_fingerprint,
    lf_normalized_bytes,
    recorded_sha256_matches,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402


STAGE_H = (
    ROOT
    / "research"
    / "invariant_bundles"
    / "submission_candidate"
)
CONFIG = STAGE_H / "configs" / "stage_h_preregistration.json"
REGISTRY = STAGE_H / "benchmarks" / "stage_h_case_registry.csv"
REPORT = STAGE_H / "benchmarks" / "stage_h_preregistration.md"
LOCK = STAGE_H / "benchmarks" / "stage_h_preregistration_lock.json"

SCHEMA_VERSION = "submission_candidate_stage_h_case_registry_v1"
EXPECTED_CAMPAIGN_COUNTS = {
    "H2_stable_bundle": 3,
    "H3_route_h_2d_manifold": 2,
    "H4_long_propagation": 3,
    "H5_sun_earth_expansion": 3,
}

FIELDS = (
    "schema_version",
    "campaign",
    "case_id",
    "source_case_id",
    "member_id",
    "family",
    "system",
    "mu",
    "jacobi_or_energy",
    "mapping_time_days",
    "rho",
    "spectral_samples",
    "source_residual",
    "source_gate_status",
    "evidence_class",
    "state_artifact",
    "state_key",
    "state_artifact_hash_mode",
    "state_artifact_bytes",
    "state_artifact_sha256",
    "state_array_sha256",
    "source_metadata_artifact",
    "source_metadata_hash_mode",
    "source_metadata_bytes",
    "source_metadata_sha256",
    "selection_rule",
    "branch",
    "expected_bundle_dimension",
    "propagation_direction",
    "duration_mapping_periods",
    "time_samples",
    "perturbation_norms",
    "subspace_angular_samples",
    "methods",
    "event_condition",
    "minimum_outcome",
    "max_iterations",
    "max_retries",
    "max_wall_seconds",
    "frozen_baseline_commit",
    "h0_source_commit",
    "config_sha256",
)


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def _one(
    rows: Iterable[Mapping[str, str]],
    criteria: Mapping[str, str],
) -> dict[str, str]:
    matches = [
        dict(row)
        for row in rows
        if all(str(row.get(key, "")) == str(value) for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one metadata row for {dict(criteria)}, found {len(matches)}"
        )
    return matches[0]


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".16g")
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _portable_fields(path: Path, prefix: str) -> dict[str, str]:
    fingerprint = artifact_fingerprint(path)
    return {
        f"{prefix}_hash_mode": fingerprint.hash_mode,
        f"{prefix}_bytes": str(fingerprint.bytes),
        f"{prefix}_sha256": fingerprint.sha256,
    }


def _state_array_sha256(states: np.ndarray) -> str:
    values = np.ascontiguousarray(states)
    header = json.dumps(
        {"dtype": values.dtype.str, "shape": list(values.shape)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(header + b"\0" + values.tobytes()).hexdigest().upper()


def _load_states(path: Path, key: str) -> np.ndarray:
    if not path.is_file():
        raise RuntimeError(f"missing state artifact: {_rel(path)}")
    with np.load(path, allow_pickle=False) as archive:
        if key not in archive.files:
            raise RuntimeError(f"missing state key {_rel(path)}::{key}")
        states = np.asarray(archive[key], dtype=float)
    if states.ndim != 2 or states.shape[1] != 6:
        raise RuntimeError(
            f"state array {_rel(path)}::{key} must have shape (N, 6)"
        )
    if states.shape[0] < 3 or states.shape[0] % 2 == 0:
        raise RuntimeError("Stage-H state arrays require an odd sample count")
    if not np.all(np.isfinite(states)):
        raise RuntimeError(f"non-finite state array: {_rel(path)}::{key}")
    return states


def _existing_source(
    source_case_id: str,
    stage_c_index: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    if source_case_id not in stage_c_index:
        raise RuntimeError(f"unknown Stage-C source case: {source_case_id}")
    source = stage_c_index[source_case_id]
    state_artifact = ROOT / source["state_artifact"]
    metadata_artifact = ROOT / source["source_metadata_artifact"]
    states = _load_states(state_artifact, source["state_key"])
    if states.shape[0] != int(source["spectral_samples"]):
        raise RuntimeError(f"Stage-C sample count drifted for {source_case_id}")
    state_fingerprint = artifact_fingerprint(state_artifact)
    if state_fingerprint.sha256 != source["state_artifact_sha256"].upper():
        raise RuntimeError(f"Stage-C state artifact hash drifted for {source_case_id}")
    if not recorded_sha256_matches(
        metadata_artifact, source["source_metadata_sha256"]
    ):
        raise RuntimeError(f"Stage-C metadata hash drifted for {source_case_id}")
    return {
        "source_case_id": source_case_id,
        "member_id": source["member_id"],
        "family": source["family"],
        "system": source["system"],
        "mu": float(source["mu"]),
        "jacobi_or_energy": float(source["jacobi_or_energy"]),
        "mapping_time_days": float(source["mapping_time"]),
        "rho": float(source["rho"]),
        "spectral_samples": states.shape[0],
        "source_residual": float(source["source_residual"]),
        "source_gate_status": source["source_gate_status"],
        "evidence_class": source["evidence_class"],
        "state_artifact": state_artifact,
        "state_key": source["state_key"],
        "states": states,
        "source_metadata_artifact": metadata_artifact,
        "selection_rule": source["selection_rule"],
    }


def _checkpoint_source(specification: Mapping[str, Any]) -> dict[str, Any]:
    system_name = str(specification["system"])
    if system_name not in SYSTEMS:
        raise RuntimeError(f"unknown CR3BP system: {system_name}")
    system = SYSTEMS[system_name]
    state_artifact = ROOT / str(specification["state_artifact"])
    metadata_artifact = ROOT / str(specification["source_metadata_artifact"])
    state_key = str(specification["state_key"])
    states = _load_states(state_artifact, state_key)
    with np.load(state_artifact, allow_pickle=False) as archive:
        required = (
            str(specification["mapping_time_key"]),
            str(specification["rho_key"]),
            str(specification["jacobi_key"]),
        )
        missing = [key for key in required if key not in archive.files]
        if missing:
            raise RuntimeError(
                f"missing checkpoint scalar keys in {_rel(state_artifact)}: {missing}"
            )
        mapping_time = float(archive[required[0]])
        rho = float(archive[required[1]])
        jacobi_or_energy = float(archive[required[2]])
    unit = str(specification["mapping_time_unit"])
    if unit == "normalized":
        mapping_time_days = mapping_time * system.time_unit_days
    elif unit == "days":
        mapping_time_days = mapping_time
    else:
        raise RuntimeError(f"unknown mapping-time unit: {unit}")
    metadata_rows = _read_csv(metadata_artifact)
    metadata = _one(
        metadata_rows,
        {
            str(key): str(value)
            for key, value in specification["source_metadata_filter"].items()
        },
    )
    residual_field = str(specification["source_residual_field"])
    source_residual = float(metadata[residual_field])
    if not np.isfinite(source_residual):
        raise RuntimeError("checkpoint source residual must be finite")
    return {
        "source_case_id": "",
        "member_id": str(specification["member_id"]),
        "family": str(specification["family"]),
        "system": system_name,
        "mu": system.mu,
        "jacobi_or_energy": jacobi_or_energy,
        "mapping_time_days": mapping_time_days,
        "rho": rho,
        "spectral_samples": states.shape[0],
        "source_residual": source_residual,
        "source_gate_status": str(specification["source_gate_status"]),
        "evidence_class": str(specification["evidence_class"]),
        "state_artifact": state_artifact,
        "state_key": state_key,
        "states": states,
        "source_metadata_artifact": metadata_artifact,
        "selection_rule": str(specification["selection_rule"]),
    }


def _validate_frozen_truth(
    specification: Mapping[str, Any],
) -> dict[str, Any]:
    truth = specification["frozen_truth"]
    baseline_path = ROOT / str(truth["baseline_summary"])
    baseline_rows = _read_csv(baseline_path)
    observed_metrics = {row["metric_id"]: row["value"] for row in baseline_rows}
    expected_metrics = {
        str(key): str(value) for key, value in truth["baseline_metrics"].items()
    }
    for metric, expected in expected_metrics.items():
        observed = observed_metrics.get(metric)
        if observed != expected:
            raise RuntimeError(
                f"frozen baseline metric {metric} drifted: {observed!r} != {expected!r}"
            )
    holdout_path = ROOT / str(truth["chapter4_holdout"])
    holdout_rows = _read_csv(holdout_path)
    if len(holdout_rows) != int(truth["holdout_rows"]):
        raise RuntimeError("frozen Chapter-4 holdout row count drifted")
    for row in holdout_rows:
        if row["holdout_gate"] != str(truth["holdout_gate"]):
            raise RuntimeError("frozen Chapter-4 holdout gate was promoted")
        if (
            row["paper_projection_acceptance"]
            != str(truth["paper_projection_acceptance"])
        ):
            raise RuntimeError("frozen paper projection acceptance was promoted")
        if row["paper_3d_equivalence"].lower() != str(
            truth["paper_3d_equivalence"]
        ).lower():
            raise RuntimeError("frozen paper 3-D boundary was promoted")
    stage_c_path = ROOT / str(truth["stage_c_registry"])
    return {
        "baseline_metrics": expected_metrics,
        "frozen_baseline_commit": observed_metrics["source_git_commit"],
        "baseline": {
            "path": _rel(baseline_path),
            **_portable_fields(baseline_path, "artifact"),
        },
        "chapter4_holdout": {
            "path": _rel(holdout_path),
            "rows": len(holdout_rows),
            "passes": sum(row["holdout_gate"] == "pass" for row in holdout_rows),
            "paper_3d_true": sum(
                row["paper_3d_equivalence"].lower() == "true"
                for row in holdout_rows
            ),
            **_portable_fields(holdout_path, "artifact"),
        },
        "stage_c_registry": {
            "path": _rel(stage_c_path),
            **_portable_fields(stage_c_path, "artifact"),
        },
    }


def build() -> tuple[list[dict[str, str]], dict[str, Any], Mapping[str, Any]]:
    specification = json.loads(CONFIG.read_text(encoding="utf-8"))
    if (
        specification.get("schema_version")
        != "submission_candidate_stage_h_preregistration_v1"
    ):
        raise RuntimeError("unexpected Stage-H preregistration schema")
    truth = _validate_frozen_truth(specification)
    stage_c_path = ROOT / str(specification["frozen_truth"]["stage_c_registry"])
    stage_c_rows = _read_csv(stage_c_path)
    stage_c_index = {row["case_id"]: row for row in stage_c_rows}
    if len(stage_c_index) != len(stage_c_rows):
        raise RuntimeError("Stage-C registry contains duplicate case IDs")
    config_fingerprint = artifact_fingerprint(CONFIG)
    rows: list[dict[str, str]] = []
    source_records: dict[tuple[str, str], dict[str, str]] = {}
    seen_case_ids: set[str] = set()
    for entry in specification["campaigns"]:
        case_id = str(entry["case_id"])
        if case_id in seen_case_ids:
            raise RuntimeError(f"duplicate Stage-H case ID: {case_id}")
        seen_case_ids.add(case_id)
        source = (
            _existing_source(str(entry["source_case_id"]), stage_c_index)
            if "source_case_id" in entry
            else _checkpoint_source(entry["source"])
        )
        state_artifact = source["state_artifact"]
        metadata_artifact = source["source_metadata_artifact"]
        state_fields = _portable_fields(state_artifact, "state_artifact")
        metadata_fields = _portable_fields(
            metadata_artifact, "source_metadata"
        )
        source_records[
            (_rel(state_artifact), source["state_key"])
        ] = {
            "state_artifact": _rel(state_artifact),
            "state_key": source["state_key"],
            **state_fields,
            "state_array_sha256": _state_array_sha256(source["states"]),
        }
        row: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "campaign": entry["campaign"],
            "case_id": case_id,
            "source_case_id": source["source_case_id"],
            "member_id": source["member_id"],
            "family": source["family"],
            "system": source["system"],
            "mu": source["mu"],
            "jacobi_or_energy": source["jacobi_or_energy"],
            "mapping_time_days": source["mapping_time_days"],
            "rho": source["rho"],
            "spectral_samples": source["spectral_samples"],
            "source_residual": source["source_residual"],
            "source_gate_status": source["source_gate_status"],
            "evidence_class": source["evidence_class"],
            "state_artifact": _rel(state_artifact),
            "state_key": source["state_key"],
            **state_fields,
            "state_array_sha256": _state_array_sha256(source["states"]),
            "source_metadata_artifact": _rel(metadata_artifact),
            **metadata_fields,
            "selection_rule": source["selection_rule"],
            "branch": entry["branch"],
            "expected_bundle_dimension": entry["expected_bundle_dimension"],
            "propagation_direction": entry["propagation_direction"],
            "duration_mapping_periods": entry["duration_mapping_periods"],
            "time_samples": entry["time_samples"],
            "perturbation_norms": ";".join(
                _fmt(value) for value in entry["perturbation_norms"]
            ),
            "subspace_angular_samples": entry["subspace_angular_samples"],
            "methods": ";".join(str(value) for value in entry["methods"]),
            "event_condition": entry["event_condition"],
            "minimum_outcome": entry["minimum_outcome"],
            "max_iterations": entry["max_iterations"],
            "max_retries": entry["max_retries"],
            "max_wall_seconds": entry["max_wall_seconds"],
            "frozen_baseline_commit": truth["frozen_baseline_commit"],
            "h0_source_commit": specification["h0_source_commit"],
            "config_sha256": config_fingerprint.sha256,
        }
        rows.append({field: _fmt(row[field]) for field in FIELDS})
    counts = Counter(row["campaign"] for row in rows)
    if dict(counts) != EXPECTED_CAMPAIGN_COUNTS:
        raise RuntimeError(
            f"Stage-H campaign counts drifted: {dict(counts)}"
        )
    h3_rows = [
        row for row in rows if row["campaign"] == "H3_route_h_2d_manifold"
    ]
    if any(row["expected_bundle_dimension"] != "2" for row in h3_rows):
        raise RuntimeError("Route-H Stage-H cases must remain two-dimensional")
    h5_rows = [
        row for row in rows if row["campaign"] == "H5_sun_earth_expansion"
    ]
    if len({row["state_artifact"] for row in h5_rows}) != 3:
        raise RuntimeError("H5 must use three distinct frozen source artifacts")
    lock = {
        "schema_version": "submission_candidate_stage_h_preregistration_lock_v1",
        "config": {
            "path": _rel(CONFIG),
            "hash_mode": config_fingerprint.hash_mode,
            "bytes": config_fingerprint.bytes,
            "sha256": config_fingerprint.sha256,
        },
        "campaign_counts": dict(counts),
        "case_count": len(rows),
        "source_state_count": len(source_records),
        "source_states": [
            source_records[key] for key in sorted(source_records)
        ],
        "frozen_truth": truth,
        "stop_rule": specification["stop_rule"],
    }
    return rows, lock, specification


def _csv_text(rows: Iterable[Mapping[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=FIELDS,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _report_text(
    rows: list[dict[str, str]],
    lock: Mapping[str, Any],
    specification: Mapping[str, Any],
) -> str:
    counts = Counter(row["campaign"] for row in rows)
    lines = [
        "# Stage H submission-candidate preregistration",
        "",
        "This registry is isolated from the frozen reproduction and Stage A-G",
        "authorities. It may consume their artifacts but cannot promote them.",
        "",
        "## Frozen truth",
        "",
        f"- H0 source commit: {specification['h0_source_commit']}",
        f"- Frozen baseline source commit: {lock['frozen_truth']['frozen_baseline_commit']}",
        "- Engineering coverage: 54/54 (V0=13, V2=41)",
        "- Chapter 4 frozen projection holdout: 0/4; paper projection failed; paper 3-D false",
        "- Chapter 5 Fig. 5.10 paper equivalence: 0/2",
        "",
        "## Preregistered campaign counts",
        "",
    ]
    for campaign in EXPECTED_CAMPAIGN_COUNTS:
        lines.append(f"- {campaign}: {counts[campaign]}")
    lines += [
        "",
        "## Cases",
        "",
        "| campaign | case | source | branch | dim | periods | direction | cap |",
        "|---|---|---|---|---:|---:|---|---:|",
    ]
    for row in rows:
        source = row["source_case_id"] or row["member_id"]
        lines.append(
            f"| {row['campaign']} | {row['case_id']} | {source} | "
            f"{row['branch']} | {row['expected_bundle_dimension']} | "
            f"{row['duration_mapping_periods']} | {row['propagation_direction']} | "
            f"{row['max_wall_seconds']} s |"
        )
    lines += [
        "",
        "## Acceptance and stop boundary",
        "",
        "- H2 requires three completed stable-bundle cases and at least two accepted cases for a submission-candidate claim.",
        "- H3 keeps both physical Route H cases two-dimensional; no result may be relabeled as a one-dimensional direction.",
        "- H4 uses three fixed, preregistered long propagations and records exit diagnostics without post-hoc event changes.",
        "- H5 uses three distinct frozen Sun-Earth checkpoint artifacts selected before Stage-H method results exist.",
        "- Failed and boundary rows remain first-class evidence and cannot be deleted from denominators.",
        "",
        specification["stop_rule"],
        "",
        "Generated by scripts/build_submission_candidate_stage_h_registry.py.",
        "",
    ]
    return "\n".join(lines)


def render() -> tuple[str, str, str]:
    rows, lock, specification = build()
    csv_text = _csv_text(rows)
    report_text = _report_text(rows, lock, specification)
    lock_text = json.dumps(
        lock,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    return csv_text, report_text, lock_text


def _normalized_text(path: Path) -> str:
    return lf_normalized_bytes(path.read_bytes()).decode("utf-8")


def check_outputs() -> None:
    expected_csv, expected_report, expected_lock = render()
    expected = {
        REGISTRY: expected_csv,
        REPORT: expected_report,
        LOCK: expected_lock,
    }
    for path, text in expected.items():
        if not path.is_file():
            raise RuntimeError(f"missing generated Stage-H artifact: {_rel(path)}")
        if _normalized_text(path) != text:
            raise RuntimeError(f"generated Stage-H artifact drifted: {_rel(path)}")
    rows = _read_csv(REGISTRY)
    print(
        "STAGE-H PREREGISTRATION CHECK PASS "
        f"cases={len(rows)} sources={len({(row['state_artifact'], row['state_key']) for row in rows})}"
    )


def write_outputs() -> None:
    csv_text, report_text, lock_text = render()
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(csv_text, encoding="utf-8", newline="\n")
    REPORT.write_text(report_text, encoding="utf-8", newline="\n")
    LOCK.write_text(lock_text, encoding="utf-8", newline="\n")
    rows = _read_csv(REGISTRY)
    print(
        "STAGE-H PREREGISTRATION WRITE PASS "
        f"cases={len(rows)} campaigns={len({row['campaign'] for row in rows})}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        check_outputs()
    else:
        write_outputs()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
