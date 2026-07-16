"""Run the predeclared Chapter 4 halo and vertical resolution audits.

All source corrections, DG matrices, directions, and manifold sheets are built
before any exposed paper mask is opened. Projection metrics are post-hoc
development diagnostics and cannot change the frozen v1 holdout.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import pickle
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_projection import (  # noqa: E402
    load_reference_panel_mask,
    project_surface_uv,
    projection_mask_metrics,
    rasterize_surface_mask,
)
from qp_orbits.chapter4_reproduction_lock import (  # noqa: E402
    load_chapter4_reproduction_lock,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import jacobi_constant  # noqa: E402
from qp_orbits.quasi_torus import (  # noqa: E402
    _trigonometric_interpolation_matrix,
    corrected_l1_constant_energy_vertical_staged_corrections,
    stroboscopic_curve_free_energy_correction,
    stroboscopic_spatial_jacobi_seed,
)
from qp_orbits.torus_stability import (  # noqa: E402
    corrected_curve_dg,
    corrected_curve_fixed_time_manifold_snapshots,
    corrected_l1_constant_energy_halo_high_order_dg_family,
    real_hyperbolic_eigen_index,
)


SCHEMA_VERSION = "chapter4_source_resolution_audit_v1"
CACHE_VERSION = 1
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CACHE = DATA / "cache"
PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
CAMERA_NPZ = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
BASELINE_LOCK = DATA / "reproduction_baseline_v1_lock.json"

HALO_RESOLUTIONS = (21, 33, 45)
VERTICAL_RESOLUTIONS = (33, 45, 57)
COMMON_PHASE_SAMPLES = 181
PHASE_SAMPLES = 121
HISTORY_SAMPLES = 161
MAX_ITERATIONS = 64
MAX_STEP = 0.01

HALO_TARGET_PERIOD_DAYS = 12.397983401715157
VERTICAL_TARGET_PERIOD_DAYS = 12.664796510496439
HALO_SNAPSHOT_DAYS = (7.79, 9.75, 11.39, 13.02)
VERTICAL_SNAPSHOT_DAYS = (8.05, 10.08, 11.77, 13.46)

CURVE_RESIDUAL_MAX = 1.0e-9
JACOBI_SPAN_MAX = 1.0e-6
DETERMINANT_ERROR_MAX = 5.0e-9
RELATIVE_IMAGINARY_MAX = 1.0e-10
UNSTABLE_RING_DISPERSION_MAX = 6.0e-2
MANIFOLD_JACOBI_DRIFT_MAX = 1.0e-10
MULTIPLIER_RELATIVE_CHANGE_MAX = 1.0e-3
PRINCIPAL_ANGLE_MAX_DEG = 5.0
SHEET_HD95_NORMALIZED_MAX = 1.0e-2

CHAMFER_MAX_FRACTION = 0.02
F1_MIN = 0.70
PROJECTION_HD95_MAX_FRACTION = 0.05
AREA_RATIO_MIN = 0.67
AREA_RATIO_MAX = 1.50

OUTPUTS = {
    "halo": {
        "csv": DATA / "research_halo_12p40_resolution_audit.csv",
        "npz": DATA / "research_halo_12p40_resolution_states.npz",
        "doc": DOCS / "research_halo_12p40_resolution_audit.md",
    },
    "vertical": {
        "csv": DATA / "research_vertical_12p66_resolution_audit.csv",
        "npz": DATA / "research_vertical_12p66_resolution_states.npz",
        "doc": DOCS / "research_vertical_12p66_resolution_audit.md",
    },
}

CSV_COLUMNS = (
    "schema_version",
    "campaign",
    "family",
    "spectral_samples",
    "source_selection",
    "source_selection_red_mask_read",
    "projection_red_mask_read",
    "target_jacobi",
    "baseline_period_days",
    "mapping_time_days",
    "rotation_angle_rad",
    "period_change_from_baseline_days",
    "source_ay_km",
    "source_az_km",
    "curve_residual",
    "source_jacobi_span",
    "bundle_dimension",
    "selected_unstable_eigenvalue_real",
    "selected_unstable_eigenvalue_imag",
    "selected_unstable_multiplier",
    "selected_relative_imaginary",
    "eigenpair_residual",
    "dg_determinant",
    "dg_determinant_error",
    "unstable_ring_count",
    "unstable_ring_relative_dispersion",
    "phase_shift_to_baseline_deg",
    "direction_sign_to_baseline",
    "base_state_rms_to_baseline",
    "principal_angle_mean_to_baseline_deg",
    "principal_angle_max_to_baseline_deg",
    "principal_angle_mean_to_previous_deg",
    "principal_angle_max_to_previous_deg",
    "multiplier_relative_change_to_baseline",
    "multiplier_relative_change_to_previous",
    "sheet_hd95_raw_mean_to_baseline",
    "sheet_hd95_raw_max_to_baseline",
    "sheet_hd95_normalized_mean_to_baseline",
    "sheet_hd95_normalized_max_to_baseline",
    "sheet_hd95_raw_mean_to_previous",
    "sheet_hd95_raw_max_to_previous",
    "sheet_hd95_normalized_mean_to_previous",
    "sheet_hd95_normalized_max_to_previous",
    "manifold_jacobi_drift_max",
    "positive_x_chamfer_fraction",
    "positive_x_f1",
    "positive_x_hd95_fraction",
    "positive_x_area_ratio",
    "positive_x_posthoc_projection_gate",
    "negative_x_chamfer_fraction",
    "negative_x_f1",
    "negative_x_hd95_fraction",
    "negative_x_area_ratio",
    "negative_x_posthoc_projection_gate",
    "posthoc_projection_pass_count",
    "source_gate",
    "cross_resolution_gate",
    "posthoc_projection_status",
    "overall_status",
    "failure_reason",
    "correction_runtime_seconds",
    "dg_runtime_seconds",
    "manifold_runtime_seconds",
    "projection_runtime_seconds",
    "total_runtime_seconds",
    "correction_cache_hit",
    "frozen_holdout_status",
    "paper_projection_acceptance",
    "paper_3d_equivalence",
    "source_git_commit",
    "generator_sha256",
    "quasi_torus_sha256",
    "torus_stability_sha256",
    "projection_core_sha256",
    "fit_lock_sha256",
    "holdout_csv_sha256",
    "npz_sha256",
)

RUNTIME_COLUMNS = (
    "correction_runtime_seconds",
    "dg_runtime_seconds",
    "manifold_runtime_seconds",
    "projection_runtime_seconds",
    "total_runtime_seconds",
    "correction_cache_hit",
)


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _array_sha256(values: np.ndarray) -> str:
    array = np.ascontiguousarray(values)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(repr(array.shape).encode("ascii"))
    digest.update(array.tobytes())
    return digest.hexdigest()


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (bool, np.bool_)):
        return str(bool(value)).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not np.isfinite(number):
            return ""
        return f"{number:.15g}"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    return str(value)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _csv_text(rows: Sequence[Mapping[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _source_git_commit() -> str:
    lock = json.loads(BASELINE_LOCK.read_text(encoding="utf-8"))
    return str(lock["source_git_commit"])


def _lift_cache_path(family: str, source: Any, samples: int) -> Path:
    payload = {
        "version": CACHE_VERSION,
        "family": family,
        "source_samples": int(source.corrected_states.shape[0]),
        "target_samples": int(samples),
        "target_jacobi": float(source.target_jacobi),
        "mapping_time": float(source.mapping_time),
        "rotation_angle": float(source.rotation_angle_rad),
        "source_states_sha256": _array_sha256(source.corrected_states),
        "max_iterations": MAX_ITERATIONS,
        "max_step": MAX_STEP,
        "quasi_torus_sha256": _sha256(ROOT / "src" / "qp_orbits" / "quasi_torus.py"),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    digest = hashlib.sha256(encoded).hexdigest()[:20]
    return CACHE / f"research_{family}_resolution_lift_v{CACHE_VERSION}_{digest}.pkl"


def _lift_correction(
    source: Any,
    *,
    family: str,
    samples: int,
    allow_cache_write: bool,
) -> tuple[Any, bool, float]:
    if samples == source.corrected_states.shape[0]:
        return source, True, 0.0
    component = 2 if family == "halo" else 0
    seed_amplitude = 1.0e-3 if family == "halo" else 1.0e-4
    cache_path = _lift_cache_path(family, source, samples)
    if cache_path.is_file():
        with cache_path.open("rb") as stream:
            correction = pickle.load(stream)
        if (
            correction.corrected_states.shape == (samples, 6)
            and abs(float(correction.target_jacobi) - float(source.target_jacobi)) < 1.0e-13
        ):
            return correction, True, 0.0

    started = time.perf_counter()
    seed = stroboscopic_spatial_jacobi_seed(
        source.seed.mu,
        target_jacobi=source.target_jacobi,
        family_label=family,
        mode_component=component,
        mode_amplitude=seed_amplitude,
        samples=samples,
        curve_samples=max(4 * samples, 120),
    )
    interpolation = _trigonometric_interpolation_matrix(
        source.seed.phases,
        seed.phases,
    )
    initial_states = interpolation @ source.corrected_states
    displacement = initial_states[:, component] - seed.orbit_state[component]
    target_amplitude = float(np.sqrt(2.0 * np.mean(displacement**2)))
    correction = stroboscopic_curve_free_energy_correction(
        seed,
        target_jacobi=source.target_jacobi,
        target_amplitude=target_amplitude,
        amplitude_component=component,
        initial_states=initial_states,
        initial_mapping_time=source.mapping_time,
        initial_rotation_angle_rad=source.rotation_angle_rad,
        phase_reference_states=initial_states,
        max_iterations=MAX_ITERATIONS,
        max_state_step=5.0e-4,
        max_mapping_time_step=0.02,
        max_rotation_step=0.02,
        max_step=MAX_STEP,
    )
    elapsed = time.perf_counter() - started
    if allow_cache_write:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".tmp")
        with temporary.open("wb") as stream:
            pickle.dump(correction, stream, protocol=pickle.HIGHEST_PROTOCOL)
        temporary.replace(cache_path)
    return correction, False, elapsed


def _halo_source():
    system = SYSTEMS["earth_moon"]
    family = corrected_l1_constant_energy_halo_high_order_dg_family(
        system.mu,
        samples=21,
        members=25,
        member_indices=(0, 4, 8, 12, 16, 20, 24),
        tolerance=3.0e-10,
        max_iterations=64,
    )
    selected = min(
        family,
        key=lambda dg: abs(
            dg.mapping_time * float(system.time_unit_days) - HALO_TARGET_PERIOD_DAYS
        ),
    )
    period_days = selected.mapping_time * float(system.time_unit_days)
    if abs(period_days - HALO_TARGET_PERIOD_DAYS) > 1.0e-9:
        raise RuntimeError("predeclared halo N21 source drifted")
    return selected.correction, selected


def _vertical_source():
    system = SYSTEMS["earth_moon"]
    source = corrected_l1_constant_energy_vertical_staged_corrections(system.mu)[-1]
    if source.corrected_states.shape[0] != 33:
        raise RuntimeError("predeclared vertical source is no longer N33")
    period_days = source.mapping_time * float(system.time_unit_days)
    if abs(period_days - VERTICAL_TARGET_PERIOD_DAYS) > 1.0e-9:
        raise RuntimeError("predeclared vertical N33 source drifted")
    return source


def _selected_direction(dg: Any) -> dict[str, Any]:
    index = real_hyperbolic_eigen_index(
        dg,
        branch="unstable",
        relative_imaginary_tolerance=RELATIVE_IMAGINARY_MAX,
    )
    eigenvalue = complex(dg.eigenvalues[index])
    vector = np.asarray(dg.eigenvectors[:, index])
    direction = np.real(vector).reshape(-1, 6)
    norms = np.linalg.norm(direction, axis=1)
    if float(np.min(norms)) < 1.0e-12:
        direction = np.imag(vector).reshape(-1, 6)
        norms = np.linalg.norm(direction, axis=1)
    if float(np.min(norms)) < 1.0e-12:
        raise RuntimeError("selected eigenvector has near-zero local blocks")
    direction = direction / norms[:, None]
    residual = float(
        np.linalg.norm(dg.map_jacobian @ vector - eigenvalue * vector)
        / max(
            np.linalg.norm(dg.map_jacobian @ vector),
            abs(eigenvalue) * np.linalg.norm(vector),
            np.finfo(float).tiny,
        )
    )
    magnitudes = np.abs(dg.eigenvalues)
    unstable = np.sort(magnitudes[magnitudes > 1.0 + 1.0e-3])
    sample_count = dg.correction.corrected_states.shape[0]
    if unstable.size < sample_count:
        raise RuntimeError("DG does not contain a full unstable multiplier ring")
    ring = unstable[-sample_count:]
    dispersion = float((np.max(ring) - np.min(ring)) / np.mean(ring))
    return {
        "index": index,
        "eigenvalue": eigenvalue,
        "direction": direction,
        "eigenpair_residual": residual,
        "ring_count": int(ring.size),
        "ring_dispersion": dispersion,
    }


def _interpolate_common(correction: Any, direction: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    phases = np.linspace(0.0, 2.0 * np.pi, COMMON_PHASE_SAMPLES, endpoint=False)
    interpolation = _trigonometric_interpolation_matrix(correction.seed.phases, phases)
    states = interpolation @ correction.corrected_states
    directions = interpolation @ direction
    norms = np.linalg.norm(directions, axis=1)
    if float(np.min(norms)) < 1.0e-12:
        raise RuntimeError("interpolated direction contains near-zero blocks")
    return states, directions / norms[:, None]


def _align_common(
    reference_states: np.ndarray,
    reference_directions: np.ndarray,
    states: np.ndarray,
    directions: np.ndarray,
) -> dict[str, Any]:
    costs = np.asarray(
        [
            np.sqrt(
                np.mean(
                    np.sum(
                        (
                            reference_states[:, :3]
                            - np.roll(states[:, :3], shift, axis=0)
                        )
                        ** 2,
                        axis=1,
                    )
                )
            )
            for shift in range(states.shape[0])
        ]
    )
    shift = int(np.argmin(costs))
    aligned_states = np.roll(states, shift, axis=0)
    aligned_directions = np.roll(directions, shift, axis=0)
    signed_dot = float(np.mean(np.sum(reference_directions * aligned_directions, axis=1)))
    sign = 1.0 if signed_dot >= 0.0 else -1.0
    aligned_directions = sign * aligned_directions
    cosines = np.clip(
        np.abs(np.sum(reference_directions * aligned_directions, axis=1)),
        0.0,
        1.0,
    )
    angles = np.degrees(np.arccos(cosines))
    return {
        "states": aligned_states,
        "directions": aligned_directions,
        "shift": shift,
        "shift_deg": float(360.0 * shift / states.shape[0]),
        "sign": sign,
        "state_rms": float(costs[shift]),
        "angle_mean": float(np.mean(angles)),
        "angle_max": float(np.max(angles)),
    }


def _symmetric_hd95(reference: np.ndarray, candidate: np.ndarray) -> tuple[float, float]:
    ref = np.asarray(reference, dtype=float).reshape(-1, 3)
    cand = np.asarray(candidate, dtype=float).reshape(-1, 3)
    ref_tree = cKDTree(ref)
    cand_tree = cKDTree(cand)
    cand_to_ref = ref_tree.query(cand, k=1, workers=1)[0]
    ref_to_cand = cand_tree.query(ref, k=1, workers=1)[0]
    raw = max(
        float(np.quantile(cand_to_ref, 0.95)),
        float(np.quantile(ref_to_cand, 0.95)),
    )
    span = np.ptp(ref, axis=0)
    diagonal = float(np.linalg.norm(span))
    if diagonal <= np.finfo(float).tiny:
        raise RuntimeError("reference manifold sheet has zero 3D diagonal")
    return raw, raw / diagonal


def _sheet_comparison(reference: Sequence[Any], candidate: Sequence[Any]) -> dict[str, float]:
    raw_values: list[float] = []
    normalized_values: list[float] = []
    for reference_branch, candidate_branch in zip(reference, candidate):
        if reference_branch.snapshot_states.shape[0] != candidate_branch.snapshot_states.shape[0]:
            raise RuntimeError("snapshot counts differ across resolutions")
        for index in range(reference_branch.snapshot_states.shape[0]):
            raw, normalized = _symmetric_hd95(
                reference_branch.snapshot_states[index, ..., :3],
                candidate_branch.snapshot_states[index, ..., :3],
            )
            raw_values.append(raw)
            normalized_values.append(normalized)
    return {
        "raw_mean": float(np.mean(raw_values)),
        "raw_max": float(np.max(raw_values)),
        "normalized_mean": float(np.mean(normalized_values)),
        "normalized_max": float(np.max(normalized_values)),
    }


def _manifold_jacobi_drift(snapshots: Any, mu: float) -> float:
    initial = jacobi_constant(snapshots.history_states[0], mu)
    history = jacobi_constant(snapshots.history_states, mu)
    snapshot = jacobi_constant(snapshots.snapshot_states, mu)
    return max(
        float(np.max(np.abs(history - initial[None, :]))),
        float(np.max(np.abs(snapshot - initial[None, None, :]))),
    )


def _projection_failures(metrics: Mapping[str, float]) -> list[str]:
    failures: list[str] = []
    if metrics["symmetric_chamfer_diagonal_fraction"] > CHAMFER_MAX_FRACTION:
        failures.append("chamfer")
    if metrics["f1_at_0p01_diagonal"] < F1_MIN:
        failures.append("f1")
    if metrics["hd95_diagonal_fraction"] > PROJECTION_HD95_MAX_FRACTION:
        failures.append("hd95")
    area = metrics["area_ratio_prediction_over_paper"]
    if not AREA_RATIO_MIN <= area <= AREA_RATIO_MAX:
        failures.append("area_ratio")
    return failures


def _family_config(family: str) -> dict[str, Any]:
    if family == "halo":
        return {
            "resolutions": HALO_RESOLUTIONS,
            "baseline_period_days": HALO_TARGET_PERIOD_DAYS,
            "snapshots_days": HALO_SNAPSHOT_DAYS,
            "figures": (("4.3", "positive_x", 0), ("4.4", "negative_x", 1)),
            "campaign": "C4-HALO-12P40-SOURCE-FALSIFICATION",
        }
    if family == "vertical":
        return {
            "resolutions": VERTICAL_RESOLUTIONS,
            "baseline_period_days": VERTICAL_TARGET_PERIOD_DAYS,
            "snapshots_days": VERTICAL_SNAPSHOT_DAYS,
            "figures": (("4.5", "positive_x", 0), ("4.6", "negative_x", 1)),
            "campaign": "C4-VERTICAL-N-CONVERGENCE",
        }
    raise ValueError(f"unsupported family: {family}")


def analyze_family(
    family: str,
    *,
    allow_cache_write: bool,
    max_wall_seconds: float,
) -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    system = SYSTEMS["earth_moon"]
    if system.time_unit_days is None or system.length_unit_km is None:
        raise RuntimeError("Earth-Moon dimensional units are required")
    config = _family_config(family)
    resolutions = config["resolutions"]
    campaign_started = time.perf_counter()
    lock = load_chapter4_reproduction_lock(ROOT)
    if lock.paper_projection_acceptance != "fail" or lock.paper_3d_equivalence:
        raise RuntimeError("frozen Chapter 4 holdout boundary drifted")

    if family == "halo":
        source, source_dg = _halo_source()
    else:
        source = _vertical_source()
        source_dg = None

    results: list[dict[str, Any]] = []
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "family": np.asarray([family]),
        "campaign": np.asarray([config["campaign"]]),
        "resolutions": np.asarray(resolutions, dtype=int),
        "snapshot_times_days": np.asarray(config["snapshots_days"], dtype=float),
        "common_phase_samples": np.asarray([COMMON_PHASE_SAMPLES], dtype=int),
        "phase_samples": np.asarray([PHASE_SAMPLES], dtype=int),
        "history_samples": np.asarray([HISTORY_SAMPLES], dtype=int),
        "selected_epsilon": np.asarray([lock.epsilon_by_family[family]], dtype=float),
        "fit_lock_sha256": np.asarray([lock.fit_lock_sha256]),
        "holdout_csv_sha256": np.asarray([lock.holdout_csv_sha256]),
        "source_git_commit": np.asarray([_source_git_commit()]),
    }

    for samples in resolutions:
        total_started = time.perf_counter()
        correction, cache_hit, correction_runtime = _lift_correction(
            source,
            family=family,
            samples=samples,
            allow_cache_write=allow_cache_write,
        )
        dg_started = time.perf_counter()
        if samples == resolutions[0] and source_dg is not None:
            dg = source_dg
        else:
            dg = corrected_curve_dg(correction, max_step=MAX_STEP)
        dg_runtime = time.perf_counter() - dg_started
        selected = _selected_direction(dg)

        snapshot_times = tuple(
            float(days) / float(system.time_unit_days)
            for days in config["snapshots_days"]
        )
        manifold_started = time.perf_counter()
        candidates = tuple(
            corrected_curve_fixed_time_manifold_snapshots(
                system.mu,
                dg=dg,
                snapshot_times=snapshot_times,
                perturbation_scale=lock.epsilon_by_family[family],
                perturbation_sign=sign,
                phase_samples=PHASE_SAMPLES,
                history_samples=HISTORY_SAMPLES,
                max_step=MAX_STEP,
            )
            for sign in (-1.0, 1.0)
        )
        negative_x, positive_x = sorted(
            candidates,
            key=lambda item: float(np.mean(item.snapshot_states[-1, ..., 0])),
        )
        snapshots = (positive_x, negative_x)
        manifold_runtime = time.perf_counter() - manifold_started

        common_states, common_directions = _interpolate_common(
            correction,
            selected["direction"],
        )
        source_jacobi = jacobi_constant(correction.corrected_states, system.mu)
        base_torus = positive_x.base_torus_states
        manifold_drift = max(
            _manifold_jacobi_drift(positive_x, system.mu),
            _manifold_jacobi_drift(negative_x, system.mu),
        )
        row: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "campaign": config["campaign"],
            "family": family,
            "spectral_samples": samples,
            "source_selection": (
                "predeclared_n21_nearest_12p40_before_mask"
                if family == "halo" and samples == 21
                else (
                    "predeclared_n33_vertical_endpoint_before_mask"
                    if family == "vertical" and samples == 33
                    else f"direct_spectral_lift_of_predeclared_n{resolutions[0]}_member"
                )
            ),
            "source_selection_red_mask_read": False,
            "projection_red_mask_read": False,
            "target_jacobi": float(correction.target_jacobi),
            "baseline_period_days": config["baseline_period_days"],
            "mapping_time_days": float(correction.mapping_time * system.time_unit_days),
            "rotation_angle_rad": float(correction.rotation_angle_rad),
            "period_change_from_baseline_days": float(
                correction.mapping_time * system.time_unit_days
                - config["baseline_period_days"]
            ),
            "source_ay_km": float(np.max(np.abs(base_torus[..., 1])) * system.length_unit_km),
            "source_az_km": float(np.max(np.abs(base_torus[..., 2])) * system.length_unit_km),
            "curve_residual": float(correction.final_residual_norms.max()),
            "source_jacobi_span": float(np.ptp(source_jacobi)),
            "bundle_dimension": 1,
            "selected_unstable_eigenvalue_real": float(selected["eigenvalue"].real),
            "selected_unstable_eigenvalue_imag": float(selected["eigenvalue"].imag),
            "selected_unstable_multiplier": float(abs(selected["eigenvalue"])),
            "selected_relative_imaginary": float(
                abs(selected["eigenvalue"].imag)
                / max(abs(selected["eigenvalue"]), np.finfo(float).tiny)
            ),
            "eigenpair_residual": selected["eigenpair_residual"],
            "dg_determinant": float(dg.determinant),
            "dg_determinant_error": abs(float(dg.determinant) - 1.0),
            "unstable_ring_count": selected["ring_count"],
            "unstable_ring_relative_dispersion": selected["ring_dispersion"],
            "manifold_jacobi_drift_max": manifold_drift,
            "correction_runtime_seconds": correction_runtime,
            "dg_runtime_seconds": dg_runtime,
            "manifold_runtime_seconds": manifold_runtime,
            "projection_runtime_seconds": 0.0,
            "total_runtime_seconds": time.perf_counter() - total_started,
            "correction_cache_hit": cache_hit,
            "frozen_holdout_status": "fail_0_of_4",
            "paper_projection_acceptance": "fail",
            "paper_3d_equivalence": False,
        }
        results.append(
            {
                "row": row,
                "correction": correction,
                "dg": dg,
                "selected": selected,
                "snapshots": snapshots,
                "common_states": common_states,
                "common_directions": common_directions,
            }
        )

        prefix = f"n{samples}"
        arrays[prefix + "_source_states"] = np.asarray(correction.corrected_states)
        arrays[prefix + "_source_phases"] = np.asarray(correction.seed.phases)
        arrays[prefix + "_rotation_angle_rad"] = np.asarray(
            [correction.rotation_angle_rad]
        )
        arrays[prefix + "_selected_direction_nodes"] = np.asarray(selected["direction"])
        arrays[prefix + "_dg_eigenvalues"] = np.asarray(dg.eigenvalues)
        arrays[prefix + "_common_states_unaligned"] = common_states
        arrays[prefix + "_common_directions_unaligned"] = common_directions
        arrays[prefix + "_base_torus_states"] = np.asarray(base_torus)
        arrays[prefix + "_positive_x_snapshot_states"] = np.asarray(
            positive_x.snapshot_states
        )
        arrays[prefix + "_negative_x_snapshot_states"] = np.asarray(
            negative_x.snapshot_states
        )
        arrays[prefix + "_positive_x_perturbation_directions"] = np.asarray(
            positive_x.perturbation_directions
        )
        arrays[prefix + "_negative_x_perturbation_directions"] = np.asarray(
            negative_x.perturbation_directions
        )
        if time.perf_counter() - campaign_started > max_wall_seconds:
            raise RuntimeError(
                f"{family} campaign exceeded max wall time after N={samples}"
            )

    baseline = results[0]
    previous = baseline
    for index, result in enumerate(results):
        aligned = _align_common(
            baseline["common_states"],
            baseline["common_directions"],
            result["common_states"],
            result["common_directions"],
        )
        previous_aligned = _align_common(
            previous["common_states"],
            previous["common_directions"],
            result["common_states"],
            result["common_directions"],
        )
        row = result["row"]
        row.update(
            {
                "phase_shift_to_baseline_deg": aligned["shift_deg"],
                "direction_sign_to_baseline": aligned["sign"],
                "base_state_rms_to_baseline": aligned["state_rms"],
                "principal_angle_mean_to_baseline_deg": aligned["angle_mean"],
                "principal_angle_max_to_baseline_deg": aligned["angle_max"],
                "principal_angle_mean_to_previous_deg": previous_aligned["angle_mean"],
                "principal_angle_max_to_previous_deg": previous_aligned["angle_max"],
                "multiplier_relative_change_to_baseline": abs(
                    row["selected_unstable_multiplier"]
                    - baseline["row"]["selected_unstable_multiplier"]
                )
                / baseline["row"]["selected_unstable_multiplier"],
                "multiplier_relative_change_to_previous": abs(
                    row["selected_unstable_multiplier"]
                    - previous["row"]["selected_unstable_multiplier"]
                )
                / previous["row"]["selected_unstable_multiplier"],
            }
        )
        baseline_sheet = _sheet_comparison(
            baseline["snapshots"],
            result["snapshots"],
        )
        previous_sheet = _sheet_comparison(
            previous["snapshots"],
            result["snapshots"],
        )
        for name, value in baseline_sheet.items():
            row[f"sheet_hd95_{name}_to_baseline"] = value
        for name, value in previous_sheet.items():
            row[f"sheet_hd95_{name}_to_previous"] = value
        prefix = f"n{row['spectral_samples']}"
        arrays[prefix + "_common_states_aligned"] = np.asarray(aligned["states"])
        arrays[prefix + "_common_directions_aligned"] = np.asarray(aligned["directions"])
        previous = result

    # Only after every source and state-space result is complete may exposed
    # paper masks be opened for post-hoc development diagnostics.
    protocol = {
        (row["figure_id"], row["panel_id"]): row
        for row in _read_csv(PROTOCOL_PATH)
    }
    with np.load(CAMERA_NPZ, allow_pickle=False) as camera:
        camera_hash = str(camera["camera_config_sha256"][0])
        if camera_hash != lock.camera_config_sha256:
            raise RuntimeError("frozen camera hash drifted")
        for result in results:
            projection_started = time.perf_counter()
            row = result["row"]
            pass_count = 0
            for figure_id, label, branch_index in config["figures"]:
                protocol_row = protocol[(figure_id, "d")]
                paper = load_reference_panel_mask(ROOT, protocol_row, allow_holdout=True)
                projection = np.asarray(
                    camera[
                        f"fig_{figure_id.replace('.', '_')}_projection_matrix"
                    ],
                    dtype=float,
                )
                placement = np.asarray(
                    camera[
                        f"fig_{figure_id.replace('.', '_')}_placement_matrix"
                    ],
                    dtype=float,
                )
                surface = result["snapshots"][branch_index].snapshot_states[3]
                uv = project_surface_uv(surface, projection, placement)
                prediction = rasterize_surface_mask(uv)
                metrics = projection_mask_metrics(paper, prediction)
                failures = _projection_failures(metrics)
                if not failures:
                    pass_count += 1
                row.update(
                    {
                        f"{label}_chamfer_fraction": metrics[
                            "symmetric_chamfer_diagonal_fraction"
                        ],
                        f"{label}_f1": metrics["f1_at_0p01_diagonal"],
                        f"{label}_hd95_fraction": metrics[
                            "hd95_diagonal_fraction"
                        ],
                        f"{label}_area_ratio": metrics[
                            "area_ratio_prediction_over_paper"
                        ],
                        f"{label}_posthoc_projection_gate": (
                            "pass" if not failures else "fail:" + ";".join(failures)
                        ),
                    }
                )
                prefix = f"n{row['spectral_samples']}_{figure_id.replace('.', '_')}"
                arrays[prefix + "_reference_mask"] = paper
                arrays[prefix + "_prediction_mask"] = prediction
                arrays[prefix + "_projected_uv"] = uv
            row["posthoc_projection_pass_count"] = pass_count
            row["projection_red_mask_read"] = True
            row["projection_runtime_seconds"] = time.perf_counter() - projection_started
            row["total_runtime_seconds"] += row["projection_runtime_seconds"]

    for index, result in enumerate(results):
        row = result["row"]
        source_failures: list[str] = []
        if row["curve_residual"] > CURVE_RESIDUAL_MAX:
            source_failures.append("curve_residual")
        if row["source_jacobi_span"] > JACOBI_SPAN_MAX:
            source_failures.append("source_jacobi_span")
        if row["dg_determinant_error"] > DETERMINANT_ERROR_MAX:
            source_failures.append("dg_determinant")
        if row["selected_relative_imaginary"] > RELATIVE_IMAGINARY_MAX:
            source_failures.append("relative_imaginary")
        if row["unstable_ring_relative_dispersion"] > UNSTABLE_RING_DISPERSION_MAX:
            source_failures.append("unstable_ring_dispersion")
        if row["manifold_jacobi_drift_max"] > MANIFOLD_JACOBI_DRIFT_MAX:
            source_failures.append("manifold_jacobi_drift")
        if family == "halo":
            if abs(row["mapping_time_days"] - 12.40) > 0.005:
                source_failures.append("period_target")
            if abs(row["source_ay_km"] - 41815.0) > 50.0:
                source_failures.append("ay_target")
            if abs(row["source_az_km"] - 35783.0) > 50.0:
                source_failures.append("az_target")
        row["source_gate"] = "pass" if not source_failures else "fail"

        convergence_failures: list[str] = []
        if index == 0:
            row["cross_resolution_gate"] = "baseline"
        else:
            if (
                row["multiplier_relative_change_to_previous"]
                > MULTIPLIER_RELATIVE_CHANGE_MAX
            ):
                convergence_failures.append("multiplier")
            if (
                row["principal_angle_max_to_previous_deg"]
                > PRINCIPAL_ANGLE_MAX_DEG
            ):
                convergence_failures.append("principal_angle")
            if (
                row["sheet_hd95_normalized_max_to_previous"]
                > SHEET_HD95_NORMALIZED_MAX
            ):
                convergence_failures.append("sheet_hd95")
            row["cross_resolution_gate"] = (
                "pass" if not convergence_failures else "fail"
            )
        row["posthoc_projection_status"] = (
            "pass_2_of_2"
            if row["posthoc_projection_pass_count"] == 2
            else f"boundary_{row['posthoc_projection_pass_count']}_of_2"
        )
        all_failures = source_failures + convergence_failures
        if source_failures:
            row["overall_status"] = "fail_source_gate"
        elif convergence_failures:
            row["overall_status"] = "boundary_cross_resolution"
        elif row["posthoc_projection_pass_count"] < 2:
            row["overall_status"] = "state_space_pass_projection_boundary"
        else:
            row["overall_status"] = "state_space_and_posthoc_projection_pass"
        row["failure_reason"] = "none" if not all_failures else ";".join(all_failures)

    hashes = {
        "generator_sha256": _sha256(Path(__file__)),
        "quasi_torus_sha256": _sha256(ROOT / "src" / "qp_orbits" / "quasi_torus.py"),
        "torus_stability_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "torus_stability.py"
        ),
        "projection_core_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "chapter4_projection.py"
        ),
    }
    for row in (result["row"] for result in results):
        row.update(
            {
                "source_git_commit": _source_git_commit(),
                **hashes,
                "fit_lock_sha256": lock.fit_lock_sha256,
                "holdout_csv_sha256": lock.holdout_csv_sha256,
            }
        )
    arrays.update({key: np.asarray([value]) for key, value in hashes.items()})
    arrays["camera_config_sha256"] = np.asarray([lock.camera_config_sha256])
    return [result["row"] for result in results], arrays


def _rows_with_hash(rows: Sequence[Mapping[str, Any]], npz_hash: str) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for source in rows:
        values = {column: _fmt(source.get(column)) for column in CSV_COLUMNS}
        values["npz_sha256"] = npz_hash
        formatted.append(values)
    return formatted


def _render_doc(family: str, rows: Sequence[Mapping[str, str]], npz_hash: str) -> str:
    config = _family_config(family)
    title = (
        "Halo 12.40-day source resolution audit"
        if family == "halo"
        else "Quasi-vertical 12.66-day resolution audit"
    )
    table = [
        "| N | period day | residual | multiplier | angle prev deg | HD95 prev | J drift | source | convergence | post-hoc projection |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for row in rows:
        table.append(
            f"| {row['spectral_samples']} | {float(row['mapping_time_days']):.9f} | "
            f"{float(row['curve_residual']):.3e} | "
            f"{float(row['selected_unstable_multiplier']):.9g} | "
            f"{float(row['principal_angle_max_to_previous_deg']):.4f} | "
            f"{float(row['sheet_hd95_normalized_max_to_previous']):.5f} | "
            f"{float(row['manifold_jacobi_drift_max']):.3e} | "
            f"{row['source_gate']} | {row['cross_resolution_gate']} | "
            f"{row['posthoc_projection_status']} |"
        )
    final = rows[-1]
    state_pass = all(
        row["source_gate"] == "pass"
        and row["cross_resolution_gate"] in {"baseline", "pass"}
        for row in rows
    )
    projection_pass = all(row["posthoc_projection_status"] == "pass_2_of_2" for row in rows)
    if state_pass:
        state_conclusion = "The predeclared source passes the registered state-space and adjacent-resolution gates."
    else:
        state_conclusion = "At least one registered state-space or adjacent-resolution gate remains a boundary; the failed row is retained in the CSV."
    if projection_pass:
        projection_conclusion = "All exposed panel-(d) development comparisons pass, but this cannot revise the frozen v1 holdout."
    else:
        projection_conclusion = "The exposed panel-(d) development comparison remains a projection boundary and cannot revise the frozen v1 holdout."
    return "\n".join(
        [
            f"# Chapter 4 {title}",
            "",
            f"Campaign: {config['campaign']}.",
            "",
            "Source selection and every state-space computation completed before any exposed red mask was opened. Projection rows are post-hoc development evidence only.",
            "",
            *table,
            "",
            "## Decision",
            "",
            f"- {state_conclusion}",
            f"- {projection_conclusion}",
            f"- Highest resolution overall status: {final['overall_status']}.",
            "- Frozen v1 result remains 0/4, paper_projection=fail, paper_3d=false.",
            "- These rows test source and resolution behavior under the current pointwise DG eigenselection. They do not yet establish that pointwise eigenselection is reliable as a cocycle invariant bundle.",
            "",
            "## Artifacts",
            "",
            f"- CSV: {_display(OUTPUTS[family]['csv'])}",
            f"- NPZ: {_display(OUTPUTS[family]['npz'])}",
            f"- NPZ SHA-256: {npz_hash}",
            f"- Generator: {_display(Path(__file__))}",
            "",
            "## Fixed gates",
            "",
            f"- curve residual <= {CURVE_RESIDUAL_MAX:g}; Jacobi span <= {JACOBI_SPAN_MAX:g}",
            f"- determinant error <= {DETERMINANT_ERROR_MAX:g}; relative imaginary <= {RELATIVE_IMAGINARY_MAX:g}",
            f"- unstable-ring dispersion <= {UNSTABLE_RING_DISPERSION_MAX:g}; manifold Jacobi drift <= {MANIFOLD_JACOBI_DRIFT_MAX:g}",
            f"- adjacent multiplier change <= {MULTIPLIER_RELATIVE_CHANGE_MAX:g}; principal angle <= {PRINCIPAL_ANGLE_MAX_DEG:g} deg; normalized sheet HD95 <= {SHEET_HD95_NORMALIZED_MAX:g}",
            f"- post-hoc projection: Chamfer/D <= {CHAMFER_MAX_FRACTION:g}, F1 >= {F1_MIN:g}, HD95/D <= {PROJECTION_HD95_MAX_FRACTION:g}, area ratio in [{AREA_RATIO_MIN:g}, {AREA_RATIO_MAX:g}]",
            "",
        ]
    )


def _compare_npz(path: Path, expected: Mapping[str, np.ndarray]) -> None:
    if not path.is_file():
        raise RuntimeError(f"missing stored NPZ: {_display(path)}")
    with np.load(path, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            missing = sorted(set(expected) - set(stored.files))
            extra = sorted(set(stored.files) - set(expected))
            raise RuntimeError(f"NPZ key drift; missing={missing}, extra={extra}")
        for key, values in expected.items():
            actual = np.asarray(stored[key])
            wanted = np.asarray(values)
            if actual.dtype.kind in "fci" or wanted.dtype.kind in "fci":
                equal = np.allclose(
                    actual,
                    wanted,
                    rtol=2.0e-11,
                    atol=2.0e-12,
                    equal_nan=True,
                )
            else:
                equal = np.array_equal(actual, wanted)
            if not equal:
                raise RuntimeError(f"NPZ array drift: {key}")


def _write_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    temporary.replace(path)


def run_family(
    family: str,
    *,
    check: bool,
    max_wall_seconds: float,
) -> None:
    output = OUTPUTS[family]
    rows, arrays = analyze_family(
        family,
        allow_cache_write=not check,
        max_wall_seconds=max_wall_seconds,
    )
    if check:
        _compare_npz(output["npz"], arrays)
        npz_hash = _sha256(output["npz"])
        if not output["csv"].is_file():
            raise RuntimeError(f"missing stored CSV: {_display(output['csv'])}")
        stored_rows = _read_csv(output["csv"])
        if len(stored_rows) != len(rows):
            raise RuntimeError("stored CSV row count drifted")
        for recomputed, stored in zip(rows, stored_rows):
            for column in RUNTIME_COLUMNS:
                recomputed[column] = stored[column]
        expected_rows = _rows_with_hash(rows, npz_hash)
        expected_csv = _csv_text(expected_rows)
        expected_doc = _render_doc(family, expected_rows, npz_hash)
        if output["csv"].read_text(encoding="utf-8") != expected_csv:
            raise RuntimeError(f"stored CSV drifted: {_display(output['csv'])}")
        if not output["doc"].is_file() or output["doc"].read_text(
            encoding="utf-8"
        ) != expected_doc:
            raise RuntimeError(f"stored report drifted: {_display(output['doc'])}")
        print(
            f"{family} resolution check PASS rows={len(rows)} "
            f"highest={expected_rows[-1]['overall_status']} frozen_holdout=fail"
        )
        return

    _write_npz(output["npz"], arrays)
    npz_hash = _sha256(output["npz"])
    formatted_rows = _rows_with_hash(rows, npz_hash)
    output["csv"].write_text(
        _csv_text(formatted_rows),
        encoding="utf-8",
        newline="\n",
    )
    output["doc"].write_text(
        _render_doc(family, formatted_rows, npz_hash),
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{family} resolution write PASS rows={len(rows)} "
        f"highest={formatted_rows[-1]['overall_status']} frozen_holdout=fail"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        choices=("halo", "vertical", "all"),
        default="all",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Recompute and compare without rewriting authoritative outputs.",
    )
    parser.add_argument(
        "--max-wall-seconds",
        type=float,
        default=8.0 * 60.0 * 60.0,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_wall_seconds <= 0.0:
        raise ValueError("--max-wall-seconds must be positive")
    families = ("halo", "vertical") if args.family == "all" else (args.family,)
    for family in families:
        run_family(
            family,
            check=args.check,
            max_wall_seconds=args.max_wall_seconds,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
