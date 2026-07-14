"""Deterministic projection-mask utilities for Chapter 4 manifold figures."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Mapping

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import distance_transform_edt


NORMALIZED_PANEL_SIZE = 512
RED_MINIMUM = 55
RED_DOMINANCE_MINIMUM = 14
RED_RATIO_MINIMUM = 1.10


class HoldoutLeakageError(RuntimeError):
    """Raised when the fit path attempts to load panel-(d) red pixels."""


def red_dominance_mask(image: Image.Image) -> np.ndarray:
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    red = rgb[:, :, 0]
    competitor = np.maximum(rgb[:, :, 1], rgb[:, :, 2])
    return (
        (red >= RED_MINIMUM)
        & (red - competitor >= RED_DOMINANCE_MINIMUM)
        & (red >= RED_RATIO_MINIMUM * competitor)
    )


def load_reference_panel_mask(
    project_root: Path,
    protocol_row: Mapping[str, str],
    *,
    allow_holdout: bool = False,
) -> np.ndarray:
    """Load one protocol-bound paper mask, rejecting holdout use by default."""

    panel_id = protocol_row["panel_id"]
    if panel_id == "d" and not allow_holdout:
        raise HoldoutLeakageError(
            "Panel (d) red pixels are forbidden before the projection fit is locked"
        )
    source = project_root / protocol_row["paper_source"]
    x0 = math.floor(float(protocol_row["panel_rect_x0"]))
    y0 = math.floor(float(protocol_row["panel_rect_y0"]))
    x1 = math.ceil(float(protocol_row["panel_rect_x1"]))
    y1 = math.ceil(float(protocol_row["panel_rect_y1"]))
    with Image.open(source) as opened:
        native = red_dominance_mask(opened.convert("RGB").crop((x0, y0, x1, y1)))
    resized = Image.fromarray(native.astype(np.uint8) * 255, mode="L").resize(
        (NORMALIZED_PANEL_SIZE, NORMALIZED_PANEL_SIZE),
        Image.Resampling.NEAREST,
    )
    mask = np.asarray(resized, dtype=np.uint8) > 0
    if not mask.any():
        raise RuntimeError("Reference red mask is empty")
    return mask


def project_surface_uv(
    surface_states: np.ndarray,
    projection_matrix: np.ndarray,
    placement_matrix: np.ndarray,
) -> np.ndarray:
    """Project a ``(phase, curve, 6)`` state surface to normalized image UV."""

    states = np.asarray(surface_states, dtype=float)
    if states.ndim != 3 or states.shape[-1] != 6:
        raise ValueError("surface_states must have shape (phase, curve, 6)")
    xyz = states[..., :3]
    homogeneous = np.concatenate(
        (xyz.reshape(-1, 3), np.ones((xyz.shape[0] * xyz.shape[1], 1))),
        axis=1,
    )
    clip = homogeneous @ np.asarray(projection_matrix, dtype=float).T
    ndc = clip[:, :2] / clip[:, 3:4]
    uv = np.column_stack((ndc, np.ones(ndc.shape[0]))) @ np.asarray(
        placement_matrix, dtype=float
    )
    return uv.reshape(xyz.shape[0], xyz.shape[1], 2)


def rasterize_surface_mask(
    uv: np.ndarray,
    *,
    size: int = NORMALIZED_PANEL_SIZE,
) -> np.ndarray:
    """Rasterize the alpha-independent surface union, closing curve only."""

    values = np.asarray(uv, dtype=float)
    if values.ndim != 3 or values.shape[-1] != 2:
        raise ValueError("uv must have shape (phase, curve, 2)")
    if values.shape[0] < 2 or values.shape[1] < 2:
        raise ValueError("uv needs at least two phase and curve samples")
    pixels = values * float(size - 1)
    image = Image.new("1", (size, size), 0)
    draw = ImageDraw.Draw(image)
    phase_count, curve_count = values.shape[:2]
    for phase_index in range(phase_count - 1):
        for curve_index in range(curve_count):
            next_curve = (curve_index + 1) % curve_count
            polygon = (
                tuple(pixels[phase_index, curve_index]),
                tuple(pixels[phase_index + 1, curve_index]),
                tuple(pixels[phase_index + 1, next_curve]),
                tuple(pixels[phase_index, next_curve]),
            )
            draw.polygon(polygon, fill=1)
    mask = np.asarray(image, dtype=bool)
    if not mask.any():
        raise RuntimeError("Projected surface mask is empty")
    return mask


def projection_mask_metrics(
    paper: np.ndarray,
    prediction: np.ndarray,
) -> dict[str, float]:
    """Return the protocol's symmetric distance, F1, HD95, area, and loss."""

    paper_mask = np.asarray(paper, dtype=bool)
    predicted_mask = np.asarray(prediction, dtype=bool)
    if paper_mask.shape != predicted_mask.shape:
        raise ValueError("Mask shapes differ")
    if not paper_mask.any() or not predicted_mask.any():
        raise ValueError("Masks must contain foreground")
    distance_to_paper = distance_transform_edt(~paper_mask)
    distance_to_prediction = distance_transform_edt(~predicted_mask)
    paper_distances = distance_to_prediction[paper_mask]
    prediction_distances = distance_to_paper[predicted_mask]
    chamfer = 0.5 * (
        float(np.mean(paper_distances)) + float(np.mean(prediction_distances))
    )
    diagonal = float(np.hypot(*paper_mask.shape))
    tolerance = 0.01 * diagonal
    precision = float(np.mean(prediction_distances <= tolerance))
    recall = float(np.mean(paper_distances <= tolerance))
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.0
    hd95 = max(
        float(np.percentile(paper_distances, 95.0)),
        float(np.percentile(prediction_distances, 95.0)),
    )
    area_ratio = float(np.count_nonzero(predicted_mask) / np.count_nonzero(paper_mask))
    loss = (
        chamfer / diagonal
        + 0.5 * (1.0 - f1)
        + 0.25 * abs(math.log(area_ratio))
        + 0.25 * hd95 / diagonal
    )
    return {
        "symmetric_chamfer_px": chamfer,
        "symmetric_chamfer_diagonal_fraction": chamfer / diagonal,
        "precision_at_0p01_diagonal": precision,
        "recall_at_0p01_diagonal": recall,
        "f1_at_0p01_diagonal": f1,
        "hd95_px": hd95,
        "hd95_diagonal_fraction": hd95 / diagonal,
        "area_ratio_prediction_over_paper": area_ratio,
        "projection_loss": loss,
    }


def log2_refinement_grid(center: float) -> np.ndarray:
    if center <= 0.0:
        raise ValueError("center must be positive")
    return center * 2.0 ** np.linspace(-0.25, 0.25, 5)
