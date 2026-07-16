"""Build the evidence-bound invariant-bundle methods-paper draft."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "research" / "invariant_bundles" / "paper"
REGISTRY = ROOT / "research" / "invariant_bundles" / "benchmarks" / "benchmark_registry.csv"
METHOD = ROOT / "research" / "invariant_bundles" / "results" / "csv" / "method_comparison.csv"
RESOLUTION = ROOT / "research" / "invariant_bundles" / "results" / "csv" / "resolution_convergence.csv"
MANIFOLD = ROOT / "research" / "invariant_bundles" / "results" / "csv" / "manifold_convergence.csv"
FIGURE_MANIFEST = ROOT / "research" / "invariant_bundles" / "figures" / "research_figure_manifest.csv"
BASELINE = ROOT / "data" / "computed" / "reproduction_baseline_v1_summary.csv"

OUTPUTS = {
    "abstract": PAPER / "abstract.md",
    "contributions": PAPER / "contributions.md",
    "figure_plan": PAPER / "figure_plan.md",
    "tables": PAPER / "tables.md",
    "limitations": PAPER / "limitations.md",
    "manuscript": PAPER / "manuscript.md",
    "claims": PAPER / "claim_evidence_matrix.csv",
}
MANIFEST = PAPER / "paper_build_manifest.json"

METHODS = (
    "traditional_pointwise_eigendecomposition",
    "ordered_partial_real_schur_tracking",
    "qr_svd_shifted_cocycle_iteration",
)
METHOD_LABEL = {
    METHODS[0]: "Pointwise eig",
    METHODS[1]: "Partial real Schur",
    METHODS[2]: "QR/SVD cocycle",
}
HIGH_CASES = (
    "em_halo_12p40_n45",
    "em_vertical_12p66_n57",
    "se_active_geometry_member_468",
)
CASE_LABEL = {
    "em_halo_12p40_n45": "Earth–Moon L1 quasi-halo 12.40 d, N45",
    "em_vertical_12p66_n57": "Earth–Moon L1 quasi-vertical 12.66 d, N57",
    "se_active_geometry_member_468": "Sun–Earth L1 active-geometry member 468",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def fmt(value: float, precision: int = 3) -> str:
    return f"{float(value):.{precision}e}"


def evidence_header(title: str, data: Mapping[str, Any]) -> str:
    return f"""# {title}

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `{data['registry_hash']}`
- Method table SHA256: `{data['method_hash']}`
- Manifold table SHA256: `{data['manifold_hash']}`
- Figure manifest SHA256: `{data['figure_hash']}`
- Source Git commit: `{data['commit']}`

"""


def load_data() -> dict[str, Any]:
    registry = pd.read_csv(REGISTRY)
    method = pd.read_csv(METHOD)
    resolution = pd.read_csv(RESOLUTION)
    manifold = pd.read_csv(MANIFOLD)
    baseline = pd.read_csv(BASELINE)
    with FIGURE_MANIFEST.open(newline="", encoding="utf-8") as stream:
        figure_rows = list(csv.DictReader(stream))
    run_ids = set(method["run_id"])
    commits = set(method["source_git_commit"])
    if len(run_ids) != 1 or len(commits) != 1:
        raise RuntimeError("method evidence contains mixed run IDs or commits")
    if len(registry) != 15 or registry["family"].nunique() != 4:
        raise RuntimeError("benchmark registry coverage drifted")
    if len(method) != 45 or len(manifold) != 126:
        raise RuntimeError("method or manifold evidence row count drifted")
    baseline_values = {
        row.metric_id: str(row.value) for row in baseline.itertuples(index=False)
    }
    return {
        "registry": registry,
        "method": method,
        "resolution": resolution,
        "manifold": manifold,
        "baseline": baseline_values,
        "figures": figure_rows,
        "run_id": next(iter(run_ids)),
        "commit": next(iter(commits)),
        "registry_hash": sha256(REGISTRY),
        "method_hash": sha256(METHOD),
        "manifold_hash": sha256(MANIFOLD),
        "figure_hash": sha256(FIGURE_MANIFEST),
    }


def status_counts(method: pd.DataFrame) -> dict[str, Counter[str]]:
    return {
        name: Counter(
            method.loc[method["method"] == name, "research_status"].tolist()
        )
        for name in METHODS
    }


def row(method: pd.DataFrame, case_id: str, method_name: str) -> pd.Series:
    selected = method[
        (method["case_id"] == case_id) & (method["method"] == method_name)
    ]
    if len(selected) != 1:
        raise RuntimeError(f"expected one method row for {case_id}/{method_name}")
    return selected.iloc[0]


def summary_metrics(data: Mapping[str, Any]) -> dict[str, Any]:
    method = data["method"]
    manifold = data["manifold"]
    counts = status_counts(method)
    high: dict[str, dict[str, pd.Series]] = {
        case: {name: row(method, case, name) for name in METHODS}
        for case in HIGH_CASES
    }
    improvement = {
        case: float(high[case][METHODS[0]]["max_invariance_residual"])
        / float(high[case][METHODS[2]]["max_invariance_residual"])
        for case in HIGH_CASES
    }
    route = {
        "physical_schur": row(method, "route_h_member_68", METHODS[1]),
        "physical_qr": row(method, "route_h_member_68", METHODS[2]),
        "legacy_schur": row(
            method, "route_h_member_68_legacy_dg_positive", METHODS[1]
        ),
        "legacy_qr": row(
            method, "route_h_member_68_legacy_dg_positive", METHODS[2]
        ),
    }
    manifold_counts = {
        name: Counter(
            manifold.loc[manifold["method"] == name, "status"].tolist()
        )
        for name in METHODS
    }
    nominal = manifold[np.isclose(manifold["perturbation_norm"], 1.0e-7)]
    high_manifold = nominal[nominal["case_id"].isin(HIGH_CASES)]
    low_qr = nominal[
        nominal["case_id"].isin(
            (
                "em_halo_12p40_n21",
                "em_halo_12p40_n33",
                "em_vertical_12p66_n33",
                "em_vertical_12p66_n45",
            )
        )
        & (nominal["method"] == METHODS[2])
    ]
    return {
        "counts": counts,
        "high": high,
        "improvement": improvement,
        "route": route,
        "manifold_counts": manifold_counts,
        "max_jacobi": float(manifold["manifold_jacobi_drift"].max()),
        "max_initial_linear_deviation": float(
            np.max(np.abs(manifold["initial_linear_growth_ratio"] - 1.0))
        ),
        "max_perturbation_sensitivity": float(
            manifold["normalized_displacement_perturbation_sensitivity"].max()
        ),
        "high_manifold": high_manifold,
        "low_qr": low_qr,
        "total_manifold_counts": Counter(manifold["status"].tolist()),
    }


def render_abstract(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    counts = metrics["counts"]
    return evidence_header("Abstract / 摘要", data) + f"""## English

Reliable stable and unstable manifold construction around quasi-periodic
orbits requires a real invariant bundle of a phase-shifted cocycle, not an
eigenvector selected independently at each phase.  We present an auditable
numerical framework that separates a traditional pointwise-eigendecomposition
baseline from two real-subspace methods: ordered partial real-Schur tracking
and shifted QR/SVD cocycle iteration.  A frozen registry contains 15 cases from
four Earth–Moon and Sun–Earth benchmark families, including positive, negative,
boundary, low-resolution, and legacy-operator controls.  Across 45
case–method runs, pointwise eigenselection produced {counts[METHODS[0]]['accepted']}/15
accepted results, partial real Schur produced {counts[METHODS[1]]['accepted']}/15,
and QR/SVD produced {counts[METHODS[2]]['accepted']}/15.  On the high-resolution
Halo N45, Vertical N57, and Sun–Earth member-468 cases, QR/SVD reduced the
maximum bundle residual relative to the pointwise baseline by factors of
{metrics['improvement'][HIGH_CASES[0]]:.2e},
{metrics['improvement'][HIGH_CASES[1]]:.2e}, and
{metrics['improvement'][HIGH_CASES[2]]:.2e}, respectively.  A 126-row manifold
campaign retained a Jacobi-drift ceiling of {metrics['max_jacobi']:.3e} and
accepted both improved methods at the three high-resolution family anchors,
while lower-resolution full-sheet distances remained above the frozen 0.01
boundary.  A Route-H control audit further shows that the previously near-real
member-68 result belongs to a legacy seed-rotation operator whose curve-map
residual is about 1.99e-3; the physical corrected-rotation curve closes near
8.5e-13 but does not yield an accepted one-dimensional bundle.  The supported
contribution is therefore a reliable numerical framework and systematic
comparison, not a claim of new invariant-bundle theory or thesis-wide numerical
equivalence.

## 中文

拟周期轨道附近的稳定/不稳定流形必须来自满足相位平移 cocycle 方程的实不变子束，
不能把各相位独立选出的复特征向量直接投影成实方向。本文建立了一个可审计数值框架，
系统比较传统点式特征分解、ordered partial real-Schur 子空间跟踪和 shifted QR/SVD
cocycle 迭代。冻结 benchmark registry 含 4 类轨道族、15 个 case；45 个 case–method
结果中，点式基线 accepted 为 {counts[METHODS[0]]['accepted']}/15，partial real-Schur
为 {counts[METHODS[1]]['accepted']}/15，QR/SVD 为 {counts[METHODS[2]]['accepted']}/15。
在 Halo N45、Vertical N57 和 Sun–Earth member 468 上，两种实子空间方法均通过，
而点式方法失败。126 行流形实验严格保持 Jacobi 漂移门槛，并保留低分辨率全片几何
不收敛及 Route H corrected-ρ 失败结果。当前证据支持“可靠数值框架与系统比较”，
不支持“新理论”或 McCarthy 2018 全文严格数值等价复现。
"""


def render_contributions(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    return evidence_header("Contributions", data) + f"""## Supported contribution statement

> A reliable numerical framework and systematic comparison for real
> invariant-bundle and global-manifold computation on quasi-periodic orbit
> cocycles.

The evidence supports the following contributions.

1. **Cocycle-aware audit equation.** Every method is tested against
   `A(theta) E(theta) ≈ E(theta + rho) R(theta)` with stored local and aggregate
   residuals, phase principal angles, bundle dimension, reciprocal-pair error,
   runtime, and failure reason.
2. **Real one- and two-dimensional outputs.** The partial real-Schur method
   returns a one-dimensional real block only for a nearly real selected root;
   a conjugate pair is retained as a two-dimensional real invariant subspace.
3. **Independent shifted QR/SVD method.** The second improved method transports,
   Fourier-interpolates, orthonormalizes, and phase-aligns real subspaces under
   a fixed 200-iteration cap.  It accepted
   `{metrics['counts'][METHODS[2]]['accepted']}/15` cases without hiding its
   `{metrics['counts'][METHODS[2]]['fail']}/15` failures.
4. **Four-family benchmark and controls.** The registry contains 15 cases from
   four families and preserves low-resolution, complex-spectrum, boundary,
   physical corrected-rho, and legacy-DG controls.
5. **Resolution-to-manifold traceability.** Bundle convergence and full-sheet
   geometry are evaluated separately.  Halo N21/N33 and Vertical N33/N45 remain
   above the 0.01 cross-resolution sheet boundary even when their local bundle
   residual is small.
6. **Route-H operator-semantics finding.** The physical corrected-rho member-68
   curve has a recomputed map residual near
   `{float(metrics['route']['physical_schur']['source_map_residual_recomputed']):.3e}`,
   but its selected partial real-Schur block is dimension
   `{int(metrics['route']['physical_schur']['bundle_dimension'])}` with relative
   imaginary part `{float(metrics['route']['physical_schur']['relative_imaginary_part']):.3f}`.
   The accepted one-dimensional legacy control instead uses a curve-map
   residual near `{float(metrics['route']['legacy_schur']['source_map_residual_recomputed']):.3e}`.

## Claims deliberately not made

- No new invariant-bundle theorem or convergence proof is claimed.
- No two-dimensional real subspace is called a one-dimensional stable or
  unstable direction.
- No research result is written back into the reproduction validation table.
- No Route-H research figure is called a replacement for original Fig. 4.3–4.8.
- No claim of thesis-wide paper equivalence is made.
- No external citation is included until title, authors, year, and DOI or
  official link are independently verified.
"""


def render_tables(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    counts = metrics["counts"]
    lines = [evidence_header("Tables", data), "## Table 1. Method outcome counts", "", "| Method | Accepted | Boundary | Fail | Total |", "|---|---:|---:|---:|---:|"]
    for method in METHODS:
        item = counts[method]
        lines.append(
            f"| {METHOD_LABEL[method]} | {item['accepted']} | {item['boundary']} | {item['fail']} | {sum(item.values())} |"
        )
    lines += ["", f"Source: `{rel(METHOD)}` grouped by `method,research_status`.", "", "## Table 2. High-resolution anchor residuals", "", "| Case | Method | Bundle dimension | Max residual | Runtime (s) | Bundle status | Manifold status |", "|---|---|---:|---:|---:|---|---|"]
    for case in HIGH_CASES:
        for method in METHODS:
            item = metrics["high"][case][method]
            lines.append(
                f"| {CASE_LABEL[case]} | {METHOD_LABEL[method]} | {int(item['bundle_dimension'])} | {float(item['max_invariance_residual']):.3e} | {float(item['runtime_seconds']):.3f} | {item['research_status']} | {item['manifold_status']} |"
            )
    lines += ["", f"Source: `{rel(METHOD)}` filtered to the three Stage-F family anchors.", "", "## Table 3. Route-H member-68 operator control", "", "| Case/operator | Method | Source map residual | Dimension | Relative imaginary | Max bundle residual | Status |", "|---|---|---:|---:|---:|---:|---|"]
    route_items = (
        ("physical corrected-rho", "physical_schur", METHODS[1]),
        ("physical corrected-rho", "physical_qr", METHODS[2]),
        ("legacy seed-rho", "legacy_schur", METHODS[1]),
        ("legacy seed-rho", "legacy_qr", METHODS[2]),
    )
    for label, key, method in route_items:
        item = metrics["route"][key]
        lines.append(
            f"| {label} | {METHOD_LABEL[method]} | {float(item['source_map_residual_recomputed']):.3e} | {int(item['bundle_dimension'])} | {float(item['relative_imaginary_part']):.3e} | {float(item['max_invariance_residual']):.3e} | {item['research_status']} |"
        )
    lines += ["", f"Source: `{rel(METHOD)}` filtered to the two member-68 registry cases.", "", "## Table 4. Stage-F manifold audit", "", "| Metric | Value | Frozen boundary |", "|---|---:|---:|", f"| Stored rows | {len(data['manifold'])} | 126 expected |", f"| Maximum Jacobi drift | {metrics['max_jacobi']:.3e} | 1.0e-10 |", f"| Maximum initial linear-ratio deviation | {metrics['max_initial_linear_deviation']:.3e} | 5.0e-2 |", f"| Maximum perturbation sensitivity | {metrics['max_perturbation_sensitivity']:.3e} | reported, not promoted |", f"| Accepted manifold rows | {metrics['total_manifold_counts']['accepted']} | — |", f"| Failed manifold rows | {metrics['total_manifold_counts']['fail']} | failures retained |", "", f"Source: `{rel(MANIFOLD)}`.", ""]
    return "\n".join(lines)


def render_figure_plan(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    descriptions = {
        "F1": ("fig_bundle_method_summary.pdf", "Bundle residual, outcome counts, runtime/accuracy, and adjacent-phase continuity across families."),
        "F2": ("fig_resolution_convergence.pdf", "Halo and vertical residual convergence, cross-N full-sheet distance, and principal-angle convergence."),
        "F3": ("fig_route_h_rho_control.pdf", "Physical corrected-rho versus frozen legacy-DG member-68 control."),
        "F4": ("fig_manifold_method_metrics.pdf", "Direction angle, normalized displacement distance, perturbation sensitivity, and residual-to-geometry relation."),
        "F5": ("fig_phase_continuity_profiles.pdf", "Phase-resolved local residual and adjacent-phase angle at three family anchors."),
        "F6": ("fig_halo_manifold_displacement_sheets.pdf", "Normalized Halo N45 displacement sheets for pointwise eig, partial real Schur, and QR/SVD."),
    }
    lines = [evidence_header("Figure plan", data), "All figures have 320-DPI PNG previews and vector PDF versions.  Captions must preserve research/reproduction boundaries.", ""]
    for figure_id, (filename, caption) in descriptions.items():
        lines += [f"## {figure_id}", "", f"- PDF: `../figures/{filename}`", f"- Caption: {caption}", "", "```latex", "\\begin{figure}[t]", "    \\centering", f"    \\includegraphics[width=\\linewidth]{{figures/{filename}}}", f"    \\caption{{{caption} Best viewed in color.}}", f"    \\label{{fig:{figure_id.lower()}}}", "\\end{figure}", "```", ""]
    lines += [f"Manifest: `{rel(FIGURE_MANIFEST)}`.  Figure hashes are checked by `generate_research_figures.py --check`.", ""]
    return "\n".join(lines)


def render_limitations(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    return evidence_header("Limitations", data) + f"""1. **No thesis-wide numerical equivalence.** The frozen reproduction layer has
   {data['baseline']['target_rows']} engineering targets, but its evidence split
   remains {data['baseline']['evidence_accepted']} accepted,
   {data['baseline']['evidence_boundary']} boundary,
   {data['baseline']['evidence_diagnostic']} diagnostic, and
   {data['baseline']['evidence_proxy']} proxy.  Research success cannot promote
   those rows.
2. **No new theory claim.** The evaluated real-Schur and QR/SVD ideas are
   numerical subspace techniques assembled into an auditable workflow.  This
   draft contains no proof of existence, uniqueness, reducibility, or
   convergence for the underlying cocycle.
3. **Partial real-Schur backend.** The locked Windows SciPy 1.17.1 runtime raises
   `0xc06d007f` on `scipy.linalg.schur`.  The implementation therefore orders a
   selected operator eigenpair, realifies a conjugate pair when necessary, and
   verifies the real partial-Schur residual directly.  A repaired LAPACK Schur
   runtime remains an independent backend-validation task.
4. **Finite iteration and resolution.** Shifted QR/SVD stops at 200 iterations.
   Five registry cases fail at this cap.  The largest spectral resolution is
   N57, not an asymptotic limit.
5. **Route-H boundary.** The physical corrected-rho Route-H cases do not yield an
   accepted one-dimensional bundle.  The legacy member-68 one-dimensional
   positive control uses a curve-map residual near
   {float(metrics['route']['legacy_schur']['source_map_residual_recomputed']):.3e}
   and is not a physical source validation.
6. **Manifold scope.** Stage F evaluates unstable, one-dimensional bundles on
   seven cases, one fixed propagation interval, three perturbation norms, two
   signs, no event termination, and the CR3BP synodic frame.  Stable bundles,
   longer global events, and two-dimensional manifold objects are not yet
   validated.
7. **Geometry boundary.** Lower-resolution Halo and Vertical sheets remain above
   the 0.01 cross-resolution distance.  Visual similarity is not used to
   override that failure.
8. **Projection boundary.** No research result changes the frozen Chapter-4
   camera/epsilon/crop/threshold holdout, whose paper-projection status remains
   failed.
9. **Literature boundary.** External references are intentionally absent from
   this draft until complete bibliographic fields and DOI or official links are
   independently verified.
"""


def render_manuscript(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    counts = metrics["counts"]
    halo = metrics["high"][HIGH_CASES[0]]
    vertical = metrics["high"][HIGH_CASES[1]]
    sun = metrics["high"][HIGH_CASES[2]]
    return evidence_header(
        "Auditable Real Invariant-Bundle Computation for Quasi-Periodic CR3BP Tori",
        data,
    ) + rf"""## 1. Introduction

Quasi-periodic orbit manifolds are frequently seeded from eigenvectors of a
large discrete differential or from eigenvectors computed independently at
each phase.  Both shortcuts can obscure the actual object of interest: a real
subbundle transported by a phase-shifted linear cocycle.  A complex selected
eigenvector may be silently projected to its real part, adjacent phases may
jump by sign or subspace, and a direction that looks smooth at one spectral
resolution may not converge as the phase grid is refined.

This study starts only after freezing the McCarthy 2018 reproduction baseline.
The baseline contains {data['baseline']['target_rows']} engineering outputs
({data['baseline']['v0_targets']} V0 and {data['baseline']['v2_targets']} V2),
but it is explicitly not a thesis-wide strict-equivalence claim.  The research
layer therefore treats reproduction artifacts as immutable benchmark sources
and never promotes research status into the figure-validation table.

The paper evaluates three numerical routes: a deliberately retained pointwise
eigendecomposition baseline, an ordered partial real-Schur subspace method, and
a shifted QR/SVD cocycle iteration.  The contribution is an auditable framework
and systematic comparison across 15 cases and four families.  It is not a claim
of a new invariant-bundle theorem.

## 2. Problem formulation

Let an invariant curve be sampled at odd phases
`theta_i = 2*pi*i/N`.  A local state-transition matrix `A(theta_i)` maps a
perturbation at `theta_i` to `theta_i + rho`.  A real rank-`k` bundle is an
orthonormal matrix field `E(theta) in R^(6 x k)` satisfying

$$
A(\theta)E(\theta) \approx E(\theta+\rho)R(\theta),
$$

where `R(theta)` is scalar for `k=1` and a real `2 x 2` reduced map for `k=2`.
The normalized local residual is

$$
r(\theta_i)=
\frac{{\lVert A_i E_i-E_{{i+\rho}}(E_{{i+\rho}}^{{T}}A_iE_i)\rVert_F}}
     {{\max(\lVert A_iE_i\rVert_F,\epsilon_\mathrm{{mach}})}}.
$$

The audit records maximum and mean residual, adjacent-phase and cross-resolution
principal angles, selected spectrum, relative imaginary part, reciprocal-pair
error, local multiplier estimate, runtime, memory estimate, status, and failure
reason.  A rank-two real subspace is never relabelled as a rank-one direction.

## 3. Quasi-periodic orbit and cocycle model

For each registry case, the stored invariant-curve nodes are propagated for the
frozen mapping time with the CR3BP variational equations.  The terminal state
is compared with Fourier interpolation of the source curve at `theta+rho`.
Only after this map revalidation passes is the cocycle used by a method.

The collocation operator is

$$
G_N=(P_{{\theta+\rho\rightarrow\theta}}\otimes I_6)
    \operatorname{{diag}}(A_0,\ldots,A_{{N-1}}),
$$

where `P` is the odd-grid trigonometric interpolation matrix.  This operator is
useful for ordered spectral-block selection, while the reported scientific
criterion remains the pointwise cocycle equation above.

## 4. Failure modes of pointwise eigenselection

The baseline eigendecomposes each local `A_i`, selects the stable or unstable
candidate by multiplier magnitude, takes a real part, normalizes each node, and
aligns adjacent signs.  It therefore reproduces the conventional failure mode
rather than hiding it.  Across all 15 cases it obtains
{counts[METHODS[0]]['accepted']} accepted results; its high-resolution maximum
residuals are {float(halo[METHODS[0]]['max_invariance_residual']):.3e},
{float(vertical[METHODS[0]]['max_invariance_residual']):.3e}, and
{float(sun[METHODS[0]]['max_invariance_residual']):.3e} for Halo N45,
Vertical N57, and Sun–Earth member 468.

The Route-H controls expose a second failure mode.  The saved scan classified
member 68 as a near-real positive control under the seed rotation.  Direct
revalidation shows that this legacy operator has a curve-map residual of
{float(metrics['route']['legacy_schur']['source_map_residual_recomputed']):.3e}.
The physically corrected rotation closes at
{float(metrics['route']['physical_schur']['source_map_residual_recomputed']):.3e},
but its selected block is rank two with relative imaginary part
{float(metrics['route']['physical_schur']['relative_imaginary_part']):.3f}.
Thus “near-real DG eigenvalue” and “validated physical one-dimensional bundle”
are not interchangeable claims.

## 5. Proposed invariant-bundle method

The term *proposed* here refers to the evaluated numerical framework, not to a
new mathematical theorem.  The first improved route extracts a selected real
partial-Schur block from `G_N`.

```latex
\begin{{algorithm}}[t]
\caption{{Ordered partial real-Schur bundle tracking}}
\begin{{algorithmic}}[1]
\Require Local matrices $A_i$, phases $\theta_i$, rotation $\rho$, branch
\Ensure Real bases $E_i$, rank $k\in\{{1,2\}}$, residuals $r_i$
\State Assemble $G_N=(P_{{\theta+\rho\rightarrow\theta}}\otimes I)\operatorname{{diag}}(A_i)$
\State Order hyperbolic roots by distance to the real axis
\If{{the selected root is real within the frozen tolerance}}
  \State Set $k\gets1$ and form a normalized real vector
\Else
  \State Set $k\gets2$ and realify the conjugate pair with real/imaginary columns
\EndIf
\State Orthonormalize the selected block and verify $\lVert G_NQ-Q(Q^TG_NQ)\rVert_F$
\State Reshape into nodewise bases, apply local QR, and align adjacent phases
\State Compute $R_i=E_{{i+\rho}}^TA_iE_i$ and $r_i$
\end{{algorithmic}}
\end{{algorithm}}
```

The second route is independent shifted QR/SVD graph iteration.

```latex
\begin{{algorithm}}[t]
\caption{{Shifted QR/SVD cocycle iteration}}
\begin{{algorithmic}}[1]
\Require $A_i$, $\theta_i$, $\rho$, rank $k$, cap $K=200$
\Ensure Real phase-aligned bases $E_i$ and convergence history
\State Initialize each $E_i$ from the leading local right-singular subspace
\For{{$j=1,\ldots,K$}}
  \State Transport $F_i\gets A_iE_i$ and apply local QR
  \State Align frames on the shifted grid $\theta_i+\rho$
  \State Interpolate $F$ back to the base grid and apply local QR
  \State Align to the previous iterate and along phase
  \State Stop if the maximum subspace angle is at most $2\times10^{{-6}}$ degrees
\EndFor
\State Compute the cocycle residual; retain nonconvergence as a failed result
\end{{algorithmic}}
\end{{algorithm}}
```

## 6. Numerical implementation

All source integrations use DOP853 with `rtol=1e-11`, `atol=1e-13`, and fixed
maximum steps (`0.01` Earth–Moon, `0.005` Sun–Earth).  Campaign caps are 15
cases, N57, 200 QR iterations, and 1800 seconds.  Per-case cocycle checkpoints
are keyed by state-artifact hash, state key, mapping time, rotation, mass ratio,
and integration step.  The research pass threshold is `max residual <= 1e-6`;
`1e-6 < residual <= 1e-3` is a boundary unless another failure applies.  These
are research-only thresholds and do not modify reproduction gates.

The locked Windows SciPy runtime cannot execute `scipy.linalg.schur` and raises
`0xc06d007f`.  The stored implementation therefore constructs and verifies a
selected real *partial* Schur block from the ordered invariant eigenpair.  This
limitation is explicit and motivates later backend cross-validation.

## 7. Benchmark families

The registry contains five Earth–Moon quasi-halo cases, three Earth–Moon
quasi-vertical cases, five Route-H cases when the physical and legacy member-68
operators are counted separately, and two Sun–Earth L1 cases.  Halo includes
N21/N33/N45 lifts, a smaller N15 member, and the old N9 low-resolution negative
control.  Vertical includes N33/N45/N57.  Route H includes physical members 17,
32, 54, and 68 plus the legacy member-68 operator.  Sun–Earth includes accepted
active-geometry member 468 and a saved smaller-amplitude checkpoint.  No branch
is blindly extended during benchmarking.

## 8. Resolution and phase-continuity tests

The partial real-Schur method records {counts[METHODS[1]]['accepted']} accepted,
{counts[METHODS[1]]['boundary']} boundary, and
{counts[METHODS[1]]['fail']} failed cases.  QR/SVD records
{counts[METHODS[2]]['accepted']} accepted and
{counts[METHODS[2]]['fail']} failed cases.  On Halo N45 their maximum residuals
are {float(halo[METHODS[1]]['max_invariance_residual']):.3e} and
{float(halo[METHODS[2]]['max_invariance_residual']):.3e}; on Vertical N57 they
are {float(vertical[METHODS[1]]['max_invariance_residual']):.3e} and
{float(vertical[METHODS[2]]['max_invariance_residual']):.3e}; on Sun–Earth 468
they are {float(sun[METHODS[1]]['max_invariance_residual']):.3e} and
{float(sun[METHODS[2]]['max_invariance_residual']):.3e}.

Cross-resolution principal angles become small for both improved methods, but
that fact alone is insufficient.  Full-sheet distances relative to the highest
resolution remain approximately 0.0219 and 0.0150 for Halo N21/N33, and 0.0245
and 0.0195 for Vertical N33/N45.  All exceed the retained 0.01 boundary.

## 9. Global manifold experiments

Stage F uses seven cases, three methods, three full-state perturbation norms
(`5e-8`, `1e-7`, `2e-7`), two signs, and 41 time samples, for 126 stored rows.
Within each case, methods share source states, phases, propagation duration,
integrator, tolerances, coordinates, and stopping rule.  The maximum Jacobi
drift is {metrics['max_jacobi']:.3e}; the maximum initial linear-growth-ratio
deviation is {metrics['max_initial_linear_deviation']:.3e}.

At Halo N45, Vertical N57, and Sun–Earth 468, both improved methods pass the
bundle and manifold checks.  The pointwise baseline fails at every Stage-F
case because its bundle residual already fails.  At the three anchors its
direction differs from QR by roughly 7–9 degrees, while partial real Schur is
within approximately `4e-5` degrees.  This difference becomes clearer when
the displacement sheet is normalized by perturbation size: pointwise-to-QR
distance is order `1e-2`, whereas Schur-to-QR distance is `1e-7` or smaller at
the anchors.

## 10. Computational cost

For the three accepted family anchors, partial real Schur required
{float(halo[METHODS[1]]['runtime_seconds']):.3f},
{float(vertical[METHODS[1]]['runtime_seconds']):.3f}, and
{float(sun[METHODS[1]]['runtime_seconds']):.3f} seconds; QR/SVD required
{float(halo[METHODS[2]]['runtime_seconds']):.3f},
{float(vertical[METHODS[2]]['runtime_seconds']):.3f}, and
{float(sun[METHODS[2]]['runtime_seconds']):.3f} seconds.  Failed Route-H QR
runs consume several seconds because they reach the 200-iteration cap.  Runtime
is therefore coupled to convergence status, and failed rows must be included in
any accuracy–cost comparison.

## 11. Discussion

Three conclusions are supported.  First, low pointwise eigenpair residual does
not imply low cocycle residual: the pointwise method solves the wrong local
problem.  Second, real subspace handling matters independently of numerical
accuracy; complex pairs must remain rank two.  Third, a small bundle residual
does not guarantee converged global-sheet geometry.  The N21/N33 and N33/N45
full-sheet failures demonstrate why source, bundle, and manifold gates must be
reported separately.

The Route-H result is especially instructive.  Correcting the curve rotation
improves curve closure by about nine orders of magnitude relative to the legacy
operator, yet removes the accepted one-dimensional Schur control.  This is not
a reason to restore the old rotation; it is evidence that operator semantics
must be part of benchmark provenance.

## 12. Limitations

This draft has no external literature comparison, theoretical convergence
proof, stable-bundle manifold campaign, two-dimensional manifold object, or
long-event global propagation.  The Schur backend is a verified partial block,
not an independent LAPACK Schur run.  Route H remains a failed physical bundle
family under the tested methods.  Lower-resolution manifold geometry remains
outside the 0.01 boundary.  The Chapter-4 projection holdout remains failed and
is untouched.

## 13. Conclusion

The frozen evidence supports an auditable real invariant-bundle framework and
systematic comparison.  Across multiple Earth–Moon and Sun–Earth families,
partial real-Schur and shifted QR/SVD methods repeatedly reduce cocycle
residuals by many orders of magnitude relative to pointwise eigenselection and
produce consistent high-resolution displacement sheets.  The same workflow
also exposes genuine negative results: Route-H physical corrected-rho cases do
not yield an accepted one-dimensional bundle, and low-resolution sheets do not
clear the retained convergence boundary.  These failures define the current
scope of the contribution and prevent overclaiming.

## Evidence map

- Registry and provenance: `{rel(REGISTRY)}`
- Method comparison: `{rel(METHOD)}`
- Resolution comparison: `{rel(RESOLUTION)}`
- Manifold comparison: `{rel(MANIFOLD)}`
- Figures and hashes: `{rel(FIGURE_MANIFEST)}`
- Reproduction baseline: `{rel(BASELINE)}`
- Detailed tables: `tables.md`
- Claim-by-claim traceability: `claim_evidence_matrix.csv`
"""


def render_claims(data: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    rows = [
        ("C1", "Introduction", "The reproduction baseline is frozen and is not a thesis-wide strict-equivalence claim.", rel(BASELINE), "target_rows and evidence-class rows", "supported", "Research cannot promote reproduction."),
        ("C2", "Benchmarks", "The registry contains 15 cases from four families.", rel(REGISTRY), "row count; family nunique", "supported", "Physical and legacy Route-H member 68 are separate."),
        ("C3", "Results", "Pointwise eig has 0/15 accepted cases; Schur has 7/15; QR/SVD has 10/15.", rel(METHOD), "group by method,research_status", "supported", "Research-only status."),
        ("C4", "Results", "QR/SVD has repeatable residual advantage on Halo, Vertical, and Sun-Earth anchors.", rel(METHOD), "three HIGH_CASES max_invariance_residual", "supported", "Does not imply thesis projection equivalence."),
        ("C5", "Resolution", "Local bundle convergence does not by itself clear full-sheet convergence.", rel(MANIFOLD), "cross_resolution_normalized_3d_distance", "supported", "0.01 boundary retained."),
        ("C6", "Route H", "The legacy member-68 positive control and physical corrected-rho case are different operators.", rel(METHOD), "source map residual, rho case IDs, dimension", "supported", "Legacy control is not a physical-source acceptance."),
        ("C7", "Manifolds", "Both improved methods pass at Halo N45, Vertical N57, and Sun-Earth 468.", rel(MANIFOLD), "nominal epsilon; both signs; status", "supported", "Only unstable 1-D manifolds tested."),
        ("C8", "Manifolds", f"Maximum stored Jacobi drift is {metrics['max_jacobi']:.3e}.", rel(MANIFOLD), "max manifold_jacobi_drift", "supported", "Finite tested campaign only."),
        ("C9", "Contribution", "The work is a reliable numerical framework and systematic comparison.", rel(METHOD) + ";" + rel(MANIFOLD), "multi-family accepted and failed rows", "supported", "No new theorem claim."),
        ("C10", "Boundary", "The work establishes McCarthy 2018 paper-equivalence.", rel(BASELINE), "frozen boundary text", "rejected", "Explicitly unsupported."),
    ]
    output = []
    fields = (
        "claim_id",
        "section",
        "claim",
        "evidence_artifact",
        "filter_or_metric",
        "status",
        "boundary",
    )
    from io import StringIO

    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(fields)
    writer.writerows(rows)
    return stream.getvalue()


def render_all(data: Mapping[str, Any]) -> dict[Path, bytes]:
    metrics = summary_metrics(data)
    rendered = {
        OUTPUTS["abstract"]: render_abstract(data, metrics),
        OUTPUTS["contributions"]: render_contributions(data, metrics),
        OUTPUTS["figure_plan"]: render_figure_plan(data, metrics),
        OUTPUTS["tables"]: render_tables(data, metrics),
        OUTPUTS["limitations"]: render_limitations(data, metrics),
        OUTPUTS["manuscript"]: render_manuscript(data, metrics),
        OUTPUTS["claims"]: render_claims(data, metrics),
    }
    return {path: content.encode("utf-8") for path, content in rendered.items()}


def manifest_bytes(data: Mapping[str, Any], rendered: Mapping[Path, bytes]) -> bytes:
    payload = {
        "schema_version": "invariant_bundle_paper_build_v1",
        "source_git_commit": data["commit"],
        "bundle_run_id": data["run_id"],
        "inputs": {
            rel(path): sha256(path)
            for path in (REGISTRY, METHOD, RESOLUTION, MANIFOLD, FIGURE_MANIFEST, BASELINE)
        },
        "outputs": {
            rel(path): hashlib.sha256(content).hexdigest().upper()
            for path, content in rendered.items()
        },
        "citation_status": "pending_verified_external_literature",
        "claim_scope": "reliable_numerical_framework_and_systematic_comparison",
    }
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build(*, check: bool) -> None:
    data = load_data()
    rendered = render_all(data)
    manifest = manifest_bytes(data, rendered)
    if check:
        for path, expected in rendered.items():
            if path.suffix == ".md" and any(
                byte in expected
                for byte in (b"\x07", b"\x08", b"\x09", b"\x0b", b"\x0c", b"\x0d")
            ):
                raise RuntimeError(f"paper artifact contains escaped control characters: {rel(path)}")
            if not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"paper artifact drifted: {rel(path)}")
        if not MANIFEST.is_file() or MANIFEST.read_bytes() != manifest:
            raise RuntimeError(f"paper manifest drifted: {rel(MANIFEST)}")
        print("invariant-bundle paper CHECK PASS files=8 claims=10")
        return
    PAPER.mkdir(parents=True, exist_ok=True)
    for path, content in rendered.items():
        path.write_bytes(content)
    MANIFEST.write_bytes(manifest)
    print("invariant-bundle paper WRITE PASS files=8 claims=10")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
