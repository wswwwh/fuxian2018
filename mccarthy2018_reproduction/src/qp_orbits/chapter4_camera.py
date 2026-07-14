"""Frozen thesis-camera definitions for Chapter 4 Figures 4.3--4.6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Chapter4PaperCamera:
    figure_id: str
    elevation_deg: float
    azimuth_deg: float
    roll_deg: float
    xlim: tuple[float, float]
    ylim: tuple[float, float]
    zlim: tuple[float, float]
    box_aspect: tuple[float, float, float]
    projection_type: str = "ortho"


_ELEVATION = 35.264389682754654

CHAPTER4_PAPER_CAMERAS: dict[str, Chapter4PaperCamera] = {
    "4.3": Chapter4PaperCamera(
        "4.3",
        _ELEVATION,
        -45.0,
        0.0,
        (0.80, 1.18),
        (-0.15, 0.15),
        (-0.10, 0.10),
        (0.38, 0.30, 0.20),
    ),
    "4.4": Chapter4PaperCamera(
        "4.4",
        _ELEVATION,
        -45.0,
        0.0,
        (0.20, 1.00),
        (-0.15, 0.35),
        (-0.10, 0.10),
        (0.80, 0.50, 0.20),
    ),
    "4.5": Chapter4PaperCamera(
        "4.5",
        _ELEVATION,
        -65.0,
        0.0,
        (0.80, 1.18),
        (-0.15, 0.15),
        (-0.10, 0.10),
        (0.38, 0.30, 0.20),
    ),
    "4.6": Chapter4PaperCamera(
        "4.6",
        _ELEVATION,
        110.0,
        0.0,
        (0.10, 1.00),
        (-0.15, 0.40),
        (-0.15, 0.15),
        (0.90, 0.55, 0.30),
    ),
}


def chapter4_axis_corner_positions(figure_id: str) -> np.ndarray:
    """Return paper axis corners A, B, C, D in data coordinates.

    A is the z/x corner, B the x/y corner, C the far end of the visible y
    edge, and D the other end of the visible z edge.  Figure 4.6 uses the
    opposite visible cube corner, uniquely fixed by its increasing tick
    directions at azimuth 110 degrees.
    """

    camera = CHAPTER4_PAPER_CAMERAS[figure_id]
    x0, x1 = camera.xlim
    y0, y1 = camera.ylim
    z0, z1 = camera.zlim
    if figure_id == "4.6":
        return np.asarray(
            [
                (x1, y1, z0),
                (x0, y1, z0),
                (x0, y0, z0),
                (x1, y1, z1),
            ],
            dtype=float,
        )
    return np.asarray(
        [
            (x0, y0, z0),
            (x1, y0, z0),
            (x1, y1, z0),
            (x0, y0, z1),
        ],
        dtype=float,
    )


def apply_chapter4_paper_camera(ax: Any, figure_id: str, *, zoom: float = 1.0) -> None:
    """Apply the frozen orthographic thesis view to a Matplotlib 3D axis."""

    camera = CHAPTER4_PAPER_CAMERAS[figure_id]
    ax.set_proj_type(camera.projection_type)
    ax.view_init(
        elev=camera.elevation_deg,
        azim=camera.azimuth_deg,
        roll=camera.roll_deg,
    )
    ax.set_xlim(*camera.xlim)
    ax.set_ylim(*camera.ylim)
    ax.set_zlim(*camera.zlim)
    ax.set_box_aspect(camera.box_aspect, zoom=zoom)
