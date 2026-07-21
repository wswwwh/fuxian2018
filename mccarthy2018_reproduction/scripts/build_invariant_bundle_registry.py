"""Build and verify the frozen Stage-C invariant-bundle benchmark registry."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
from io import BytesIO, StringIO
import os
from pathlib import Path
import pickle
import subprocess
import sys
from typing import Any, Iterable, Mapping
import zipfile

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.artifact_fingerprints import recorded_sha256_matches  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _trigonometric_interpolation_matrix,
    stroboscopic_invariant_curve_seed,
)


RESEARCH = ROOT / "research" / "invariant_bundles"
BENCHMARKS = RESEARCH / "benchmarks"
REGISTRY = BENCHMARKS / "benchmark_registry.csv"
STATE_EXTRACTS = BENCHMARKS / "benchmark_state_extracts.npz"
PROVENANCE = BENCHMARKS / "benchmark_provenance.md"

HALO_RESOLUTION = ROOT / "data" / "computed" / "research_halo_12p40_resolution_audit.csv"
HALO_STATES = ROOT / "data" / "computed" / "research_halo_12p40_resolution_states.npz"
VERTICAL_RESOLUTION = ROOT / "data" / "computed" / "research_vertical_12p66_resolution_audit.csv"
VERTICAL_STATES = ROOT / "data" / "computed" / "research_vertical_12p66_resolution_states.npz"
HALO_HIGH_ORDER = ROOT / "data" / "computed" / "chapter3_corrected_constant_energy_halo_high_order_family.csv"
HALO_HIGH_ORDER_CACHE = (
    ROOT / "data" / "computed" / "cache" / "quasi_halo_high_order_v1_68dc7a7f21096967.pkl"
)
HALO_N9_FAMILY = ROOT / "data" / "computed" / "chapter3_corrected_constant_energy_halo_pseudo_arclength_family.csv"
HALO_N9_STATES = ROOT / "data" / "computed" / "chapter4_fig43_fig44_global_manifold_audit.npz"
ROUTE_H_AUDIT = ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_audit.csv"
ROUTE_H_SPECTRUM = ROOT / "data" / "computed" / "chapter4_real_hyperbolic_scan.csv"
ROUTE_H_CACHE = ROOT / "data" / "computed" / "cache" / "fixed_mapping_dro_v1_079947170b953a50.pkl"
SUN_ACTIVE_AUDIT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_audit.csv"
SUN_ACTIVE_CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz"
SUN_SMALL_AUDIT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_resolution_lift_audit.csv"
SUN_SMALL_CHECKPOINT = ROOT / "data" / "computed" / "chapter5_sun_earth_l1_quasi_halo_21point_checkpoint.npz"

SCHEMA_VERSION = "invariant_bundle_benchmark_registry_v1"
REQUIRED_FIELDS = (
    "case_id",
    "family",
    "member_id",
    "system",
    "mu",
    "jacobi_or_energy",
    "mapping_time",
    "rho",
    "spectral_samples",
    "state_artifact",
    "source_residual",
    "expected_bundle_type",
    "positive_or_negative_control",
    "provenance",
    "git_commit",
)
FIELDS = REQUIRED_FIELDS + (
    "schema_version",
    "mapping_time_unit",
    "state_key",
    "state_artifact_sha256",
    "source_metadata_artifact",
    "source_metadata_sha256",
    "selection_rule",
    "source_gate_status",
    "evidence_class",
    "notes",
)


@dataclass(frozen=True)
class BuildResult:
    rows: tuple[dict[str, Any], ...]
    state_arrays: Mapping[str, np.ndarray]


def _rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _bytes_sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _one(rows: Iterable[dict[str, str]], **criteria: object) -> dict[str, str]:
    matches = [
        row
        for row in rows
        if all(str(row.get(key)) == str(value) for key, value in criteria.items())
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one row for {criteria}, found {len(matches)}")
    return matches[0]


def _git_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _load_pickle_tuple(path: Path) -> tuple[Any, ...]:
    with path.open("rb") as stream:
        value = pickle.load(stream)
    if not isinstance(value, tuple):
        raise RuntimeError(f"expected tuple in {_rel(path)}")
    return value


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return f"{number:.16g}" if np.isfinite(number) else str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _deterministic_npz_bytes(arrays: Mapping[str, np.ndarray]) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as archive:
        for key in sorted(arrays):
            npy = BytesIO()
            np.lib.format.write_array(npy, np.asarray(arrays[key]), allow_pickle=False)
            info = zipfile.ZipInfo(f"{key}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, npy.getvalue(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def _row(
    *,
    commit: str,
    case_id: str,
    family: str,
    member_id: str,
    system: str,
    jacobi: float,
    mapping_days: float,
    rho: float,
    samples: int,
    state_artifact: Path,
    state_key: str,
    source_residual: float,
    expected_bundle_type: str,
    control: str,
    provenance: str,
    source_metadata: Path,
    selection_rule: str,
    source_gate_status: str,
    evidence_class: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "family": family,
        "member_id": member_id,
        "system": system,
        "mu": SYSTEMS[system].mu,
        "jacobi_or_energy": jacobi,
        "mapping_time": mapping_days,
        "rho": rho,
        "spectral_samples": samples,
        "state_artifact": _rel(state_artifact),
        "source_residual": source_residual,
        "expected_bundle_type": expected_bundle_type,
        "positive_or_negative_control": control,
        "provenance": provenance,
        "git_commit": commit,
        "schema_version": SCHEMA_VERSION,
        "mapping_time_unit": "days",
        "state_key": state_key,
        "state_artifact_sha256": "__STATE_HASH__" if state_artifact == STATE_EXTRACTS else _sha256(state_artifact),
        "source_metadata_artifact": _rel(source_metadata),
        "source_metadata_sha256": _sha256(source_metadata),
        "selection_rule": selection_rule,
        "source_gate_status": source_gate_status,
        "evidence_class": evidence_class,
        "notes": notes,
    }


def build(*, source_commit: str | None = None) -> BuildResult:
    commit = source_commit or _git_commit()
    earth_moon = SYSTEMS["earth_moon"]
    sun_earth = SYSTEMS["sun_earth"]
    rows: list[dict[str, Any]] = []
    state_arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "source_git_commit": np.asarray([commit]),
    }

    halo_rows = _read_csv(HALO_RESOLUTION)
    with np.load(HALO_STATES, allow_pickle=False) as states:
        for samples, control in ((21, "positive"), (33, "boundary"), (45, "boundary")):
            audit = _one(halo_rows, spectral_samples=samples)
            key = f"n{samples}_source_states"
            if np.asarray(states[key]).shape != (samples, 6):
                raise RuntimeError(f"invalid halo state shape for N={samples}")
            rows.append(
                _row(
                    commit=commit,
                    case_id=f"em_halo_12p40_n{samples}",
                    family="earth_moon_l1_quasi_halo",
                    member_id=f"12p40_n{samples}",
                    system="earth_moon",
                    jacobi=float(audit["target_jacobi"]),
                    mapping_days=float(audit["mapping_time_days"]),
                    rho=float(audit["rotation_angle_rad"]),
                    samples=samples,
                    state_artifact=HALO_STATES,
                    state_key=key,
                    source_residual=float(audit["curve_residual"]),
                    expected_bundle_type="real_1d_hyperbolic",
                    control=control,
                    provenance="Stage-B direct spectral lift of the predeclared 12.40-day physical member",
                    source_metadata=HALO_RESOLUTION,
                    selection_rule=f"spectral_samples == {samples}",
                    source_gate_status=audit["overall_status"],
                    evidence_class="research_stage_b",
                    notes="Frozen Chapter-4 projection holdout remains failed and is not used for source selection.",
                )
            )

    high_order_rows = _read_csv(HALO_HIGH_ORDER)
    small_halo_meta = _one(high_order_rows, stage="N9-to-N15", curve_samples=15, member_index=0)
    high_order_cache = _load_pickle_tuple(HALO_HIGH_ORDER_CACHE)
    small_halo = high_order_cache[0]
    small_key = "em_halo_12p09_n15_small_states"
    state_arrays[small_key] = np.asarray(small_halo.corrected_states)
    state_arrays[small_key.replace("_states", "_phases")] = np.asarray(small_halo.seed.phases)
    if abs(float(small_halo.mapping_time) * earth_moon.time_unit_days - float(small_halo_meta["mapping_time_days"])) > 1.0e-10:
        raise RuntimeError("small-halo cache and metadata mapping time disagree")
    if abs(float(small_halo.rotation_angle_rad) - float(small_halo_meta["rotation_angle_rad"])) > 1.0e-10:
        raise RuntimeError("small-halo cache and metadata rotation disagree")
    rows.append(
        _row(
            commit=commit,
            case_id="em_halo_12p09_n15_small",
            family="earth_moon_l1_quasi_halo",
            member_id="high_order_member_0",
            system="earth_moon",
            jacobi=float(small_halo_meta["target_jacobi"]),
            mapping_days=float(small_halo_meta["mapping_time_days"]),
            rho=float(small_halo_meta["rotation_angle_rad"]),
            samples=15,
            state_artifact=STATE_EXTRACTS,
            state_key=small_key,
            source_residual=float(small_halo_meta["curve_residual"]),
            expected_bundle_type="real_1d_hyperbolic_candidate",
            control="positive_candidate",
            provenance="Accepted N9-to-N15 high-order family member 0; minimal state extract from the hashed correction cache",
            source_metadata=HALO_HIGH_ORDER,
            selection_rule="stage == N9-to-N15 and curve_samples == 15 and member_index == 0",
            source_gate_status="accepted_source",
            evidence_class="accepted_reproduction_source",
            notes=f"Correction cache sha256={_sha256(HALO_HIGH_ORDER_CACHE)}",
        )
    )

    n9_rows = _read_csv(HALO_N9_FAMILY)
    n9_meta = _one(n9_rows, member_index=26)
    with np.load(HALO_N9_STATES, allow_pickle=False) as states:
        n9_states = np.asarray(states["plus_x_source_states"])
        if n9_states.shape != (9, 6):
            raise RuntimeError("invalid legacy N9 state shape")
    rows.append(
        _row(
            commit=commit,
            case_id="em_halo_12p097_n9_lowres_negative",
            family="earth_moon_l1_quasi_halo",
            member_id="pseudo_arclength_26",
            system="earth_moon",
            jacobi=float(n9_meta["target_jacobi"]),
            mapping_days=float(n9_meta["mapping_time_days"]),
            rho=float(n9_meta["rotation_angle_rad"]),
            samples=9,
            state_artifact=HALO_N9_STATES,
            state_key="plus_x_source_states",
            source_residual=float(n9_meta["curve_residual"]),
            expected_bundle_type="real_1d_hyperbolic_low_resolution",
            control="negative",
            provenance="Frozen current N9 Chapter-4 source retained as the required low-resolution counterexample",
            source_metadata=HALO_N9_FAMILY,
            selection_rule="member_index == 26",
            source_gate_status="source_pass_projection_fail",
            evidence_class="frozen_reproduction_negative_control",
            notes="This case is not promoted by the Stage-B 12.40-day diagnostic.",
        )
    )

    vertical_rows = _read_csv(VERTICAL_RESOLUTION)
    with np.load(VERTICAL_STATES, allow_pickle=False) as states:
        for samples, control in ((33, "positive"), (45, "boundary"), (57, "negative")):
            audit = _one(vertical_rows, spectral_samples=samples)
            key = f"n{samples}_source_states"
            if np.asarray(states[key]).shape != (samples, 6):
                raise RuntimeError(f"invalid vertical state shape for N={samples}")
            rows.append(
                _row(
                    commit=commit,
                    case_id=f"em_vertical_12p66_n{samples}",
                    family="earth_moon_l1_quasi_vertical",
                    member_id=f"12p66_n{samples}",
                    system="earth_moon",
                    jacobi=float(audit["target_jacobi"]),
                    mapping_days=float(audit["mapping_time_days"]),
                    rho=float(audit["rotation_angle_rad"]),
                    samples=samples,
                    state_artifact=VERTICAL_STATES,
                    state_key=key,
                    source_residual=float(audit["curve_residual"]),
                    expected_bundle_type="real_1d_hyperbolic",
                    control=control,
                    provenance="Stage-B direct spectral lift of the predeclared 12.66-day quasi-vertical endpoint",
                    source_metadata=VERTICAL_RESOLUTION,
                    selection_rule=f"spectral_samples == {samples}",
                    source_gate_status=audit["overall_status"],
                    evidence_class="research_stage_b",
                    notes="N57 remains a failed source-gate row; it is deliberately retained.",
                )
            )

    route_rows = _read_csv(ROUTE_H_AUDIT)
    route_spectrum = _read_csv(ROUTE_H_SPECTRUM)
    route_cache = _load_pickle_tuple(ROUTE_H_CACHE)
    route_cases = (
        (
            68,
            "real_1d_hyperbolic_frozen_claim_under_test",
            "positive_claim_under_test",
            "physical corrected-rho retest of the frozen near-real claim",
        ),
        (17, "real_2d_complex_pair_subspace", "negative", "strong complex-direction negative control"),
        (32, "real_2d_complex_pair_subspace", "negative", "complex-direction negative control"),
        (54, "real_2d_complex_pair_subspace", "negative", "maximum-amplitude complex-spectrum case"),
    )
    for member, expected, control, note in route_cases:
        audit = _one(route_rows, member_index=member)
        spectrum = _one(route_spectrum, member_index=member)
        correction = route_cache[member]
        key = f"route_h_member_{member}_states"
        phase_key = key.replace("_states", "_phases")
        state_arrays[key] = np.asarray(correction.corrected_states)
        state_arrays[phase_key] = np.asarray(correction.seed.phases)
        if state_arrays[key].shape != (45, 6):
            raise RuntimeError(f"invalid Route-H member {member} state shape")
        if abs(float(correction.rotation_angle_rad) - float(audit["rho_rad"])) > 1.0e-10:
            raise RuntimeError(f"Route-H member {member} rotation disagrees")
        rows.append(
            _row(
                commit=commit,
                case_id=f"route_h_member_{member}",
                family="earth_moon_route_h_quasi_dro",
                member_id=str(member),
                system="earth_moon",
                jacobi=float(audit["mean_jacobi"]),
                mapping_days=float(audit["mapping_time_days"]),
                rho=float(audit["rho_rad"]),
                samples=int(audit["curve_samples"]),
                state_artifact=STATE_EXTRACTS,
                state_key=key,
                source_residual=float(audit["map_residual_max"]),
                expected_bundle_type=expected,
                control=control,
                provenance="Strict Route-H fixed-mapping cache member using its corrected physical rotation; frozen scan status retained only as a legacy comparison",
                source_metadata=ROUTE_H_SPECTRUM,
                selection_rule=f"member_index == {member}",
                source_gate_status=(
                    f"frozen_legacy_dg_{spectrum['real_hyperbolic_status']}_physical_rho_retest"
                ),
                evidence_class="accepted_source_research_spectrum_control",
                notes=f"{note}; correction cache sha256={_sha256(ROUTE_H_CACHE)}",
            )
        )

    legacy_member = 68
    legacy_audit = _one(route_rows, member_index=legacy_member)
    legacy_spectrum = _one(route_spectrum, member_index=legacy_member)
    legacy_correction = route_cache[legacy_member]
    legacy_rho = float(legacy_correction.seed.rotation_angle_rad)
    legacy_target = _trigonometric_interpolation_matrix(
        legacy_correction.seed.phases,
        legacy_correction.seed.phases + legacy_rho,
    ) @ np.asarray(legacy_correction.corrected_states)
    legacy_residual = float(
        np.max(
            np.linalg.norm(
                np.asarray(legacy_correction.corrected_mapped_states)
                - legacy_target,
                axis=1,
            )
        )
    )
    rows.append(
        _row(
            commit=commit,
            case_id="route_h_member_68_legacy_dg_positive",
            family="earth_moon_route_h_quasi_dro",
            member_id="68_legacy_seed_rho",
            system="earth_moon",
            jacobi=float(legacy_audit["mean_jacobi"]),
            mapping_days=float(legacy_audit["mapping_time_days"]),
            rho=legacy_rho,
            samples=int(legacy_audit["curve_samples"]),
            state_artifact=STATE_EXTRACTS,
            state_key="route_h_member_68_states",
            source_residual=legacy_residual,
            expected_bundle_type="real_1d_hyperbolic_legacy_dg",
            control="positive_legacy_dg",
            provenance="Frozen Chapter-4 real-hyperbolic positive control replayed with the seed rotation used by legacy corrected_curve_dg",
            source_metadata=ROUTE_H_SPECTRUM,
            selection_rule="member_index == 68 and rho == correction.seed.rotation_angle_rad",
            source_gate_status=legacy_spectrum["real_hyperbolic_status"],
            evidence_class="frozen_algorithmic_positive_control_not_physical_source",
            notes=(
                "The physical corrected rho remains a separate registry case; "
                f"legacy map residual={legacy_residual:.16g}."
            ),
        )
    )

    active_audit = _read_csv(SUN_ACTIVE_AUDIT)[0]
    with np.load(SUN_ACTIVE_CHECKPOINT, allow_pickle=False) as active:
        if int(active["accepted"]) != 468:
            raise RuntimeError("Sun-Earth active checkpoint is not member 468")
        active_states = np.asarray(active["states"])
        if active_states.shape != (21, 6):
            raise RuntimeError("invalid Sun-Earth active checkpoint shape")
        active_mapping_days = float(active["mapping_time"]) * sun_earth.time_unit_days
        active_rho = float(active["rotation"])
        active_jacobi = float(active["jacobi"])
    rows.append(
        _row(
            commit=commit,
            case_id="se_active_geometry_member_468",
            family="sun_earth_l1_two_frequency_torus",
            member_id="468",
            system="sun_earth",
            jacobi=active_jacobi,
            mapping_days=active_mapping_days,
            rho=active_rho,
            samples=21,
            state_artifact=SUN_ACTIVE_CHECKPOINT,
            state_key="states",
            source_residual=float(active_audit["combined_metric"]),
            expected_bundle_type="to_be_classified_real_1d_or_2d",
            control="research_target",
            provenance="Accepted active-geometry member 468 from the saved family checkpoint; no new amplitude continuation",
            source_metadata=SUN_ACTIVE_AUDIT,
            selection_rule="accepted_members == 468",
            source_gate_status="accepted_active_geometry",
            evidence_class="accepted_reproduction_source",
            notes="Research classification cannot promote the Chapter-5 paper-equivalence gate.",
        )
    )

    small_sun_rows = _read_csv(SUN_SMALL_AUDIT)
    small_sun_meta = _one(small_sun_rows, member="continued_half_percent_2")
    with np.load(SUN_SMALL_CHECKPOINT, allow_pickle=False) as small:
        small_states = np.asarray(small["current_states"])
        small_rho = float(small["current_rotation"])
        x_amplitude = float(small["x_amplitude"])
        samples = int(small["samples"])
    seed = stroboscopic_invariant_curve_seed(
        sun_earth.mu,
        point="L1",
        x_amplitude=x_amplitude,
        vertical_amplitude=1.0e-5,
        samples=samples,
        curve_samples=168,
    )
    small_mapping_days = float(seed.orbit_period) * sun_earth.time_unit_days
    small_jacobi = float(np.mean(jacobi_constant(small_states, sun_earth.mu)))
    rows.append(
        _row(
            commit=commit,
            case_id="se_quasi_halo_small_n21",
            family="sun_earth_l1_two_frequency_torus",
            member_id="continued_half_percent_2",
            system="sun_earth",
            jacobi=small_jacobi,
            mapping_days=small_mapping_days,
            rho=small_rho,
            samples=samples,
            state_artifact=SUN_SMALL_CHECKPOINT,
            state_key="current_states",
            source_residual=float(small_sun_meta["curve_residual_norm"]),
            expected_bundle_type="to_be_classified_real_1d_or_2d",
            control="research_target",
            provenance="Saved 21-point smaller-amplitude Sun-Earth checkpoint selected without extending the branch",
            source_metadata=SUN_SMALL_AUDIT,
            selection_rule="member == continued_half_percent_2 and state_key == current_states",
            source_gate_status="accepted_source_target_pair_false",
            evidence_class="boundary_reproduction_source",
            notes="Smaller in vertical extent than member 468; the target pair remains unaccepted.",
        )
    )

    if len(rows) != 15 or len({row["case_id"] for row in rows}) != 15:
        raise RuntimeError("Stage-C registry must contain 15 unique cases")
    if len({row["family"] for row in rows}) != 4:
        raise RuntimeError("Stage-C registry must contain four families")
    return BuildResult(tuple(rows), state_arrays)


def _csv_bytes(rows: Iterable[Mapping[str, Any]]) -> bytes:
    output = BytesIO()
    text = []
    text.append(",".join(FIELDS))
    for row in rows:
        formatted = {field: _fmt(row.get(field, "")) for field in FIELDS}
        line = BytesIO()
        wrapper = __import__("io").TextIOWrapper(line, encoding="utf-8", newline="", write_through=True)
        csv.writer(wrapper, lineterminator="\n").writerow([formatted[field] for field in FIELDS])
        wrapper.detach()
        text.append(line.getvalue().decode("utf-8").rstrip("\n"))
    return ("\n".join(text) + "\n").encode("utf-8")


def _provenance_text(rows: tuple[dict[str, Any], ...], state_hash: str) -> str:
    families: dict[str, int] = {}
    controls: dict[str, int] = {}
    for row in rows:
        families[row["family"]] = families.get(row["family"], 0) + 1
        controls[row["positive_or_negative_control"]] = controls.get(row["positive_or_negative_control"], 0) + 1
    lines = [
        "# Invariant-bundle benchmark provenance",
        "",
        f"- Schema: `{SCHEMA_VERSION}`",
        f"- Source Git commit: `{rows[0]['git_commit']}`",
        f"- Cases: `{len(rows)}`",
        f"- Families: `{len(families)}`",
        f"- Minimal state-extract SHA256: `{state_hash}`",
        "- Mapping-time unit in the registry: `days`",
        "- The registry references frozen authoritative artifacts and never writes reproduction acceptance tables.",
        "",
        "## Family coverage",
        "",
    ]
    lines.extend(f"- `{family}`: `{count}` cases" for family, count in sorted(families.items()))
    lines += ["", "## Control coverage", ""]
    lines.extend(f"- `{control}`: `{count}` cases" for control, count in sorted(controls.items()))
    lines += [
        "",
        "## Boundary lock",
        "",
        "Stage-C classifications are research-only. They do not change the frozen Chapter-4 camera holdout,",
        "the 54-figure validation table, any source gate, or any paper-equivalence claim. Failed and boundary",
        "rows are deliberately retained as controls.",
        "",
        "## Case provenance",
        "",
        "| case | source metadata | state artifact / key | source gate | role |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['case_id']}` | `{row['source_metadata_artifact']}` | "
            f"`{row['state_artifact']}::{row['state_key']}` | `{row['source_gate_status']}` | "
            f"`{row['positive_or_negative_control']}` |"
        )
    return "\n".join(lines) + "\n"


def render(*, source_commit: str | None = None) -> tuple[bytes, bytes, bytes]:
    result = build(source_commit=source_commit)
    state_payload = _deterministic_npz_bytes(result.state_arrays)
    state_hash = _bytes_sha256(state_payload)
    rows = tuple(
        {
            **row,
            "state_artifact_sha256": state_hash
            if row["state_artifact"] == _rel(STATE_EXTRACTS)
            else row["state_artifact_sha256"],
        }
        for row in result.rows
    )
    return _csv_bytes(rows), state_payload, _provenance_text(rows, state_hash).encode("utf-8")


def _check_file(path: Path, expected: bytes) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing generated artifact: {_rel(path)}")
    if path.read_bytes() != expected:
        raise RuntimeError(f"generated artifact drifted: {_rel(path)}")


def _check_registry(expected: bytes) -> None:
    actual_rows = _read_csv(REGISTRY)
    expected_rows = list(csv.DictReader(StringIO(expected.decode("utf-8"))))
    if len(actual_rows) != len(expected_rows):
        raise RuntimeError(f"generated artifact drifted: {_rel(REGISTRY)}")
    for actual, candidate in zip(actual_rows, expected_rows, strict=True):
        for field in FIELDS:
            if field == "source_metadata_sha256":
                metadata = ROOT / actual["source_metadata_artifact"]
                if not recorded_sha256_matches(metadata, actual[field]):
                    raise RuntimeError(
                        "frozen source metadata hash no longer matches: "
                        f"{actual['source_metadata_artifact']}"
                    )
                continue
            if actual[field] != candidate[field]:
                raise RuntimeError(
                    f"generated artifact drifted: {_rel(REGISTRY)} "
                    f"case={actual.get('case_id')} field={field}"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source_commit: str | None = None
    if args.check:
        existing = _read_csv(REGISTRY)
        frozen_commits = {row["git_commit"] for row in existing}
        if len(frozen_commits) != 1:
            raise RuntimeError(
                "benchmark registry must contain one frozen source Git commit"
            )
        source_commit = frozen_commits.pop()
    registry, states, provenance = render(source_commit=source_commit)
    if args.check:
        _check_registry(registry)
        _check_file(STATE_EXTRACTS, states)
        _check_file(PROVENANCE, provenance)
        print("invariant-bundle registry CHECK PASS cases=15 families=4")
        return 0
    BENCHMARKS.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_bytes(registry)
    STATE_EXTRACTS.write_bytes(states)
    PROVENANCE.write_bytes(provenance)
    print("invariant-bundle registry WRITE PASS cases=15 families=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
