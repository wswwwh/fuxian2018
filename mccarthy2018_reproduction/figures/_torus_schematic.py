"""Helpers for Chapter 3 torus schematic figures."""

from __future__ import annotations

import numpy as np


def torus_mesh(major_radius: float = 2.45, minor_radius: float = 0.62, n_major: int = 120, n_minor: int = 44):
    u = np.linspace(0.0, 2.0 * np.pi, n_major)
    v = np.linspace(0.0, 2.0 * np.pi, n_minor)
    uu, vv = np.meshgrid(u, v)
    x = (major_radius + minor_radius * np.cos(vv)) * np.cos(uu)
    y = (major_radius + minor_radius * np.cos(vv)) * np.sin(uu)
    z = minor_radius * np.sin(vv)
    return x, y, z


def torus_curve(u, v, major_radius: float = 2.45, minor_radius: float = 0.62):
    u = np.asarray(u)
    v = np.asarray(v)
    x = (major_radius + minor_radius * np.cos(v)) * np.cos(u)
    y = (major_radius + minor_radius * np.cos(v)) * np.sin(u)
    z = minor_radius * np.sin(v)
    return x, y, z


def section_circle(u0: float, major_radius: float = 2.45, minor_radius: float = 0.62, scale: float = 1.04, n: int = 160):
    v = np.linspace(0.0, 2.0 * np.pi, n)
    return torus_curve(np.full_like(v, u0), v, major_radius, minor_radius * scale)


def section_disk(u0: float, major_radius: float = 2.45, minor_radius: float = 0.62, scale: float = 1.02):
    rho = np.linspace(0.0, minor_radius * scale, 12)
    v = np.linspace(0.0, 2.0 * np.pi, 72)
    rr, vv = np.meshgrid(rho, v)
    er = np.array([np.cos(u0), np.sin(u0), 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    center = np.array([major_radius * np.cos(u0), major_radius * np.sin(u0), 0.0])
    pts = center[:, None, None] + rr[None, :, :] * (
        np.cos(vv)[None, :, :] * er[:, None, None] + np.sin(vv)[None, :, :] * ez[:, None, None]
    )
    return pts[0], pts[1], pts[2]


def plot_torus(ax, alpha: float = 0.48) -> None:
    x, y, z = torus_mesh()
    ax.plot_surface(
        x,
        y,
        z,
        rstride=1,
        cstride=1,
        color="#b8b8b8",
        edgecolor="none",
        linewidth=0,
        antialiased=True,
        shade=True,
        alpha=alpha,
    )


def add_curve_arrow(ax, x, y, z, index: int, color: str, length: float = 0.28, linewidth: float = 1.5) -> None:
    idx = int(np.clip(index, 1, len(x) - 2))
    direction = np.array([x[idx + 1] - x[idx - 1], y[idx + 1] - y[idx - 1], z[idx + 1] - z[idx - 1]])
    norm = np.linalg.norm(direction)
    if norm == 0.0:
        return
    direction = direction / norm * length
    ax.quiver(
        x[idx],
        y[idx],
        z[idx],
        direction[0],
        direction[1],
        direction[2],
        color=color,
        arrow_length_ratio=0.55,
        linewidth=linewidth,
        normalize=False,
    )


def clean_torus_axes(ax) -> None:
    ax.set_axis_off()
    ax.set_xlim(-3.45, 3.45)
    ax.set_ylim(-2.95, 3.05)
    ax.set_zlim(-1.25, 1.25)
    ax.set_box_aspect((5.5, 4.0, 1.9))
    ax.view_init(elev=26, azim=-58)
