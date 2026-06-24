"""Build the 54-figure reproduction index from the thesis figure list."""

from __future__ import annotations

import csv
from pathlib import Path

from _paths import PROJECT_ROOT


FIGURES = [
    ("2.1", 8, "schematic", 0, "Geometry in the three-body system and reference frames"),
    ("2.2", 14, "schematic", 0, "Collinear libration point geometry"),
    ("2.3", 14, "numeric", 1, "Relative locations of the five libration points"),
    ("2.4", 16, "numeric", 1, "Earth-Moon zero-velocity curves for JC=3.16 and JC=3.18"),
    ("2.5", 17, "numeric", 1, "Earth-Moon rotating frame"),
    ("2.6", 18, "numeric", 1, "ZVC comparison for Earth-Moon, Saturn-Titan, and Sun-Earth"),
    ("2.7", 24, "numeric", 1, "Linearized in-plane and out-of-plane variations at Earth-Moon L1"),
    ("2.8", 24, "numeric", 1, "Linearized Lissajous motion around Earth-Moon L1"),
    ("2.9", 29, "schematic", 2, "Single-shooting differential corrections targeting"),
    ("2.10", 31, "schematic", 2, "Multiple-shooting trajectory arcs"),
    ("2.11", 34, "numeric", 2, "L2 Lyapunov initial guess and corrected solution"),
    ("2.12", 39, "schematic", 2, "Natural and pseudo-arclength continuation"),
    ("2.13", 40, "numeric", 2, "Jupiter-Europa L2 Lyapunov, halo, and vertical families"),
    ("2.14", 43, "numeric", 2, "Stable and unstable manifolds from an L1 Lyapunov orbit"),
    ("2.15", 45, "numeric", 2, "Stability index for Earth-Moon L2 halo family"),
    ("3.1", 48, "schematic", 3, "Two-dimensional torus as product of two circles"),
    ("3.2", 49, "schematic", 3, "Invariant curve, rotation angle, and return trajectory"),
    ("3.3", 49, "schematic", 3, "Seven-point discretized invariant curve mapping"),
    ("3.4", 62, "schematic", 3, "Patch curves for multiple-shooting torus correction"),
    ("3.5", 68, "numeric", 3, "Constant-energy quasi-halo tori, JC=3.1389"),
    ("3.6", 69, "numeric", 3, "Constant-energy quasi-halo amplitudes"),
    ("3.7", 70, "numeric", 3, "Constant-energy quasi-vertical tori, JC=3.1389"),
    ("3.8", 71, "numeric", 3, "Constant-energy quasi-vertical amplitudes"),
    ("3.9", 71, "numeric", 3, "Frequency ratio versus mapping time"),
    ("3.10", 72, "numeric", 3, "Period-2, period-3, and period-8 halo examples"),
    ("3.11", 73, "numeric", 3, "Poincare map and central periodic orbits"),
    ("3.12", 76, "numeric", 3, "Constant-frequency quasi-halo tori"),
    ("3.13", 77, "numeric", 3, "Constant-frequency quasi-halo amplitudes and Jacobi constant"),
    ("3.14", 78, "numeric", 3, "Constant-frequency quasi-vertical tori"),
    ("3.15", 79, "numeric", 3, "Constant-frequency quasi-vertical Jacobi constant and mapping time"),
    ("3.16", 82, "numeric", 3, "Constant-mapping-time quasi-DRO tori"),
    ("3.17", 83, "numeric", 3, "Quasi-DRO amplitude and Jacobi constant versus rotation angle"),
    ("4.1", 86, "numeric", 4, "Earth-Moon L2 quasi-halo orbit and DG eigenstructure"),
    ("4.2", 87, "numeric", 4, "Quasi-halo stability index versus mapping time"),
    ("4.3", 89, "numeric", 4, "Quasi-halo unstable manifold in +x direction"),
    ("4.4", 90, "numeric", 4, "Quasi-halo unstable manifold in -x direction"),
    ("4.5", 91, "numeric", 4, "Quasi-vertical unstable manifold in +x direction"),
    ("4.6", 92, "numeric", 4, "Quasi-vertical unstable manifold in -x direction"),
    ("4.7", 93, "numeric", 4, "Quasi-halo and periodic halo manifold comparison"),
    ("4.8", 93, "numeric", 4, "Quasi-vertical and periodic halo manifold comparison"),
    ("5.1", 96, "application", 5, "Sun-Earth L1 quasi-vertical long propagation"),
    ("5.2", 98, "schematic", 5, "Sun-Moon eclipsing geometry"),
    ("5.3", 100, "schematic", 5, "Earth-Moon-spacecraft line-of-sight geometry"),
    ("5.4", 101, "schematic", 5, "Sun-Earth-Moon synodic geometry"),
    ("5.5", 102, "application", 5, "Quasi-DRO and associated planar periodic DRO"),
    ("5.6", 103, "application", 5, "Quasi-DRO ephemeris trajectories by phase"),
    ("5.7", 104, "application", 5, "Quasi-DRO ephemeris trajectories by insertion epoch"),
    ("5.8", 106, "application", 5, "Halo-to-Lyapunov transfer initial guess and converged transfer"),
    ("5.9", 107, "application", 5, "NRHOs and potential departure locations"),
    ("5.10", 108, "application", 5, "Converged transfer trajectories for two departure locations"),
    ("5.11", 109, "application", 5, "Converged transfer between two NRHOs"),
    ("5.12", 109, "application", 5, "Rendezvous maneuver versus arrival time"),
    ("5.13", 111, "application", 5, "Periapsis heat map from Sun-Earth L1 stable manifolds"),
    ("5.14", 112, "application", 5, "LEO to quasi-periodic Sun-Earth L1 Lissajous transfer"),
]


IMPLEMENTED = {
    "2.1",
    "2.2",
    "2.3",
    "2.4",
    "2.5",
    "2.6",
    "2.7",
    "2.8",
    "2.9",
    "2.10",
    "2.11",
    "2.12",
    "2.13",
    "2.14",
    "2.15",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.5",
    "3.6",
    "3.7",
    "3.8",
    "3.9",
    "3.9",
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
    "3.15",
    "3.16",
    "3.17",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "4.7",
    "4.8",
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5",
    "5.6",
    "5.7",
    "5.8",
    "5.9",
    "5.10",
    "5.11",
    "5.12",
    "5.13",
    "5.14",
}
SHAPE_MATCH = {
    "2.1",
    "2.2",
    "2.5",
    "2.9",
    "2.10",
    "2.12",
    "2.13",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "3.9",
    "3.10",
    "3.11",
    "3.16",
    "3.17",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "4.7",
    "4.8",
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5",
    "5.6",
    "5.7",
    "5.8",
    "5.9",
    "5.10",
    "5.11",
    "5.12",
    "5.13",
    "5.14",
}
LOCAL_NUMERICAL = {
    "2.13",
    "3.9",
    "3.10",
    "3.16",
    "3.17",
    "4.1",
    "4.2",
    "4.3",
    "4.4",
    "4.5",
    "4.6",
    "4.7",
    "4.8",
    "5.1",
    "5.5",
    "5.6",
    "5.7",
    "5.8",
    "5.9",
    "5.10",
    "5.11",
    "5.12",
    "5.13",
    "5.14",
}


def dependency_label(stage: int) -> str:
    labels = {
        0: "reference/schematic",
        1: "cr3bp-basics",
        2: "periodic-orbits",
        3: "quasi-periodic-tori",
        4: "torus-stability-manifolds",
        5: "applications",
    }
    return labels[stage]


def main() -> Path:
    out_path = PROJECT_ROOT / "data" / "figure_index.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "figure_id",
                "source_page",
                "pdf_page",
                "figure_type",
                "dependency_stage",
                "dependency_label",
                "title",
                "script",
                "status",
                "repro_level",
            ],
        )
        writer.writeheader()
        for figure_id, source_page, figure_type, stage, title in FIGURES:
            chapter, number = figure_id.split(".")
            script = f"figures/fig_{int(chapter)}_{int(number):02d}.py"
            writer.writerow(
                {
                    "figure_id": figure_id,
                    "source_page": source_page,
                    "pdf_page": source_page + 16,
                    "figure_type": figure_type,
                    "dependency_stage": stage,
                    "dependency_label": dependency_label(stage),
                    "title": title,
                    "script": script,
                    "status": "implemented" if figure_id in IMPLEMENTED else "planned",
                    "repro_level": (
                        "shape-match + local numerical"
                        if figure_id in LOCAL_NUMERICAL
                        else "shape-match"
                        if figure_id in SHAPE_MATCH
                        else "physical-consistency"
                        if figure_id in IMPLEMENTED
                        else "not-started"
                    ),
                }
            )
    print(f"Wrote {out_path} ({len(FIGURES)} rows)")
    return out_path


if __name__ == "__main__":
    main()
