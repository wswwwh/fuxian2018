"""Archive frozen one-factor Chapter 4 projection/transport negative controls."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree

import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_agg import FigureCanvasAgg  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qp_orbits.chapter4_projection import (  # noqa: E402
    NORMALIZED_PANEL_SIZE,
    load_reference_panel_mask,
    project_surface_uv,
    projection_mask_metrics,
    rasterize_surface_mask,
    red_dominance_mask,
)
from qp_orbits.chapter4_reproduction_lock import (  # noqa: E402
    load_chapter4_reproduction_lock,
)
from qp_orbits.constants import SYSTEMS  # noqa: E402
from qp_orbits.cr3bp import integrate_states_cr3bp  # noqa: E402
from qp_orbits.variational import integrate_states_and_stms  # noqa: E402


SCHEMA_VERSION = "chapter4_projection_semantics_negative_controls_v1"
DATA = ROOT / "data" / "computed"
DOCS = ROOT / "docs"
CSV_PATH = DATA / "chapter4_projection_semantics_negative_controls.csv"
NPZ_PATH = DATA / "chapter4_projection_semantics_negative_controls.npz"
DOC_PATH = DOCS / "chapter4_projection_semantics_negative_controls.md"

PROTOCOL_PATH = DATA / "chapter4_fig43_fig46_camera_holdout_protocol.csv"
HOLDOUT_PATH = DATA / "chapter4_fig43_fig46_projection_holdout_audit.csv"
CAMERA_NPZ = DATA / "chapter4_fig43_fig46_camera_calibration.npz"
FIT_NPZ = DATA / "chapter4_fig43_fig46_projection_fit_evidence.npz"
HALO_NPZ = DATA / "chapter4_fig43_fig44_global_manifold_audit.npz"
VERTICAL_NPZ = DATA / "chapter4_fig45_fig48_vertical_manifold_audit.npz"

CONTROLS = (
    "panel_time_mapping",
    "mask_extraction_order",
    "quad_rasterizer",
    "surface_renderer",
    "explicit_stm_transport",
)
FIGURES = (
    ("4.3", "halo", "positive_x", 0, HALO_NPZ, "plus_x"),
    ("4.4", "halo", "negative_x", 1, HALO_NPZ, "minus_x"),
    ("4.5", "vertical", "positive_x", 0, VERTICAL_NPZ, "plus_x"),
    ("4.6", "vertical", "negative_x", 1, VERTICAL_NPZ, "minus_x"),
)

CHAMFER_MAX_FRACTION = 0.02
F1_MIN = 0.70
HD95_MAX_FRACTION = 0.05
AREA_RATIO_MIN = 0.67
AREA_RATIO_MAX = 1.50

CSV_COLUMNS = (
    "schema_version",
    "control_id",
    "variant_id",
    "figure_id",
    "family",
    "branch",
    "panel_id",
    "canonical_snapshot_index",
    "variant_snapshot_index",
    "changed_factor",
    "fixed_camera",
    "fixed_epsilon",
    "fixed_crop",
    "fixed_thresholds",
    "historical_exposure",
    "paper_mask_read",
    "variant_metric_reference",
    "canonical_chamfer_fraction",
    "canonical_f1",
    "canonical_hd95_fraction",
    "canonical_area_ratio",
    "canonical_projection_loss",
    "variant_chamfer_fraction",
    "variant_f1",
    "variant_hd95_fraction",
    "variant_area_ratio",
    "variant_projection_loss",
    "delta_projection_loss_from_canonical",
    "semantic_chamfer_fraction",
    "semantic_f1",
    "semantic_hd95_fraction",
    "semantic_area_ratio",
    "state_rms_difference",
    "state_max_abs_difference",
    "state_hd95_raw",
    "state_hd95_normalized",
    "variant_protocol_gate",
    "semantic_similarity_gate",
    "interpretation",
    "control_runtime_seconds",
    "paper_projection_acceptance",
    "paper_3d_equivalence",
    "fit_lock_sha256",
    "holdout_csv_sha256",
    "camera_config_sha256",
    "generator_sha256",
    "projection_core_sha256",
    "variational_core_sha256",
    "npz_sha256",
)


def _display(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


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


def _csv_text(rows: Sequence[Mapping[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _protocol_gate(metrics: Mapping[str, float]) -> str:
    failures: list[str] = []
    if metrics["symmetric_chamfer_diagonal_fraction"] > CHAMFER_MAX_FRACTION:
        failures.append("chamfer")
    if metrics["f1_at_0p01_diagonal"] < F1_MIN:
        failures.append("f1")
    if metrics["hd95_diagonal_fraction"] > HD95_MAX_FRACTION:
        failures.append("hd95")
    if not AREA_RATIO_MIN <= metrics["area_ratio_prediction_over_paper"] <= AREA_RATIO_MAX:
        failures.append("area_ratio")
    return "pass" if not failures else "fail:" + ";".join(failures)


def _triangulated_surface_mask(uv: np.ndarray) -> np.ndarray:
    values = np.asarray(uv, dtype=float)
    pixels = values * float(NORMALIZED_PANEL_SIZE - 1)
    image = Image.new("1", (NORMALIZED_PANEL_SIZE, NORMALIZED_PANEL_SIZE), 0)
    draw = ImageDraw.Draw(image)
    phase_count, curve_count = values.shape[:2]
    for phase_index in range(phase_count - 1):
        for curve_index in range(curve_count):
            next_curve = (curve_index + 1) % curve_count
            p00 = tuple(pixels[phase_index, curve_index])
            p10 = tuple(pixels[phase_index + 1, curve_index])
            p11 = tuple(pixels[phase_index + 1, next_curve])
            p01 = tuple(pixels[phase_index, next_curve])
            draw.polygon((p00, p10, p11), fill=1)
            draw.polygon((p00, p11, p01), fill=1)
    mask = np.asarray(image, dtype=bool)
    if not mask.any():
        raise RuntimeError("triangulated rasterizer produced an empty mask")
    return mask


def _matplotlib_surface_mask(uv: np.ndarray) -> np.ndarray:
    values = np.asarray(uv, dtype=float)
    phase_count, curve_count = values.shape[:2]
    polygons = []
    for phase_index in range(phase_count - 1):
        for curve_index in range(curve_count):
            next_curve = (curve_index + 1) % curve_count
            polygons.append(
                (
                    values[phase_index, curve_index],
                    values[phase_index + 1, curve_index],
                    values[phase_index + 1, next_curve],
                    values[phase_index, next_curve],
                )
            )
    dpi = 100
    figure = Figure(
        figsize=(NORMALIZED_PANEL_SIZE / dpi, NORMALIZED_PANEL_SIZE / dpi),
        dpi=dpi,
        facecolor="white",
    )
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_axes((0.0, 0.0, 1.0, 1.0))
    axis.set_xlim(0.0, 1.0)
    axis.set_ylim(1.0, 0.0)
    axis.set_axis_off()
    collection = PolyCollection(
        polygons,
        facecolors="#c9253d",
        edgecolors="none",
        linewidths=0.0,
        antialiaseds=False,
    )
    axis.add_collection(collection)
    canvas.draw()
    rgba = np.asarray(canvas.buffer_rgba()).copy()
    mask = red_dominance_mask(Image.fromarray(rgba[:, :, :3], mode="RGB"))
    if not mask.any():
        raise RuntimeError("Matplotlib renderer produced an empty mask")
    return mask


def _resize_then_threshold_mask(protocol_row: Mapping[str, str]) -> np.ndarray:
    source = ROOT / protocol_row["paper_source"]
    x0 = math.floor(float(protocol_row["panel_rect_x0"]))
    y0 = math.floor(float(protocol_row["panel_rect_y0"]))
    x1 = math.ceil(float(protocol_row["panel_rect_x1"]))
    y1 = math.ceil(float(protocol_row["panel_rect_y1"]))
    with Image.open(source) as opened:
        resized = opened.convert("RGB").crop((x0, y0, x1, y1)).resize(
            (NORMALIZED_PANEL_SIZE, NORMALIZED_PANEL_SIZE),
            Image.Resampling.BILINEAR,
        )
        mask = red_dominance_mask(resized)
    if not mask.any():
        raise RuntimeError("resize-then-threshold mask is empty")
    return mask


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
    diagonal = float(np.linalg.norm(np.ptp(ref, axis=0)))
    if diagonal <= np.finfo(float).tiny:
        raise RuntimeError("reference state surface has zero diagonal")
    return raw, raw / diagonal


def _explicit_stm_surfaces(
    audit_path: Path,
    *,
    prefix: str,
) -> tuple[np.ndarray, np.ndarray, float]:
    with np.load(audit_path, allow_pickle=False) as audit:
        source_states = np.asarray(audit[prefix + "_source_states"], dtype=float)
        phase_times = np.asarray(audit[prefix + "_phase_times_nd"], dtype=float)
        snapshot_times = np.asarray(audit[prefix + "_snapshot_times_nd"], dtype=float)
        base_snapshot_states = np.asarray(
            audit[prefix + "_base_snapshot_states"],
            dtype=float,
        )
        nonlinear_snapshot_states = np.asarray(
            audit[prefix + "_snapshot_states"],
            dtype=float,
        )
        base_history = np.asarray(audit[prefix + "_base_history_states"], dtype=float)
        nonlinear_history = np.asarray(audit[prefix + "_history_states"], dtype=float)
    evaluation = np.unique(
        np.r_[
            0.0,
            np.concatenate(
                [elapsed + phase_times for elapsed in snapshot_times]
            ),
        ]
    )
    solution = integrate_states_and_stms(
        source_states,
        (0.0, float(evaluation[-1])),
        SYSTEMS["earth_moon"].mu,
        t_eval=evaluation,
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    sample_count = source_states.shape[0]
    augmented = solution.y.T.reshape(evaluation.size, sample_count, 42)
    states = augmented[:, :, :6]
    stms = augmented[:, :, 6:].reshape(evaluation.size, sample_count, 6, 6)
    requested = np.concatenate(
        [elapsed + phase_times for elapsed in snapshot_times]
    )
    indices = np.searchsorted(evaluation, requested)
    if float(np.max(np.abs(evaluation[indices] - requested))) > 1.0e-12:
        raise RuntimeError("explicit STM evaluation time is missing")
    base = states[indices].reshape(snapshot_times.size, phase_times.size, sample_count, 6)
    phi = stms[indices].reshape(
        snapshot_times.size,
        phase_times.size,
        sample_count,
        6,
        6,
    )
    base_error = float(np.max(np.abs(base - base_snapshot_states)))
    if base_error > 5.0e-10:
        raise RuntimeError(f"explicit STM base rerun drifted by {base_error}")
    initial_delta = nonlinear_history[0] - base_history[0]
    linear_delta = np.einsum("kpnij,nj->kpni", phi, initial_delta, optimize=True)
    explicit = base + linear_delta
    return explicit, nonlinear_snapshot_states, base_error


def _stm_reseed_panel_d(
    audit_path: Path,
    *,
    prefix: str,
) -> tuple[np.ndarray, np.ndarray, float]:
    with np.load(audit_path, allow_pickle=False) as audit:
        source_states = np.asarray(audit[prefix + "_source_states"], dtype=float)
        phase_times = np.asarray(audit[prefix + "_phase_times_nd"], dtype=float)
        snapshot_times = np.asarray(audit[prefix + "_snapshot_times_nd"], dtype=float)
        base_torus_states = np.asarray(
            audit[prefix + "_base_torus_states"],
            dtype=float,
        )
        nonlinear_panel_d = np.asarray(
            audit[prefix + "_snapshot_states"],
            dtype=float,
        )[3]
        base_history = np.asarray(audit[prefix + "_base_history_states"], dtype=float)
        nonlinear_history = np.asarray(audit[prefix + "_history_states"], dtype=float)
    solution = integrate_states_and_stms(
        source_states,
        (0.0, float(phase_times[-1])),
        SYSTEMS["earth_moon"].mu,
        t_eval=phase_times,
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=0.01,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    sample_count = source_states.shape[0]
    augmented = solution.y.T.reshape(phase_times.size, sample_count, 42)
    base = augmented[:, :, :6]
    stms = augmented[:, :, 6:].reshape(phase_times.size, sample_count, 6, 6)
    base_error = float(np.max(np.abs(base - base_torus_states)))
    if base_error > 5.0e-10:
        raise RuntimeError(f"STM reseed base torus drifted by {base_error}")
    initial_delta = nonlinear_history[0] - base_history[0]
    epsilon_by_node = np.linalg.norm(initial_delta, axis=1)
    epsilon = float(np.mean(epsilon_by_node))
    if float(np.ptp(epsilon_by_node)) > 1.0e-12:
        raise RuntimeError("stored perturbation norm is not uniform")
    transported = np.einsum("pnij,nj->pni", stms, initial_delta, optimize=True)
    norms = np.linalg.norm(transported, axis=2)
    if float(np.min(norms)) < 1.0e-14:
        raise RuntimeError("STM transported direction has a zero block")
    reseed_states = base + epsilon * transported / norms[:, :, None]
    flattened = reseed_states.reshape(-1, 6)
    elapsed = float(snapshot_times[3])
    propagated = integrate_states_cr3bp(
        flattened,
        (0.0, elapsed),
        SYSTEMS["earth_moon"].mu,
        t_eval=np.asarray([elapsed]),
        rtol=1.0e-12,
        atol=1.0e-14,
        max_step=0.01,
    )
    if not propagated.success:
        raise RuntimeError(propagated.message)
    reseeded_panel_d = propagated.y[:, -1].reshape(
        phase_times.size,
        sample_count,
        6,
    )
    return reseeded_panel_d, nonlinear_panel_d, base_error


def _metric_fields(prefix: str, metrics: Mapping[str, float]) -> dict[str, float]:
    return {
        prefix + "_chamfer_fraction": metrics[
            "symmetric_chamfer_diagonal_fraction"
        ],
        prefix + "_f1": metrics["f1_at_0p01_diagonal"],
        prefix + "_hd95_fraction": metrics["hd95_diagonal_fraction"],
        prefix + "_area_ratio": metrics["area_ratio_prediction_over_paper"],
        prefix + "_projection_loss": metrics["projection_loss"],
    }


def _semantic_gate(metrics: Mapping[str, float]) -> str:
    return (
        "close"
        if metrics["f1_at_0p01_diagonal"] >= 0.95
        and metrics["hd95_diagonal_fraction"] <= 0.01
        else "material_difference"
    )


def analyze() -> tuple[list[dict[str, Any]], dict[str, np.ndarray]]:
    lock = load_chapter4_reproduction_lock(ROOT)
    if lock.paper_projection_acceptance != "fail" or lock.paper_3d_equivalence:
        raise RuntimeError("frozen holdout boundary drifted")
    protocol = {
        (row["figure_id"], row["panel_id"]): row
        for row in _read_csv(PROTOCOL_PATH)
    }
    holdout = {row["figure_id"]: row for row in _read_csv(HOLDOUT_PATH)}
    hashes = {
        "generator_sha256": _sha256(Path(__file__)),
        "projection_core_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "chapter4_projection.py"
        ),
        "variational_core_sha256": _sha256(
            ROOT / "src" / "qp_orbits" / "variational.py"
        ),
    }
    arrays: dict[str, np.ndarray] = {
        "schema_version": np.asarray([SCHEMA_VERSION]),
        "control_ids": np.asarray(CONTROLS),
        "fit_lock_sha256": np.asarray([lock.fit_lock_sha256]),
        "holdout_csv_sha256": np.asarray([lock.holdout_csv_sha256]),
        **{key: np.asarray([value]) for key, value in hashes.items()},
    }
    rows: list[dict[str, Any]] = []

    # Build explicit STM transport controls before any paper mask is opened.
    explicit_by_figure: dict[str, dict[str, Any]] = {}
    reseed_by_figure: dict[str, dict[str, Any]] = {}
    audit_cache: dict[tuple[Path, str], tuple[np.ndarray, np.ndarray, float]] = {}
    for figure_id, family, branch, _, audit_path, prefix in FIGURES:
        key = (audit_path, prefix)
        if key not in audit_cache:
            started = time.perf_counter()
            explicit, nonlinear, base_error = _explicit_stm_surfaces(
                audit_path,
                prefix=prefix,
            )
            audit_cache[key] = (explicit, nonlinear, base_error)
            runtime = time.perf_counter() - started
        else:
            explicit, nonlinear, base_error = audit_cache[key]
            runtime = 0.0
        explicit_by_figure[figure_id] = {
            "explicit": explicit,
            "nonlinear": nonlinear,
            "base_error": base_error,
            "runtime": runtime,
            "family": family,
            "branch": branch,
        }
        stem = figure_id.replace(".", "_")
        arrays[f"fig_{stem}_explicit_stm_snapshot_states"] = explicit
        arrays[f"fig_{stem}_nonlinear_snapshot_states"] = nonlinear
        reseed_started = time.perf_counter()
        reseeded, reseed_nonlinear, reseed_base_error = _stm_reseed_panel_d(
            audit_path,
            prefix=prefix,
        )
        reseed_by_figure[figure_id] = {
            "reseeded": reseeded,
            "nonlinear": reseed_nonlinear,
            "base_error": reseed_base_error,
            "runtime": time.perf_counter() - reseed_started,
        }
        arrays[f"fig_{stem}_stm_reseed_panel_d_states"] = reseeded

    with np.load(FIT_NPZ, allow_pickle=False) as fit, np.load(
        CAMERA_NPZ, allow_pickle=False
    ) as camera:
        camera_hash = str(camera["camera_config_sha256"][0])
        if camera_hash != lock.camera_config_sha256:
            raise RuntimeError("camera configuration hash drifted")
        arrays["camera_config_sha256"] = np.asarray([camera_hash])
        fit_states = {
            "halo": np.asarray(fit["selected_halo_snapshot_states"], dtype=float),
            "vertical": np.asarray(
                fit["selected_vertical_snapshot_states"],
                dtype=float,
            ),
        }
        projection_data: dict[str, dict[str, Any]] = {}
        for figure_id, family, branch, branch_index, _, _ in FIGURES:
            projection = np.asarray(
                camera[f"fig_{figure_id.replace('.', '_')}_projection_matrix"],
                dtype=float,
            )
            placement = np.asarray(
                camera[f"fig_{figure_id.replace('.', '_')}_placement_matrix"],
                dtype=float,
            )
            current_surface = fit_states[family][branch_index, 3]
            previous_surface = fit_states[family][branch_index, 2]
            explicit_surface = explicit_by_figure[figure_id]["explicit"][3]
            reseed_surface = reseed_by_figure[figure_id]["reseeded"]
            nonlinear_surface = explicit_by_figure[figure_id]["nonlinear"][3]
            if float(np.max(np.abs(current_surface - nonlinear_surface))) > 5.0e-12:
                raise RuntimeError(f"fit/audit current surface drifted for Fig. {figure_id}")
            current_uv = project_surface_uv(current_surface, projection, placement)
            previous_uv = project_surface_uv(previous_surface, projection, placement)
            explicit_uv = project_surface_uv(explicit_surface, projection, placement)
            reseed_uv = project_surface_uv(reseed_surface, projection, placement)
            current_mask = rasterize_surface_mask(current_uv)
            previous_mask = rasterize_surface_mask(previous_uv)
            explicit_mask = rasterize_surface_mask(explicit_uv)
            reseed_mask = rasterize_surface_mask(reseed_uv)
            projection_data[figure_id] = {
                "projection": projection,
                "placement": placement,
                "current_uv": current_uv,
                "previous_uv": previous_uv,
                "explicit_uv": explicit_uv,
                "current_mask": current_mask,
                "previous_mask": previous_mask,
                "explicit_mask": explicit_mask,
                "reseed_mask": reseed_mask,
            }
            stem = figure_id.replace(".", "_")
            arrays[f"fig_{stem}_canonical_prediction_mask"] = current_mask
            arrays[f"fig_{stem}_previous_time_prediction_mask"] = previous_mask
            arrays[f"fig_{stem}_explicit_stm_prediction_mask"] = explicit_mask
            arrays[f"fig_{stem}_stm_reseed_prediction_mask"] = reseed_mask
            arrays[f"fig_{stem}_canonical_uv"] = current_uv
            arrays[f"fig_{stem}_previous_time_uv"] = previous_uv
            arrays[f"fig_{stem}_explicit_stm_uv"] = explicit_uv
            arrays[f"fig_{stem}_stm_reseed_uv"] = reseed_uv

    # Projection controls below are explicitly post-hoc and may read panel d.
    for figure_id, family, branch, _, _, _ in FIGURES:
        base_started = time.perf_counter()
        protocol_row = protocol[(figure_id, "d")]
        paper = load_reference_panel_mask(ROOT, protocol_row, allow_holdout=True)
        data = projection_data[figure_id]
        canonical_mask = data["current_mask"]
        canonical_metrics = projection_mask_metrics(paper, canonical_mask)
        frozen = holdout[figure_id]
        for key in (
            "symmetric_chamfer_diagonal_fraction",
            "f1_at_0p01_diagonal",
            "hd95_diagonal_fraction",
            "area_ratio_prediction_over_paper",
            "projection_loss",
        ):
            if abs(float(frozen[key]) - float(canonical_metrics[key])) > 5.0e-13:
                raise RuntimeError(f"frozen holdout replay drifted: {figure_id} {key}")
        stem = figure_id.replace(".", "_")
        arrays[f"fig_{stem}_canonical_reference_mask"] = paper

        variants: list[tuple[str, str, np.ndarray, bool, str]] = [
            (
                "panel_time_mapping",
                "panel_d_with_adjacent_time_c",
                data["previous_mask"],
                True,
                "paper_panel_d",
            ),
            (
                "mask_extraction_order",
                "resize_rgb_then_threshold",
                canonical_mask,
                True,
                "alternative_paper_mask",
            ),
            (
                "quad_rasterizer",
                "two_triangles_per_quad",
                _triangulated_surface_mask(data["current_uv"]),
                True,
                "paper_panel_d",
            ),
            (
                "surface_renderer",
                "matplotlib_polycollection",
                _matplotlib_surface_mask(data["current_uv"]),
                True,
                "paper_panel_d",
            ),
            (
                "explicit_stm_transport",
                "first_order_stm_to_tau_plus_phase",
                data["explicit_mask"],
                False,
                "canonical_nonlinear_prediction",
            ),
            (
                "explicit_stm_transport",
                "stm_phase_transport_normalized_reseed_then_nonlinear_tau",
                data["reseed_mask"],
                False,
                "canonical_nonlinear_prediction",
            ),
        ]
        alternative_paper = _resize_then_threshold_mask(protocol_row)
        arrays[f"fig_{stem}_resize_then_threshold_reference_mask"] = alternative_paper

        for control_id, variant_id, variant_mask, reads_paper, metric_reference in variants:
            started = time.perf_counter()
            if control_id == "mask_extraction_order":
                variant_metrics = projection_mask_metrics(
                    alternative_paper,
                    canonical_mask,
                )
                semantic_metrics = projection_mask_metrics(paper, alternative_paper)
                semantic_reference = paper
            elif control_id == "explicit_stm_transport":
                variant_metrics = projection_mask_metrics(
                    canonical_mask,
                    variant_mask,
                )
                semantic_metrics = variant_metrics
                semantic_reference = canonical_mask
            else:
                variant_metrics = projection_mask_metrics(paper, variant_mask)
                semantic_metrics = projection_mask_metrics(canonical_mask, variant_mask)
                semantic_reference = canonical_mask
            arrays[f"fig_{stem}_{control_id}_variant_mask"] = variant_mask
            arrays[f"fig_{stem}_{control_id}_semantic_reference_mask"] = (
                semantic_reference
            )

            state_rms = None
            state_max = None
            state_hd95_raw = None
            state_hd95_normalized = None
            if control_id == "explicit_stm_transport":
                current_state = explicit_by_figure[figure_id]["nonlinear"][3]
                if variant_id == "first_order_stm_to_tau_plus_phase":
                    explicit_state = explicit_by_figure[figure_id]["explicit"][3]
                    transport_runtime = explicit_by_figure[figure_id]["runtime"]
                else:
                    explicit_state = reseed_by_figure[figure_id]["reseeded"]
                    transport_runtime = reseed_by_figure[figure_id]["runtime"]
                difference = explicit_state - current_state
                state_rms = float(np.sqrt(np.mean(difference**2)))
                state_max = float(np.max(np.abs(difference)))
                state_hd95_raw, state_hd95_normalized = _symmetric_hd95(
                    current_state[..., :3],
                    explicit_state[..., :3],
                )

            delta_loss = (
                None
                if control_id == "explicit_stm_transport"
                else float(
                    variant_metrics["projection_loss"]
                    - canonical_metrics["projection_loss"]
                )
            )
            if control_id == "panel_time_mapping":
                interpretation = (
                    "Adjacent panel time improves exposed loss; mapping remains a post-hoc candidate."
                    if delta_loss is not None and delta_loss < 0.0
                    else "Adjacent panel time does not improve exposed loss."
                )
            elif control_id == "mask_extraction_order":
                interpretation = (
                    "Resize/threshold ordering is close to the frozen mask."
                    if _semantic_gate(semantic_metrics) == "close"
                    else "Resize/threshold ordering materially changes the extracted mask."
                )
            elif control_id == "quad_rasterizer":
                interpretation = (
                    "Triangle decomposition is close to the frozen quad union."
                    if _semantic_gate(semantic_metrics) == "close"
                    else "Triangle decomposition materially changes the rasterized union."
                )
            elif control_id == "surface_renderer":
                interpretation = (
                    "Matplotlib polygon rendering is close to the deterministic union."
                    if _semantic_gate(semantic_metrics) == "close"
                    else "Matplotlib polygon rendering materially changes the surface mask."
                )
            else:
                interpretation = (
                    "First-order STM transport is close to nonlinear tau+phase geometry."
                    if _semantic_gate(semantic_metrics) == "close"
                    else "First-order STM transport differs materially from nonlinear tau+phase geometry."
                )

            row: dict[str, Any] = {
                "schema_version": SCHEMA_VERSION,
                "control_id": control_id,
                "variant_id": variant_id,
                "figure_id": figure_id,
                "family": family,
                "branch": branch,
                "panel_id": "d",
                "canonical_snapshot_index": 3,
                "variant_snapshot_index": 2 if control_id == "panel_time_mapping" else 3,
                "changed_factor": control_id,
                "fixed_camera": True,
                "fixed_epsilon": True,
                "fixed_crop": True,
                "fixed_thresholds": True,
                "historical_exposure": True,
                "paper_mask_read": reads_paper,
                "variant_metric_reference": metric_reference,
                **_metric_fields("canonical", canonical_metrics),
                **_metric_fields("variant", variant_metrics),
                "delta_projection_loss_from_canonical": delta_loss,
                "semantic_chamfer_fraction": semantic_metrics[
                    "symmetric_chamfer_diagonal_fraction"
                ],
                "semantic_f1": semantic_metrics["f1_at_0p01_diagonal"],
                "semantic_hd95_fraction": semantic_metrics[
                    "hd95_diagonal_fraction"
                ],
                "semantic_area_ratio": semantic_metrics[
                    "area_ratio_prediction_over_paper"
                ],
                "state_rms_difference": state_rms,
                "state_max_abs_difference": state_max,
                "state_hd95_raw": state_hd95_raw,
                "state_hd95_normalized": state_hd95_normalized,
                "variant_protocol_gate": (
                    "not_applicable"
                    if control_id == "explicit_stm_transport"
                    else _protocol_gate(variant_metrics)
                ),
                "semantic_similarity_gate": _semantic_gate(semantic_metrics),
                "interpretation": interpretation,
                "control_runtime_seconds": (
                    time.perf_counter() - started
                    + (
                        transport_runtime
                        if control_id == "explicit_stm_transport"
                        else 0.0
                    )
                    + (time.perf_counter() - base_started if control_id == CONTROLS[0] else 0.0)
                ),
                "paper_projection_acceptance": "fail",
                "paper_3d_equivalence": False,
                "fit_lock_sha256": lock.fit_lock_sha256,
                "holdout_csv_sha256": lock.holdout_csv_sha256,
                "camera_config_sha256": lock.camera_config_sha256,
                **hashes,
            }
            rows.append(row)

    if len(rows) != (len(CONTROLS) + 1) * len(FIGURES):
        raise RuntimeError("negative-control row count drifted")
    return rows, arrays


def _rows_with_hash(rows: Sequence[Mapping[str, Any]], npz_hash: str) -> list[dict[str, str]]:
    formatted: list[dict[str, str]] = []
    for source in rows:
        row = {column: _fmt(source.get(column)) for column in CSV_COLUMNS}
        row["npz_sha256"] = npz_hash
        formatted.append(row)
    return formatted


def _render_doc(rows: Sequence[Mapping[str, str]], npz_hash: str) -> str:
    grouped: dict[str, list[Mapping[str, str]]] = {
        control: [row for row in rows if row["control_id"] == control]
        for control in CONTROLS
    }
    table = [
        "| control | variant | mean semantic F1 | max semantic HD95/D | protocol passes | interpretation |",
        "|---|---|---:|---:|---:|---|",
    ]
    for control in CONTROLS:
        subset = grouped[control]
        mean_f1 = float(np.mean([float(row["semantic_f1"]) for row in subset]))
        max_hd95 = float(
            np.max([float(row["semantic_hd95_fraction"]) for row in subset])
        )
        passes = sum(row["variant_protocol_gate"] == "pass" for row in subset)
        table.append(
            f"| {control} | {subset[0]['variant_id']} | {mean_f1:.4f} | "
            f"{max_hd95:.4f} | {passes}/{len(subset)} | "
            f"{subset[0]['interpretation']} |"
        )

    panel_rows = grouped["panel_time_mapping"]
    panel_improvements = sum(
        float(row["delta_projection_loss_from_canonical"]) < 0.0
        for row in panel_rows
    )
    renderer_material = sum(
        row["semantic_similarity_gate"] == "material_difference"
        for control in ("mask_extraction_order", "quad_rasterizer", "surface_renderer")
        for row in grouped[control]
    )
    transport_material = sum(
        row["semantic_similarity_gate"] == "material_difference"
        for row in grouped["explicit_stm_transport"]
    )
    return "\n".join(
        [
            "# Chapter 4 frozen projection/transport negative controls",
            "",
            "All rows are post-hoc diagnostics with historical exposure. Camera, epsilon, crop, red threshold, protocol gates, source members, and the frozen v1 holdout are unchanged.",
            "",
            *table,
            "",
            "## Bounded conclusion",
            "",
            f"- Replacing panel-(d) time by the adjacent panel-(c) time lowers exposed loss in {panel_improvements}/4 rows. This is diagnostic only and no time remapping is selected.",
            f"- Mask/rasterizer/renderer alternatives show material mask differences in {renderer_material}/12 rows under the fixed semantic-similarity gate.",
            f"- The two explicit STM transport variants differ materially from nonlinear tau+phase geometry in {transport_material}/{len(grouped['explicit_stm_transport'])} rows.",
            "- No control is allowed to change paper_projection=fail, paper_3d=false, or the stored 0/4 holdout.",
            "- These controls can falsify a simple implementation-semantic explanation; they cannot recover unpublished original 3D states or prove paper equivalence.",
            "",
            "## Artifacts",
            "",
            f"- CSV: {_display(CSV_PATH)}",
            f"- NPZ: {_display(NPZ_PATH)}",
            f"- NPZ SHA-256: {npz_hash}",
            f"- Generator: {_display(Path(__file__))}",
            "",
        ]
    )


def _compare_npz(expected: Mapping[str, np.ndarray]) -> None:
    if not NPZ_PATH.is_file():
        raise RuntimeError("stored negative-control NPZ is missing")
    with np.load(NPZ_PATH, allow_pickle=False) as stored:
        if set(stored.files) != set(expected):
            raise RuntimeError("negative-control NPZ keys drifted")
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
                raise RuntimeError(f"negative-control NPZ array drift: {key}")


def _write_npz(arrays: Mapping[str, np.ndarray]) -> None:
    temporary = NPZ_PATH.with_name(NPZ_PATH.stem + ".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    temporary.replace(NPZ_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows, arrays = analyze()
    if args.check:
        _compare_npz(arrays)
        npz_hash = _sha256(NPZ_PATH)
        if not CSV_PATH.is_file():
            raise RuntimeError("stored negative-control CSV is missing")
        stored_rows = _read_csv(CSV_PATH)
        if len(stored_rows) != len(rows):
            raise RuntimeError("negative-control CSV row count drifted")
        for recomputed, stored in zip(rows, stored_rows):
            recomputed["control_runtime_seconds"] = stored["control_runtime_seconds"]
        expected_rows = _rows_with_hash(rows, npz_hash)
        if CSV_PATH.read_text(encoding="utf-8") != _csv_text(expected_rows):
            raise RuntimeError("stored negative-control CSV drifted")
        expected_doc = _render_doc(expected_rows, npz_hash)
        if not DOC_PATH.is_file() or DOC_PATH.read_text(encoding="utf-8") != expected_doc:
            raise RuntimeError("stored negative-control report drifted")
        print("chapter4 negative controls CHECK PASS rows=24 frozen_holdout=fail")
        return 0

    _write_npz(arrays)
    npz_hash = _sha256(NPZ_PATH)
    formatted = _rows_with_hash(rows, npz_hash)
    CSV_PATH.write_text(_csv_text(formatted), encoding="utf-8", newline="\n")
    DOC_PATH.write_text(
        _render_doc(formatted, npz_hash),
        encoding="utf-8",
        newline="\n",
    )
    print("chapter4 negative controls WRITE PASS rows=24 frozen_holdout=fail")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
