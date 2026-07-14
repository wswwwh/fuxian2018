"""Build the paper-target registry used by reproduction audits."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

from _paths import PROJECT_ROOT


PURE_SCHEMATIC_IDS = {
    "2.1",
    "2.2",
    "2.5",
    "2.9",
    "2.10",
    "2.12",
    "3.1",
    "3.2",
    "3.3",
    "3.4",
    "5.2",
    "5.3",
    "5.4",
}


PAPER_TARGETS = {
    "2.3": "general CR3BP libration-point geometry; L1/L2/L3 on x-axis; L4/L5=(1/2-mu,+/-sqrt(3)/2)",
    "2.4": "Earth-Moon zero-velocity curves at JC=3.16 and JC=3.18",
    "2.6": "ZVC comparison: Earth-Moon mu=0.01215; Saturn-Titan mu=0.0002366; Sun-Earth mu=3.0035e-6",
    "2.7": "Earth-Moon L1 decoupled in-plane and out-of-plane first-order modes; equations 2.61-2.66",
    "2.8": "Earth-Moon L1 linear Lissajous motion coupling in-plane and out-of-plane modes; equations 2.67-2.72",
    "2.11": "Earth-Moon L2 planar Lyapunov correction; x0=[x0,0,0,0,ydot0,0]; free variables=[x0,ydot0,T]; constraints=[y(T),xdot(T)]=0",
    "2.13": "Jupiter-Europa L2 Lyapunov, halo, and vertical families; mu=2.528e-5",
    "2.14": "Earth-Moon L1 Lyapunov stable/unstable manifolds; JC=3.1827",
    "2.15": "Earth-Moon L2 halo-family stability index; nu=(abs(lambda_max)+1/abs(lambda_max))/2; stable nu=1; unstable nu>1",
    "3.5": "constant-energy quasi-halo family; JC=3.1389; T0=12.03,12.09,12.26,12.40 day",
    "3.6": "constant-energy quasi-halo amplitude and amplitude-ratio curves; JC=3.1389",
    "3.7": "constant-energy quasi-vertical family; JC=3.1389; T0=12.87,12.85,12.78,12.66 day",
    "3.8": "constant-energy quasi-vertical amplitude and amplitude-ratio curves; JC=3.1389",
    "3.9": "frequency ratio versus mapping time for constant-energy quasi-halo and quasi-vertical families; JC=3.1389",
    "3.10": "Earth-Moon period-2, period-3, and period-8 halo examples",
    "3.11": "Poincare map and central periodic orbits; JC=3.1389; section z=0",
    "3.12": "constant-frequency quasi-halo family; omega1/omega0=9.441; JC=3.1182,3.0876,3.0364,3.0011",
    "3.13": "constant-frequency quasi-halo amplitude and JC curves; omega1/omega0=9.441",
    "3.14": "constant-frequency quasi-vertical family; omega1/omega0=9.441; JC=3.0433,3.0387,3.0305,3.0291",
    "3.15": "constant-frequency quasi-vertical JC and mapping-time curves; omega1/omega0=9.441",
    "3.16": "constant-mapping-time quasi-DRO tori; T0=14.74 day; JC=2.9225,2.9221,2.9215,2.9212",
    "3.17": "constant-mapping-time quasi-DRO z-amplitude and JC versus rho; T0=14.74 day; digitized rho about 1.436..1.510",
    "4.1": "Earth-Moon L2 quasi-halo; JC=3.044; N=25; stability index nu=1.3837",
    "4.2": "L1 constant-energy quasi-halo stability index versus T0; JC=3.1389; include associated periodic halo anchor",
    "4.3": "L1 quasi-halo +x unstable manifold; JC=3.1389; snapshots=7.79,9.75,11.39,13.02 day",
    "4.4": "L1 quasi-halo -x unstable manifold; JC=3.1389; snapshots=7.79,9.75,11.39,13.02 day",
    "4.5": "L1 quasi-vertical +x unstable manifold; JC=3.1389; snapshots=8.05,10.08,11.77,13.46 day",
    "4.6": "L1 quasi-vertical -x unstable manifold; JC=3.1389; snapshots=8.05,10.08,11.77,13.46 day",
    "4.7": "L1 quasi-halo unstable manifold compared with associated periodic halo manifold",
    "4.8": "L1 quasi-vertical unstable manifold compared with associated periodic-orbit manifold",
    "5.1": "single corrected Sun-Earth L1 quasi-vertical trajectory propagated 325,1068,2182 day",
    "5.5": "quasi-DRO T0=14.75 day; planar DRO rp=73800 km; 10 returns=147.5 day; planar LOS outage about 2.3 h/rev; quasi-DRO zero outage",
    "5.6": "DE421 Sun-Earth-Moon ephemeris-corrected quasi-DRO; epoch=2020-06-15; insertion phase=0,24,80,120 deg",
    "5.7": "DE421 Sun-Earth-Moon ephemeris-corrected quasi-DRO; insertion epochs=2020-06-01,04,10,15",
    "5.8": "halo-to-Lyapunov transfer; delta-v=139.4+4.0=143.4 m/s; TOF=186.9 day",
    "5.9": "northern L2 NRHO rp=4800,12610 km; stability index=1.5425,1.1762; constant-frequency quasi-NRHO corridor anchored at periodic NRHO rp=8065 km and frequency ratio=5.0305",
    "5.10": "autonomous Earth-Moon CR3BP feasible solutions (not the later SQP optima): transfer 1=48.3+32.2=80.5 m/s, TOF=23 day; transfer 2=51.3+35.3=86.6 m/s, TOF=12.4 day; epoch not applicable",
    "5.11": "CR3BP-symmetric reverse transfers from rp=12610 km NRHO to rp=4800 km NRHO using accepted Fig.5.10 solutions",
    "5.12": "rendezvous delta-v versus arrival offset; baseline=80.5 m/s; offset=-24..24 h; minimum near -6.5 h",
    "5.13": "Sun-Earth L1 two-frequency Lissajous torus; z=940000 km; y=660000 km; at least 3500 torus points; candidate periapsis about 7033 km",
    "5.14": "stable-manifold transfer to 185 km LEO (geocentric radius 6563 km); zero deterministic insertion maneuver after departure",
}


FIELDNAMES = [
    "figure_id",
    "source_page",
    "pdf_page",
    "figure_type",
    "title",
    "script",
    "acceptance_tier",
    "target_status",
    "paper_targets",
    "source_type",
    "current_repro_level",
    "uses_proxy",
    "validation_artifact",
    "next_action",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def build_rows(project_root: Path) -> list[dict[str, str]]:
    figure_rows = read_rows(project_root / "data" / "figure_index.csv")
    validation_rows = read_rows(
        project_root / "data" / "computed" / "figure_validation_table.csv"
    )
    validation_by_id = {row["figure_id"]: row for row in validation_rows}
    output: list[dict[str, str]] = []
    for figure in figure_rows:
        figure_id = figure["figure_id"]
        validation = validation_by_id[figure_id]
        schematic = figure_id in PURE_SCHEMATIC_IDS
        explicit_target = PAPER_TARGETS.get(figure_id)
        output.append(
            {
                "figure_id": figure_id,
                "source_page": figure["source_page"],
                "pdf_page": figure["pdf_page"],
                "figure_type": "schematic" if schematic else figure["figure_type"],
                "title": figure["title"],
                "script": figure["script"],
                "acceptance_tier": "V0" if schematic else "V2",
                "target_status": (
                    "schematic_semantics_recorded"
                    if schematic
                    else "explicit_parameters_recorded"
                    if explicit_target
                    else "caption_target_needs_parameter_extraction"
                ),
                "paper_targets": explicit_target or figure["title"],
                "source_type": "explicit",
                "current_repro_level": validation["current_repro_level"],
                "uses_proxy": validation["uses_proxy"],
                "validation_artifact": validation["main_data_source"],
                "next_action": validation["next_action"],
            }
        )
    return output


def render_rows(rows: list[dict[str, str]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root containing data/figure_index.csv.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output CSV path (defaults to data/reproduction_targets.csv).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the existing registry differs; do not write files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = args.project_root.resolve()
    output_path = args.output or project_root / "data" / "reproduction_targets.csv"
    rows = build_rows(project_root)
    rendered = render_rows(rows)
    if args.check:
        if not output_path.is_file():
            print(f"target registry is missing: {output_path}", file=sys.stderr)
            return 1
        with output_path.open("r", newline="", encoding="utf-8") as stream:
            current = stream.read()
        if current != rendered:
            print(
                "target registry is out of date; run build_reproduction_targets.py",
                file=sys.stderr,
            )
            return 1
        print(f"target registry is up to date: {len(rows)} rows")
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        stream.write(rendered)
    print(f"wrote {len(rows)} targets to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
