"""Build the first Chapter 4 DG/manifold audit from Route H quasi-DRO data.

This script does not replace the Chapter 4 thesis-scale figures directly.  It
checks whether the accepted high-amplitude fixed-mapping quasi-DRO corrections
from Route H can feed McCarthy's discrete-curve DG layer and a local unstable
manifold propagation without using proxy source curves.
"""

from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path
from typing import Any

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
SCRIPTS = PROJECT_ROOT / "scripts"
for candidate in (SRC, SCRIPTS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import run_chapter3_integrated_breakthrough as campaign
from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import _member_from_correction
from qp_orbits.cr3bp import jacobi_constant
from qp_orbits.torus_stability import (
    _corrected_curve_manifold_from_dg,
    corrected_curve_dg,
    real_hyperbolic_eigen_index,
)

DEFAULT_CACHE = (
    PROJECT_ROOT
    / "data"
    / "computed"
    / "cache"
    / "fixed_mapping_dro_v1_079947170b953a50.pkl"
)
ROUTE_H_AUDIT = PROJECT_ROOT / "data" / "computed" / "chapter3_fixed_mapping_cache_audit.csv"
DG_OUTPUT = PROJECT_ROOT / "data" / "computed" / "chapter4_route_h_quasi_dro_dg.csv"
MANIFOLD_OUTPUT = (
    PROJECT_ROOT / "data" / "computed" / "chapter4_route_h_quasi_dro_manifold_probe.csv"
)
DOC_OUTPUT = PROJECT_ROOT / "docs" / "chapter4_route_h_quasi_dro_dg_manifold_audit.md"
FIGURE_PNG_OUTPUT = PROJECT_ROOT / "outputs" / "figures_png" / "fig_4_route_h.png"
FIGURE_PDF_OUTPUT = PROJECT_ROOT / "outputs" / "figures_pdf" / "fig_4_route_h.pdf"

DG_FIELDS = (
    "member_index",
    "max_abs_z_km",
    "rho_rad",
    "mapping_time_days",
    "curve_samples",
    "map_residual_norm",
    "curve_jacobi_span",
    "dg_dimension",
    "determinant",
    "determinant_error_from_one",
    "stability_index",
    "max_multiplier",
    "min_multiplier",
    "real_unstable_index",
    "real_unstable_multiplier",
    "real_unstable_eigenvalue_real",
    "real_unstable_eigenvalue_imag",
    "real_unstable_relative_imaginary",
    "real_stable_index",
    "real_stable_multiplier",
    "real_stable_eigenvalue_real",
    "real_stable_eigenvalue_imag",
    "real_stable_relative_imaginary",
    "real_pair_reciprocity_error",
    "real_pair_complex_reciprocity_error",
    "unit_multiplier_count",
    "dg_status",
)

MANIFOLD_FIELDS = (
    "member_index",
    "branch",
    "perturbation_sign",
    "perturbation_scale",
    "duration_periods",
    "duration_nd",
    "duration_days",
    "time_samples",
    "curve_samples",
    "selected_eigenvalue",
    "selected_eigenvalue_abs",
    "initial_mean_separation",
    "final_mean_separation",
    "mean_state_growth",
    "expected_growth",
    "growth_ratio",
    "jacobi_drift_max",
    "terminal_x_min",
    "terminal_x_max",
    "terminal_y_min",
    "terminal_y_max",
    "terminal_z_min",
    "terminal_z_max",
    "manifold_status",
)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if np.isfinite(number):
            return f"{number:.16g}"
        return str(number)
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, complex):
        return f"{value.real:.16g}{value.imag:+.16g}j"
    return str(value)


def _load_cache(path: Path) -> tuple[Any, ...]:
    with path.open("rb") as stream:
        cached = pickle.load(stream)
    if not isinstance(cached, tuple):
        raise RuntimeError(f"fixed-mapping cache did not contain a tuple: {path}")
    return cached


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() == "true"


def _accepted_route_h_indices(path: Path, *, min_z_km: float) -> list[int]:
    if not path.exists():
        raise RuntimeError(f"missing Route H audit CSV: {path}")
    indices: list[int] = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if not _truthy(row.get("strict_acceptance")):
                continue
            if float(row["max_abs_z_km"]) < min_z_km:
                continue
            indices.append(int(row["member_index"]))
    if not indices:
        raise RuntimeError(f"Route H audit has no strict accepted members above {min_z_km:g} km")
    return indices


def _representative_indices(indices: list[int], count: int) -> list[int]:
    if count >= len(indices):
        return list(indices)
    if count == 1:
        return [indices[-1]]
    positions = np.linspace(0, len(indices) - 1, count)
    selected = [indices[int(round(position))] for position in positions]
    return list(dict.fromkeys(selected))


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _fmt(row.get(field, "")) for field in fields})


def _dg_row(member_index: int, correction: Any, max_step: float) -> tuple[dict[str, Any], Any, int, int]:
    system = SYSTEMS["earth_moon"]
    member = _member_from_correction(member_index, correction, system)
    dg = corrected_curve_dg(correction, max_step=max_step)
    unstable_index = real_hyperbolic_eigen_index(dg, branch="unstable")
    stable_index = real_hyperbolic_eigen_index(dg, branch="stable")
    unstable_eigenvalue = complex(dg.eigenvalues[unstable_index])
    stable_eigenvalue = complex(dg.eigenvalues[stable_index])
    unstable = float(abs(unstable_eigenvalue))
    stable = float(abs(stable_eigenvalue))
    row = {
        "member_index": member_index,
        "max_abs_z_km": member.max_abs_z_km,
        "rho_rad": member.rotation_angle_rad,
        "mapping_time_days": member.mapping_time_days,
        "curve_samples": member.states.shape[0],
        "map_residual_norm": member.map_residual_norm,
        "curve_jacobi_span": member.curve_jacobi_span,
        "dg_dimension": dg.map_jacobian.shape[0],
        "determinant": dg.determinant,
        "determinant_error_from_one": abs(dg.determinant - 1.0),
        "stability_index": dg.stability_index,
        "max_multiplier": dg.max_multiplier,
        "min_multiplier": dg.min_multiplier,
        "real_unstable_index": unstable_index,
        "real_unstable_multiplier": unstable,
        "real_unstable_eigenvalue_real": unstable_eigenvalue.real,
        "real_unstable_eigenvalue_imag": unstable_eigenvalue.imag,
        "real_unstable_relative_imaginary": abs(unstable_eigenvalue.imag) / unstable,
        "real_stable_index": stable_index,
        "real_stable_multiplier": stable,
        "real_stable_eigenvalue_real": stable_eigenvalue.real,
        "real_stable_eigenvalue_imag": stable_eigenvalue.imag,
        "real_stable_relative_imaginary": abs(stable_eigenvalue.imag) / stable,
        "real_pair_reciprocity_error": abs(unstable * stable - 1.0),
        "real_pair_complex_reciprocity_error": abs(
            unstable_eigenvalue * stable_eigenvalue - 1.0
        ),
        "unit_multiplier_count": dg.unit_multiplier_count,
        "dg_status": "route_h accepted source converted to discrete-curve DG",
    }
    return row, dg, unstable_index, stable_index


def _manifold_row(
    *,
    member_index: int,
    dg: Any,
    eigen_index: int,
    duration_periods: float,
    perturbation_scale: float,
    perturbation_sign: float,
    time_samples: int,
    max_step: float,
) -> dict[str, Any]:
    system = SYSTEMS["earth_moon"]
    sheet = _corrected_curve_manifold_from_dg(
        system.mu,
        dg=dg,
        branch="unstable",
        eigen_index=eigen_index,
        duration_periods=duration_periods,
        perturbation_scale=perturbation_scale,
        perturbation_sign=perturbation_sign,
        time_samples=time_samples,
        max_step=max_step,
    )
    state_separation = sheet.state_separation_norms
    initial_mean = float(np.mean(state_separation[0]))
    final_mean = float(np.mean(state_separation[-1]))
    mean_growth = final_mean / initial_mean if initial_mean > 0.0 else float("nan")
    expected_growth = float(abs(sheet.eigenvalue) ** duration_periods)
    growth_ratio = mean_growth / expected_growth if expected_growth > 0.0 else float("nan")
    jacobi_values = jacobi_constant(sheet.manifold_states.reshape(-1, 6), system.mu).reshape(
        sheet.manifold_states.shape[:2]
    )
    jacobi_drift = float(np.max(np.abs(jacobi_values - jacobi_values[0:1, :])))
    terminal = sheet.surface[-1]
    duration_nd = float(abs(sheet.times[-1] - sheet.times[0]))
    return {
        "member_index": member_index,
        "branch": "unstable",
        "perturbation_sign": perturbation_sign,
        "perturbation_scale": perturbation_scale,
        "duration_periods": duration_periods,
        "duration_nd": duration_nd,
        "duration_days": duration_nd * (system.time_unit_days or 1.0),
        "time_samples": sheet.times.size,
        "curve_samples": sheet.surface.shape[1],
        "selected_eigenvalue": sheet.eigenvalue,
        "selected_eigenvalue_abs": abs(sheet.eigenvalue),
        "initial_mean_separation": initial_mean,
        "final_mean_separation": final_mean,
        "mean_state_growth": mean_growth,
        "expected_growth": expected_growth,
        "growth_ratio": growth_ratio,
        "jacobi_drift_max": jacobi_drift,
        "terminal_x_min": float(np.min(terminal[:, 0])),
        "terminal_x_max": float(np.max(terminal[:, 0])),
        "terminal_y_min": float(np.min(terminal[:, 1])),
        "terminal_y_max": float(np.max(terminal[:, 1])),
        "terminal_z_min": float(np.min(terminal[:, 2])),
        "terminal_z_max": float(np.max(terminal[:, 2])),
        "manifold_status": "local Route H unstable manifold probe; not thesis-scale global sheet",
    }


def _write_doc(
    *,
    selected_indices: list[int],
    accepted_indices: list[int],
    dg_rows: list[dict[str, Any]],
    manifold_rows: list[dict[str, Any]],
    max_step: float,
) -> None:
    best = max(dg_rows, key=lambda row: float(row["max_abs_z_km"])) if dg_rows else None
    worst_det = max((float(row["determinant_error_from_one"]) for row in dg_rows), default=float("nan"))
    worst_recip = max((float(row["real_pair_reciprocity_error"]) for row in dg_rows), default=float("nan"))
    worst_jacobi = max((float(row["jacobi_drift_max"]) for row in manifold_rows), default=float("nan"))
    dg_lines = "\n".join(
        f"- member `{row['member_index']}`: z `{float(row['max_abs_z_km']):.12g}` km, "
        f"DG dimension `{row['dg_dimension']}`, max multiplier `{float(row['max_multiplier']):.6g}`, "
        f"det error `{float(row['determinant_error_from_one']):.3e}`"
        for row in dg_rows
    )
    manifold_lines = "\n".join(
        f"- member `{row['member_index']}`: duration `{float(row['duration_periods']):.3g}` maps, "
        f"Jacobi drift `{float(row['jacobi_drift_max']):.3e}`, "
        f"growth ratio `{float(row['growth_ratio']):.6g}`"
        for row in manifold_rows
    ) or "- manifold probe skipped"
    DOC_OUTPUT.write_text(
        f"""# Chapter 4 Route H Quasi-DRO DG/Manifold Audit

## Scope

This audit uses the strict accepted Route H fixed-mapping quasi-DRO corrections
from `data/computed/chapter3_fixed_mapping_cache_audit.csv` as Chapter 4 source
data.  It computes McCarthy-style discrete-curve DG spectra and a short local
unstable manifold probe directly from the cached correction objects.

It is an upstream Chapter 4 source-layer audit.  It does not yet replace the
existing Fig. 4.3-4.8 proxy backgrounds, because those figures currently target
L1 quasi-halo and quasi-vertical manifolds, while Route H is the Chapter 3
quasi-DRO family.

The strict real-hyperbolic gate is applied before a manifold probe is allowed.
The companion scan in `data/computed/chapter4_real_hyperbolic_scan.csv` found
only member `68` passing both stable and unstable relative-imaginary tolerances
(`1e-6`) among the 31 accepted Route H members above 10,500 km.  The other 30
members have Fourier-shifted complex hyperbolic pairs and remain boundary
evidence; their magnitude-only reciprocal pairs are not promoted to real
manifold directions.

## Inputs And Parameters

- Accepted Route H members above 10,500 km: `{len(accepted_indices)}`
- Strict real-hyperbolic member(s) audited here: `{selected_indices}`
- DG / manifold integration max step: `{max_step}`

## DG Outcome

- DG rows written: `{len(dg_rows)}`
- Best audited Route H z amplitude: `{best['max_abs_z_km'] if best else 'N/A'}` km
- Worst determinant error from one: `{worst_det:.3e}`
- Worst real stable/unstable reciprocity error: `{worst_recip:.3e}`

{dg_lines}

## Local Manifold Probe

- Manifold probe rows written: `{len(manifold_rows)}`
- Worst probe Jacobi drift: `{worst_jacobi:.3e}`

{manifold_lines}

## Outputs

- `{DG_OUTPUT.relative_to(PROJECT_ROOT)}`
- `{MANIFOLD_OUTPUT.relative_to(PROJECT_ROOT)}`
- `{FIGURE_PNG_OUTPUT.relative_to(PROJECT_ROOT)}`
- `{FIGURE_PDF_OUTPUT.relative_to(PROJECT_ROOT)}`

## Decision

Member `68` passes the strict Route H source/DG compatibility and local
manifold-probe gates without a proxy source curve.  This is not a three-member
cross-amplitude promotion: the companion scan passes only `1/31`, so the Route H
branch remains a boundary/source-layer result for the original Chapter 4
manifold claim.  The regenerated source-layer figure is available as
`fig_4_route_h` after running `figures/fig_4_route_h_quasi_dro.py`.

Separately, the original L1 quasi-halo/quasi-vertical Fig. 4.3-4.8 audits have
eight of eight requested snapshot rows accepted with proxy-free propagation.
Those rows remain numerical source-layer replacements with an explicit
pointwise paper-panel digitization boundary; they do not imply that the Route H
three-member gate has passed.
""",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--route-h-audit", type=Path, default=ROUTE_H_AUDIT)
    parser.add_argument("--min-z-km", type=float, default=campaign.TARGET_MIN_KM)
    parser.add_argument("--representatives", type=int, default=3)
    parser.add_argument("--member-index", action="append", type=int, default=[])
    parser.add_argument("--max-step", type=float, default=0.02)
    parser.add_argument("--skip-manifold", action="store_true")
    parser.add_argument("--duration-periods", type=float, default=0.1)
    parser.add_argument("--time-samples", type=int, default=12)
    parser.add_argument("--perturbation-scale", type=float, default=1.0e-7)
    args = parser.parse_args()

    if args.representatives <= 0:
        raise SystemExit("--representatives must be positive")
    if args.max_step <= 0.0:
        raise SystemExit("--max-step must be positive")
    if args.duration_periods <= 0.0:
        raise SystemExit("--duration-periods must be positive")
    if args.time_samples < 2:
        raise SystemExit("--time-samples must be at least 2")
    if not args.cache.exists():
        raise SystemExit(f"missing fixed-mapping cache: {args.cache}")

    accepted_indices = _accepted_route_h_indices(args.route_h_audit, min_z_km=args.min_z_km)
    selected_indices = (
        sorted(dict.fromkeys(args.member_index))
        if args.member_index
        else _representative_indices(accepted_indices, args.representatives)
    )
    missing = [index for index in selected_indices if index not in accepted_indices]
    if missing:
        raise SystemExit(f"selected members are not strict Route H accepted rows: {missing}")

    cached = _load_cache(args.cache)
    dg_rows: list[dict[str, Any]] = []
    manifold_rows: list[dict[str, Any]] = []
    for index in selected_indices:
        print(f"route_h_member_{index}: computing DG", flush=True)
        row, dg, unstable_index, _ = _dg_row(index, cached[index], args.max_step)
        dg_rows.append(row)
        if not args.skip_manifold:
            print(f"route_h_member_{index}: propagating local unstable manifold probe", flush=True)
            manifold_rows.append(
                _manifold_row(
                    member_index=index,
                    dg=dg,
                    eigen_index=unstable_index,
                    duration_periods=args.duration_periods,
                    perturbation_scale=args.perturbation_scale,
                    perturbation_sign=1.0,
                    time_samples=args.time_samples,
                    max_step=args.max_step,
                )
            )

    _write_csv(DG_OUTPUT, DG_FIELDS, dg_rows)
    _write_csv(MANIFOLD_OUTPUT, MANIFOLD_FIELDS, manifold_rows)
    _write_doc(
        selected_indices=selected_indices,
        accepted_indices=accepted_indices,
        dg_rows=dg_rows,
        manifold_rows=manifold_rows,
        max_step=args.max_step,
    )
    print(f"wrote {DG_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {MANIFOLD_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)
    print(f"wrote {DOC_OUTPUT.relative_to(PROJECT_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
