"""Build and validate the bilingual invariant-bundle submission-candidate package."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Iterable
import zipfile
from xml.etree import ElementTree

from qp_orbits.artifact_fingerprints import fingerprint_fields, fingerprint_matches


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "invariant_bundles"
SC = RESEARCH / "submission_candidate"
PACKAGE = SC / "package"
CONFIG = SC / "configs" / "submission_candidate_package.json"
RESULTS = SC / "results"
BASE_ZH = RESEARCH / "paper_release" / "manuscript_zh.md"
BASE_EN = RESEARCH / "paper" / "manuscript.md"
BASELINE = ROOT / "data" / "computed" / "reproduction_baseline_v1_summary.csv"
HOLDOUT = (
    ROOT
    / "data"
    / "computed"
    / "chapter4_fig43_fig46_projection_holdout_audit.csv"
)
FIGURE_AUDIT = (
    ROOT
    / "reports"
    / "adviser_figure_correctness_audit"
    / "adviser_figure_correctness_audit.csv"
)
DOCX_BUILDER = ROOT / "scripts" / "build_submission_candidate_docx.js"

SUMMARY_PATHS = {
    "h2_bundle": RESULTS / "stable_bundles" / "stable_bundle_summary.json",
    "h2_manifold": RESULTS / "stable_manifolds" / "stable_manifold_summary.json",
    "h3": RESULTS / "route_h_2d_manifolds" / "route_h_2d_summary.json",
    "h4": RESULTS / "long_propagation" / "long_propagation_summary.json",
    "h5": RESULTS / "sun_earth_expansion" / "sun_earth_expansion_summary.json",
}

CLAIM_FIELDS = (
    "claim_id",
    "claim_text_zh",
    "claim_text_en",
    "evidence_scope",
    "evidence_paths",
    "acceptance_rule",
    "observed",
    "status",
    "authority_boundary",
    "adviser_decision_use",
)
HASH_FIELDS = (
    "artifact_role",
    "path_root",
    "path",
    "hash_mode",
    "bytes",
    "sha256",
)


def rel(path: Path) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def csv_text(rows: Iterable[dict[str, Any]], fields: Iterable[str]) -> str:
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def count(rows: Iterable[dict[str, str]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(row[field] for row in rows).items()))


def fmt_e(value: float) -> str:
    return f"{value:.3e}"


def require_replace(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"required manuscript anchor drifted: {old[:80]!r}")
    return text.replace(old, new, 1)


def collect_evidence() -> dict[str, Any]:
    config = read_json(CONFIG)
    baseline = {row["metric_id"]: row["value"] for row in read_csv(BASELINE)}
    if baseline.get("target_rows") != "54":
        raise RuntimeError("frozen baseline target_rows is not 54")
    if baseline.get("v0_targets") != "13" or baseline.get("v2_targets") != "41":
        raise RuntimeError("frozen baseline tier counts drifted")

    holdout = read_csv(HOLDOUT)
    if len(holdout) != 4 or any(
        row["paper_projection_acceptance"] != "fail"
        or row["paper_3d_equivalence"] != "false"
        for row in holdout
    ):
        raise RuntimeError("Chapter 4 frozen 0/4 authority boundary drifted")

    summaries = {key: read_json(path) for key, path in SUMMARY_PATHS.items()}
    expected_gates = {
        "h2_bundle": ("h2_gate_status", "pass"),
        "h2_manifold": ("h2_stable_manifold_gate_status", "pass"),
        "h3": ("h3_gate_status", "pass"),
        "h4": ("h4_gate_status", "pass"),
        "h5": ("h5_gate_status", "pass"),
    }
    for key, (field, expected) in expected_gates.items():
        if summaries[key].get(field) != expected:
            raise RuntimeError(f"{key} gate is not {expected}")

    h2_bundle_rows = read_csv(
        RESULTS / "stable_bundles" / "stable_bundle_comparison.csv"
    )
    h2_manifold_rows = read_csv(
        RESULTS / "stable_manifolds" / "stable_manifold_convergence.csv"
    )
    h3_diag = read_csv(
        RESULTS
        / "route_h_2d_manifolds"
        / "route_h_2d_subspace_diagnostics.csv"
    )
    h3_manifold = read_csv(
        RESULTS
        / "route_h_2d_manifolds"
        / "route_h_2d_manifold_convergence.csv"
    )
    h3_attempts = read_csv(
        RESULTS / "route_h_2d_manifolds" / "route_h_2d_method_attempts.csv"
    )
    h4_rows = read_csv(
        RESULTS / "long_propagation" / "long_propagation_events.csv"
    )
    h5_sources = read_csv(
        RESULTS / "sun_earth_expansion" / "source_validation.csv"
    )
    h5_benchmarks = read_csv(
        RESULTS / "sun_earth_expansion" / "benchmark_comparison.csv"
    )
    h5_manifolds = read_csv(
        RESULTS / "sun_earth_expansion" / "manifold_validation.csv"
    )

    figure_counts: dict[str, int] = {}
    if FIGURE_AUDIT.is_file():
        figure_counts = count(read_csv(FIGURE_AUDIT), "audit_class")

    return {
        "config": config,
        "baseline": baseline,
        "holdout": holdout,
        "summaries": summaries,
        "h2_bundle_rows": h2_bundle_rows,
        "h2_manifold_rows": h2_manifold_rows,
        "h3_diag": h3_diag,
        "h3_manifold": h3_manifold,
        "h3_attempts": h3_attempts,
        "h4_rows": h4_rows,
        "h5_sources": h5_sources,
        "h5_benchmarks": h5_benchmarks,
        "h5_manifolds": h5_manifolds,
        "figure_counts": figure_counts,
    }


def stage_h_table_zh(e: dict[str, Any]) -> str:
    h2b = e["summaries"]["h2_bundle"]
    h2m = e["summaries"]["h2_manifold"]
    h3 = e["summaries"]["h3"]
    h4 = e["summaries"]["h4"]
    h5 = e["summaries"]["h5"]
    return f"""
## 12. Stage H：稳定子束、二维流形与长传播扩展

旧稿明确列出的四项实证缺口已按预注册上限执行；这里的“完成”是指案例、配置、失败和边界均已留下可复核证据，不等于所有数值行均 accepted。Stage H 的注册表、配置、锁、CSV、NPZ、Markdown、环境记录和 SHA256 均位于 `research/invariant_bundles/submission_candidate/`。研究结果不写回复现权威表。

| 子阶段 | 预注册范围 | 观测结果 | Gate |
|---|---|---|---|
| H2 稳定子束 | 3 案例 × 3 方法 | {h2b['method_rows']} 行；改进方法 accepted={h2b['accepted_improved_rows']}，点式方法 fail=3 | `{h2b['h2_gate_status']}` |
| H2 稳定流形 | 3 案例 × 3 方法 × 3 扰动 × 2 符号 | {h2m['rows']} 行；改进方法 accepted={h2m['accepted_improved_rows']}，失败行保留 | `{h2m['h2_stable_manifold_gate_status']}` |
| H3 Route H 二维对象 | 2 案例、8 个角向种子 | {h3['diagnostic_rows']} 相位诊断、{h3['manifold_rows']} 流形行；Schur accepted={h3['accepted_schur_manifold_rows']} | `{h3['h3_gate_status']}` |
| H4 三周期传播 | 3 案例 × 2 方法 × 2 符号 | {h4['event_rows']} 结果行：accepted=8、物理边界=4；轨迹事件={h4['trajectory_rows']} | `{h4['h4_gate_status']}` |
| H5 Sun–Earth 扩展 | 3 个不同本地源 × 3 方法 | {h5['benchmark_rows']} benchmark 行；改进方法 boundary=6、点式 fail=3 | `{h5['h5_gate_status']}` |

### 12.1 三个稳定子束与稳定流形 benchmark

Halo N45、Vertical N57 与 Sun–Earth member 468 均按稳定分支、反向传播重新验收。两种改进方法在三个案例上形成 6 行 accepted 稳定一维子束；点式 eig 的 3 行最大不变性残差仍约为 1e-1，并保留为 fail。随后 54 行稳定流形传播覆盖三种扰动幅值和两个符号；改进方法 36 行通过，点式方法 18 行因上游 bundle 失败而保留。由此可以把旧稿只验证“不稳定一维分支”的限制收窄为：稳定分支已在三个代表案例、一个映射周期和声明扰动范围内通过；这仍不是全轨道族或高保真星历验证。

### 12.2 Route H 二维实子空间流形

member 68 与 member 32 的物理 corrected-rho 算子仍是实二维共轭块，绝不重命名为一维方向。原始方程残差最大为 `{fmt_e(max(float(row['raw_equation_residual']) for row in e['h3_diag']))}`，gauge-consistent 子空间残差最大为 `{fmt_e(max(float(row['gauge_consistent_subspace_residual']) for row in e['h3_diag']))}`。在 real-Schur 实化后，两案例各产生 2 个扰动幅值对应的 accepted 二维流形对象，共 4 行；所有对象保持初始片秩 2。冻结 Stage E 的归一化帧残差和一维 fail 状态同时保留，说明 H3 解决的是表示与二维几何对象，而不是事后改写旧的一维验收。

QR/SVD 路线按 local-SVD、Schur seed 和确定性随机 seed 三种初始化，每种至 500 次迭代；两案例均留下有界失败证据，没有生成可接受对象，也没有降为一维。这一结果支持“Schur 二维对象在当前实现中可构造”，不支持“所有二维迭代算法均已收敛”。

### 12.3 三周期传播与物理半径边界

H4 对三个稳定分支固定传播 3 个映射周期，局部、全局与远场阈值只记录首次越界时刻，不终止积分。12 个方法/符号结果中 8 行 accepted、4 行 boundary；每个案例至少有一行无物理碰撞的 accepted 结果。4 个接近次天体的初始尝试触发且仅触发一次收紧积分重试，最终选中轨迹最大 Jacobi 漂移为 `{fmt_e(float(h4['maximum_selected_jacobi_drift']))}`。Halo 正号和 Vertical 负号的两种方法进入采样月球物理半径，故保留为物理 boundary，而不是删除或误报为数值失败。

### 12.4 三个新增 Sun–Earth 本地源 benchmark

H5 使用 active-event-step、sharpness-stage-4 与 energy-frontier 三个不同本地状态文件/数组，它们均不在冻结 Stage-C 注册表中。三源重算映射残差依次为 {', '.join(fmt_e(float(row['recomputed_map_residual'])) for row in e['h5_sources'])}，均通过各自源上限。Schur/QR 的 6 行改进结果约为 4.3e-5 至 4.8e-5，依冻结研究阈值只能标为 boundary；点式方法 3 行 fail。对应 18 行一周期流形中，改进方法 12 行 boundary、点式 6 行诊断性 fail。

“新增独立源”仅表示三套不同的本地源工件、状态数组和元数据指纹；不表示外部独立求解器、独立机构数据或第三方实验验证。所有 H5 行都携带 `source_authority_boundary=true`，因此不能被摘要压缩成“3 个 Sun–Earth 案例通过”。
""".strip()


def stage_h_table_en(e: dict[str, Any]) -> str:
    h2b = e["summaries"]["h2_bundle"]
    h2m = e["summaries"]["h2_manifold"]
    h3 = e["summaries"]["h3"]
    h4 = e["summaries"]["h4"]
    h5 = e["summaries"]["h5"]
    source_residuals = ", ".join(
        fmt_e(float(row["recomputed_map_residual"])) for row in e["h5_sources"]
    )
    return f"""
## 11. Preregistered Stage-H extensions

The four empirical gaps named in the reviewed Chinese draft were executed under preregistered case, iteration, retry, and wall-time caps. Completion here means that accepted, boundary, and failed outcomes are all preserved with CSV, NPZ, Markdown, configuration, environment, and SHA256 evidence. It does not mean that every numerical row passed, and none of these research results promotes a reproduction authority table.

| Stage | Preregistered scope | Observed result | Gate |
|---|---|---|---|
| H2 stable bundles | 3 cases × 3 methods | {h2b['method_rows']} rows; improved accepted={h2b['accepted_improved_rows']}; pointwise fail=3 | `{h2b['h2_gate_status']}` |
| H2 stable manifolds | 3 cases × 3 methods × 3 perturbations × 2 signs | {h2m['rows']} rows; improved accepted={h2m['accepted_improved_rows']} | `{h2m['h2_stable_manifold_gate_status']}` |
| H3 Route-H rank-two objects | 2 cases and 8 angular seeds | {h3['diagnostic_rows']} phase diagnostics; {h3['manifold_rows']} manifold rows; Schur accepted={h3['accepted_schur_manifold_rows']} | `{h3['h3_gate_status']}` |
| H4 three-period propagation | 3 cases × 2 methods × 2 signs | {h4['event_rows']} result rows: accepted=8 and physical boundary=4; {h4['trajectory_rows']} trajectory events | `{h4['h4_gate_status']}` |
| H5 Sun–Earth expansion | 3 distinct local sources × 3 methods | {h5['benchmark_rows']} benchmark rows; improved boundary=6 and pointwise fail=3 | `{h5['h5_gate_status']}` |

### 11.1 Stable bundles and stable-manifold propagation

The Halo N45, Vertical N57, and Sun–Earth member-468 anchors were reevaluated on the stable branch and propagated backward. Both improved methods produced six accepted one-dimensional stable-bundle rows across the three cases, whereas all three pointwise rows retained order-1e-1 invariance residuals and failed. The subsequent 54-row stable-manifold campaign covered three perturbation norms and both signs: 36 improved-method rows were accepted, while 18 pointwise rows retained their upstream bundle failure. This closes the previously explicit stable-branch evidence gap only for the declared cases, one mapping period, and perturbation range.

### 11.2 Physical Route-H rank-two real objects

The corrected-rho operators for members 68 and 32 remain rank-two real conjugate blocks and are never relabelled as one-dimensional directions. Their maximum raw equation residual is `{fmt_e(max(float(row['raw_equation_residual']) for row in e['h3_diag']))}` and their maximum gauge-consistent subspace residual is `{fmt_e(max(float(row['gauge_consistent_subspace_residual']) for row in e['h3_diag']))}`. Real-Schur realification generated four accepted rank-two manifold cells while retaining the frozen Stage-E normalized-frame residuals and one-dimensional failures. H3 therefore adds a valid rank-two representation and geometric object; it does not rewrite the historical rank-one gate.

QR/SVD was bounded to local-SVD, Schur-seed, and deterministic-random initializations with 500 iterations each. All six retries remained bounded failures, generated no accepted manifold, and were never collapsed to rank one. The supported claim is method-specific: the Schur construction yields the tested rank-two objects, whereas the tested QR/SVD variants do not converge to an accepted object.

### 11.3 Three-period propagation and physical-radius boundaries

H4 propagated each stable anchor for exactly three mapping periods. Local, global, and far-field thresholds record first crossings but never terminate integration. Eight of twelve method/sign rows were accepted and four were retained as physical boundaries; every case has at least one collision-free accepted row. Four close-approach first attempts triggered the single preregistered tighter retry. The maximum selected Jacobi drift is `{fmt_e(float(h4['maximum_selected_jacobi_drift']))}`. The positive Halo and negative Vertical signs enter the sampled lunar physical radius for both improved methods, so these rows remain boundaries rather than being deleted or described as numerical failures.

### 11.4 Three additional local Sun–Earth sources

H5 uses three different local source artifacts and arrays: active-event-step, sharpness-stage-4, and energy-frontier. None is a frozen Stage-C registry array. Recomputed source-map residuals are {source_residuals} and pass their source-specific limits. The six improved Schur/QR benchmark rows have residuals near 4.3e-5 to 4.8e-5 and therefore remain boundaries under the frozen research threshold; all three pointwise rows fail. The associated one-period campaign stores 12 improved-method boundary rows and six diagnostic pointwise failures.

Here, “independent new source” is deliberately narrow: the sources are distinct local artifacts, state arrays, and metadata fingerprints. They are not an external solver, external institution, or independent experimental dataset. Every H5 row carries the preregistered source-authority boundary.
""".strip()


def build_zh(e: dict[str, Any]) -> str:
    config = e["config"]
    text = BASE_ZH.read_text(encoding="utf-8")
    text = require_replace(
        text,
        "# 拟周期轨道实不变子束计算方法的数值比较与可靠性分析",
        f"# {config['title_zh']}",
    )
    text = require_replace(
        text,
        "- 稿件定位：数值框架与系统比较（`numerical_framework_and_systematic_comparison`）",
        "- 稿件定位：数值框架、系统比较与有界扩展（`numerical_framework_systematic_comparison_and_bounded_extension`）",
    )
    text = require_replace(
        text,
        "- 状态：导师评审初稿；`not_submission_ready`；不声明已经达到投稿条件",
        "- 状态：`adviser_submission_decision_candidate`；可交导师决定是否进入选刊与投稿准备；尚未选刊，未获外部投稿授权",
    )
    text = require_replace(
        text,
        "## 12. 局限性与讨论",
        stage_h_table_zh(e) + "\n\n## 13. 局限性与讨论",
    )
    text = require_replace(text, "## 13. 结论", "## 14. 结论")
    old_gap = "第四，流形范围限于 7 案例的一维不稳定子束、固定传播窗、三种扰动、两个符号、无事件终止和 CR3BP 会合坐标。稳定子束、二维 Route H 流形对象、长时间事件传播、更多 Sun–Earth 案例和更高保真星历模型尚未独立验证。局部 bundle 残差与全局流形片几何是不同验收对象，不能互相代替。"
    new_gap = "第四，Stage H 已增加三个稳定子束及其稳定流形、两个 Route H 二维实子空间流形、三个三周期传播案例和三个不同本地 Sun–Earth 源。其有效范围仍受预注册案例、CR3BP 会合坐标、固定三周期、有限扰动和本地源权威边界限制；尚未覆盖高保真星历、外部独立求解器、全轨道族统计或更长任务级传播。局部 bundle 残差与全局流形片几何仍是不同验收对象，不能互相代替。"
    text = require_replace(text, old_gap, new_gap)
    old_status = "最后，独立后端、失败分类、消融、全新进程和 CI 使证据链更可靠，却不自动满足期刊的理论深度、统计广度、稳定子束、二维流形或外部数据要求。本文是可交导师评审的完整初稿，**不声明已经达到投稿条件**。"
    new_status = "最后，Stage H 补齐了旧稿点名的四类计算证据，但独立后端、失败分类、消融、全新进程和 CI 仍不会自动满足具体期刊的理论深度、统计广度、外部验证或格式要求。本包的精确状态是 **可交导师作投稿决策**，不是“已经达到投稿条件”，更不是已经获得外部投稿授权。"
    text = require_replace(text, old_status, new_status)
    old_next = "在冻结阈值下，partial real-Schur 和 shifted QR/SVD 相对 pointwise eig 显著降低了可接受案例的 cocycle 残差，同时把二维共轭子空间、初始化敏感和全片不收敛等负结果明确暴露出来。最稳妥的论文定位是 `numerical_framework_and_systematic_comparison`：贡献在于同源数据、统一门槛、独立后端、失败证据和可重复工程的系统结合，而非新理论。下一步应优先增加稳定子束、二维 Route H 流形、长事件传播和更多 Sun–Earth 独立案例，再由导师判断目标期刊与理论深化方向。"
    new_next = "在冻结阈值下，partial real-Schur 和 shifted QR/SVD 相对 pointwise eig 显著降低了可接受案例的 cocycle 残差，同时把二维共轭子空间、初始化敏感、物理半径穿越与 Sun–Earth 源权威边界明确暴露出来。Stage H 已按预注册补充稳定子束、二维 Route H 流形、三周期传播和三个新增本地 Sun–Earth 源；最稳妥的论文定位因此更新为 `numerical_framework_systematic_comparison_and_bounded_extension`。下一步不是继续无边界扩算，而是由导师决定目标期刊、理论深化程度、是否要求外部求解器复核，以及哪些 boundary 结果进入正文。"
    text = require_replace(text, old_next, new_next)
    text = text.replace("](figures/", "](../../paper_release/figures/")
    return text.rstrip() + "\n"


def build_en(e: dict[str, Any]) -> str:
    config = e["config"]
    text = BASE_EN.read_text(encoding="utf-8")
    first = "# Auditable Real Invariant-Bundle Computation for Quasi-Periodic CR3BP Tori"
    text = require_replace(text, first, f"# {config['title_en']}")
    text = require_replace(
        text,
        "> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.",
        "> Status: `adviser_submission_decision_candidate`. This bilingual package is ready for an adviser’s venue/submission decision; no target journal has been selected and no external submission is authorized.",
    )
    identity = (
        "\n- Author: Wuwenhao Wu (兀文昊)\n"
        "- Adviser: Chen Zhang (张晨)\n"
        "- Institution: University of Chinese Academy of Sciences\n"
        "- Package date: 2026-07-21\n"
    )
    anchor = "- Registry SHA256:"
    if anchor not in text:
        raise RuntimeError("English manuscript identity anchor drifted")
    text = text.replace(anchor, identity + "\n" + anchor, 1)
    text = require_replace(
        text,
        "## 11. Discussion",
        stage_h_table_en(e) + "\n\n## 12. Discussion",
    )
    text = require_replace(text, "## 12. Limitations", "## 13. Limitations")
    text = require_replace(text, "## 13. Conclusion", "## 14. Conclusion")
    text = require_replace(text, "## Evidence map", "## 15. Evidence map")
    old_limit = (
        "This draft has no external literature comparison, theoretical convergence\n"
        "proof, stable-bundle manifold campaign, two-dimensional manifold object, or\n"
        "long-event global propagation.  The Schur backend is a verified partial block,\n"
        "not an independent LAPACK Schur run.  Route H remains a failed physical bundle\n"
        "family under the tested methods.  Lower-resolution manifold geometry remains\n"
        "outside the 0.01 boundary.  The Chapter-4 projection holdout remains failed and\n"
        "is untouched."
    )
    new_limit = (
        "Stage H adds three stable-bundle campaigns, two rank-two Route-H manifold "
        "objects, three fixed three-period propagations, and three distinct local "
        "Sun–Earth source benchmarks. The supported scope is still bounded by the "
        "preregistered CR3BP cases, finite perturbations, a three-period horizon, and "
        "local source artifacts. There is no new convergence theorem, external solver "
        "replication, ephemeris-model validation, or target-journal assessment. The "
        "lower-resolution 0.01 manifold boundary and the frozen Chapter-4 0/4 projection "
        "holdout remain untouched."
    )
    text = require_replace(text, old_limit, new_limit)
    conclusion_anchor = (
        "These failures define the current\n"
        "scope of the contribution and prevent overclaiming."
    )
    conclusion_update = (
        "These failures and boundaries define the current scope of the contribution and "
        "prevent overclaiming. The completed Stage-H campaign upgrades the deliverable "
        "from an internal draft to an adviser submission-decision candidate, not to an "
        "externally authorized or venue-formatted submission."
    )
    text = require_replace(text, conclusion_anchor, conclusion_update)
    figures = """

![Method-level accepted, boundary, and failed outcomes](../../paper_release/figures/fig_bundle_method_summary.png)

![Route-H physical and legacy operator controls](../../paper_release/figures/fig_route_h_rho_control.png)

![Representative manifold displacement sheets](../../paper_release/figures/fig_halo_manifold_displacement_sheets.png)
"""
    text = text.replace("## 13. Limitations", figures.strip() + "\n\n## 13. Limitations", 1)
    return text.rstrip() + "\n"


def claim_rows(e: dict[str, Any]) -> list[dict[str, str]]:
    figure_observed = (
        "; ".join(f"{key}={value}" for key, value in e["figure_counts"].items())
        if e["figure_counts"]
        else "figure audit not included in package inputs"
    )
    return [
        {
            "claim_id": "SC01",
            "claim_text_zh": "McCarthy 54 图实现为完整工程覆盖，不是整篇学位论文严格等价复现。",
            "claim_text_en": "The 54 McCarthy figures are complete engineering coverage, not thesis-wide strict equivalence.",
            "evidence_scope": "54 reproduction targets",
            "evidence_paths": rel(BASELINE),
            "acceptance_rule": "target_rows=54; V0=13; V2=41; frozen labels retained",
            "observed": "54 targets; 13 V0; 41 V2",
            "status": "supported_with_boundary",
            "authority_boundary": "research outputs cannot promote reproduction labels",
            "adviser_decision_use": "separate paper-method merit from reproduction equivalence",
        },
        {
            "claim_id": "SC02",
            "claim_text_zh": "Chapter 4 冻结投影 holdout 保持 0/4。",
            "claim_text_en": "The frozen Chapter-4 projection holdout remains 0/4.",
            "evidence_scope": "Fig. 4.3–4.6 holdout panels",
            "evidence_paths": rel(HOLDOUT),
            "acceptance_rule": "four rows; paper_projection=fail; paper_3d=false",
            "observed": "0/4; paper_projection=fail; paper_3d=false",
            "status": "supported_negative",
            "authority_boundary": "post-hoc or Stage-H evidence cannot overwrite the holdout",
            "adviser_decision_use": "do not market the work as a strict McCarthy reproduction",
        },
        {
            "claim_id": "SC03",
            "claim_text_zh": "基础研究层包含 15 案例、4 类轨道族和 3 种方法。",
            "claim_text_en": "The foundational research layer contains 15 cases, four families, and three methods.",
            "evidence_scope": "Stage C–F registry and method table",
            "evidence_paths": "research/invariant_bundles/benchmarks/benchmark_registry.csv;research/invariant_bundles/results/csv/method_comparison.csv",
            "acceptance_rule": "15 registry rows and 45 method rows",
            "observed": "15 cases; 4 families; 3 methods",
            "status": "supported",
            "authority_boundary": "finite benchmark, not family-wide enumeration",
            "adviser_decision_use": "supports systematic-comparison positioning",
        },
        {
            "claim_id": "SC04",
            "claim_text_zh": "基础层点式 eig 为 0/15 accepted，两种改进方法在代表案例显著降低 cocycle 残差。",
            "claim_text_en": "Pointwise eig is 0/15 accepted in the base layer, while both improved methods reduce cocycle residuals on representative cases.",
            "evidence_scope": "all Stage-C bundle cases",
            "evidence_paths": "research/invariant_bundles/results/csv/method_comparison.csv",
            "acceptance_rule": "accepted max residual <=1e-6",
            "observed": "pointwise 0 accepted; Schur 7; QR/SVD 10",
            "status": "supported",
            "authority_boundary": "research status only",
            "adviser_decision_use": "core numerical-comparison claim",
        },
        {
            "claim_id": "SC05",
            "claim_text_zh": "MATLAB real-Schur 独立后端在 12 个关键离散算子上维数、分类和状态一致。",
            "claim_text_en": "An independent MATLAB real-Schur backend agrees in dimension, classification, and status on 12 key discrete operators.",
            "evidence_scope": "12 independent-backend cases",
            "evidence_paths": "research/invariant_bundles/results/csv/independent_schur_backend_comparison.csv",
            "acceptance_rule": "principal angle <=1e-4 deg and exact categorical agreement",
            "observed": "12/12 categorical agreement",
            "status": "supported",
            "authority_boundary": "finite discrete-operator validation, not a theorem",
            "adviser_decision_use": "supports implementation credibility",
        },
        {
            "claim_id": "SC06",
            "claim_text_zh": "H2 在三个代表案例上得到 6 行 accepted 稳定一维子束。",
            "claim_text_en": "H2 obtains six accepted stable one-dimensional bundle rows on three representative cases.",
            "evidence_scope": "Halo N45; Vertical N57; Sun–Earth 468",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/stable_bundles/stable_bundle_comparison.csv",
            "acceptance_rule": "both improved methods accepted per case",
            "observed": "3 cases; improved accepted=6; pointwise fail=3",
            "status": "supported",
            "authority_boundary": "three cases and one mapping period",
            "adviser_decision_use": "closes the named stable-bundle evidence gap",
        },
        {
            "claim_id": "SC07",
            "claim_text_zh": "H2 稳定流形保存 54 行，其中改进方法 36 行 accepted、点式 18 行 fail。",
            "claim_text_en": "H2 stores 54 stable-manifold rows: 36 improved-method rows accepted and 18 pointwise rows failed.",
            "evidence_scope": "3 cases × 3 methods × 3 perturbations × 2 signs",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/stable_manifolds/stable_manifold_convergence.csv",
            "acceptance_rule": "bundle, Jacobi, local linearity, and branch gates",
            "observed": "54 rows; accepted=36; fail=18",
            "status": "supported",
            "authority_boundary": "fixed one-period CR3BP propagation",
            "adviser_decision_use": "supports stable-manifold extension",
        },
        {
            "claim_id": "SC08",
            "claim_text_zh": "H3 的两个 physical Route H 案例保持二维实共轭语义。",
            "claim_text_en": "Both physical Route-H H3 cases preserve rank-two real-conjugate semantics.",
            "evidence_scope": "members 68 and 32",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/route_h_2d_manifolds/route_h_2d_subspace_diagnostics.csv",
            "acceptance_rule": "raw local rank=2 at every phase; never relabelled 1D",
            "observed": "90/90 phase rows rank 2",
            "status": "supported",
            "authority_boundary": "does not promote the frozen Stage-E rank-one failure",
            "adviser_decision_use": "supports a dedicated rank-two case study",
        },
        {
            "claim_id": "SC09",
            "claim_text_zh": "H3 real-Schur 实化产生 4 行 accepted 二维流形对象。",
            "claim_text_en": "H3 real-Schur realification produces four accepted rank-two manifold objects.",
            "evidence_scope": "2 cases × 2 perturbation norms",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/route_h_2d_manifolds/route_h_2d_manifold_convergence.csv",
            "acceptance_rule": "rank=2; manifold generated; Jacobi and linearity gates pass",
            "observed": "4 accepted Schur rows",
            "status": "supported",
            "authority_boundary": "method-specific finite-horizon result",
            "adviser_decision_use": "candidate distinctive result for the main text",
        },
        {
            "claim_id": "SC10",
            "claim_text_zh": "H3 QR/SVD 的三种初始化均在 500 次上限内有界失败。",
            "claim_text_en": "All three H3 QR/SVD initializations remain bounded failures at the 500-iteration cap.",
            "evidence_scope": "2 cases × 3 QR initializations",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/route_h_2d_manifolds/route_h_2d_method_attempts.csv",
            "acceptance_rule": "all attempts retained; no rank-one relabelling",
            "observed": "6 bounded QR failures",
            "status": "supported_with_bounded_scope",
            "authority_boundary": "not an impossibility theorem for all algorithms",
            "adviser_decision_use": "negative-result and robustness discussion",
        },
        {
            "claim_id": "SC11",
            "claim_text_zh": "H4 三周期传播的 12 行结果中 8 行 accepted、4 行物理 boundary。",
            "claim_text_en": "Eight of twelve H4 three-period propagation rows are accepted and four are physical boundaries.",
            "evidence_scope": "3 cases × 2 methods × 2 signs",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/long_propagation/long_propagation_events.csv",
            "acceptance_rule": "Jacobi <1e-10; local linearity; physical radius separated",
            "observed": "accepted=8; physical boundary=4; 492 trajectory events",
            "status": "supported_with_physical_boundary",
            "authority_boundary": "fixed three periods; threshold events are diagnostic",
            "adviser_decision_use": "supports longer-horizon extension without hiding collisions",
        },
        {
            "claim_id": "SC12",
            "claim_text_zh": "H4 每个代表案例至少有一个无物理碰撞的 accepted 结果。",
            "claim_text_en": "Every H4 representative case has at least one collision-free accepted result.",
            "evidence_scope": "three long-propagation cases",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/long_propagation/long_propagation_summary.json",
            "acceptance_rule": "cases_with_collision_free_accepted_row=3",
            "observed": "3/3 cases",
            "status": "supported",
            "authority_boundary": "does not erase the four sign-specific physical boundaries",
            "adviser_decision_use": "supports interpretable long propagation",
        },
        {
            "claim_id": "SC13",
            "claim_text_zh": "H5 新增三个不同本地 Sun–Earth 源工件，且均不属于冻结 Stage-C 状态数组。",
            "claim_text_en": "H5 adds three distinct local Sun–Earth source artifacts, none of which is a frozen Stage-C state array.",
            "evidence_scope": "active-event-step; sharpness-stage-4; energy-frontier",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/sun_earth_expansion/source_independence.csv;research/invariant_bundles/submission_candidate/results/sun_earth_expansion/source_validation.csv",
            "acceptance_rule": "distinct artifact and array hashes; new_vs_stage_c_registry=true",
            "observed": "3 distinct local sources",
            "status": "supported_with_authority_boundary",
            "authority_boundary": "not an external independent solver or dataset",
            "adviser_decision_use": "supports cross-source breadth with precise wording",
        },
        {
            "claim_id": "SC14",
            "claim_text_zh": "H5 三源映射残差均通过各自源上限。",
            "claim_text_en": "All three H5 recomputed source-map residuals pass their source-specific limits.",
            "evidence_scope": "three H5 sources",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/sun_earth_expansion/source_validation.csv",
            "acceptance_rule": "recomputed_map_residual <= source_map_residual_limit",
            "observed": ";".join(fmt_e(float(row["recomputed_map_residual"])) for row in e["h5_sources"]),
            "status": "supported",
            "authority_boundary": "source quality does not imply paper equivalence",
            "adviser_decision_use": "supports source validity",
        },
        {
            "claim_id": "SC15",
            "claim_text_zh": "H5 的 6 行改进 bundle 与 12 行改进流形均为 boundary，而非 accepted。",
            "claim_text_en": "The six improved H5 bundle rows and twelve improved manifold rows remain boundaries, not accepted results.",
            "evidence_scope": "3 sources × 2 improved methods",
            "evidence_paths": "research/invariant_bundles/submission_candidate/results/sun_earth_expansion/benchmark_comparison.csv;research/invariant_bundles/submission_candidate/results/sun_earth_expansion/manifold_validation.csv",
            "acceptance_rule": "frozen accepted residual <=1e-6; source-authority boundary retained",
            "observed": "benchmark boundary=6; manifold boundary=12",
            "status": "supported_boundary",
            "authority_boundary": "must not be summarized as three accepted Sun–Earth cases",
            "adviser_decision_use": "decide whether boundary results belong in main text or appendix",
        },
        {
            "claim_id": "SC16",
            "claim_text_zh": "Stage H 结果不改变 54 图 baseline 或 Chapter 4 holdout。",
            "claim_text_en": "Stage-H results do not modify the 54-figure baseline or Chapter-4 holdout.",
            "evidence_scope": "all Stage-H outputs",
            "evidence_paths": "research/invariant_bundles/submission_candidate/benchmarks/stage_h_preregistration.md",
            "acceptance_rule": "authority boundary repeated in every campaign",
            "observed": "baseline and holdout hashes remain input authorities",
            "status": "supported",
            "authority_boundary": "strict no-promotion rule",
            "adviser_decision_use": "prevents reproduction overclaiming",
        },
        {
            "claim_id": "SC17",
            "claim_text_zh": "论文贡献定位为可审计数值框架、系统比较与有界扩展，而非新定理。",
            "claim_text_en": "The contribution is an auditable numerical framework, systematic comparison, and bounded extension—not a new theorem.",
            "evidence_scope": "methods, literature, and all experiments",
            "evidence_paths": "research/invariant_bundles/paper/literature_matrix.csv;research/invariant_bundles/submission_candidate/package/manuscript_en.md",
            "acceptance_rule": "explicit theorem and novelty boundaries retained",
            "observed": "positioning fixed in both manuscripts",
            "status": "supported_with_boundary",
            "authority_boundary": "no existence, uniqueness, reducibility, or convergence-rate theorem",
            "adviser_decision_use": "venue and contribution framing",
        },
        {
            "claim_id": "SC18",
            "claim_text_zh": "导师图像审计将 54 图按 P0–P3 分级，不把当前 A/B/C/D 数值门槛当作论文图等价。",
            "claim_text_en": "The adviser-facing figure audit ranks all 54 figures P0–P3 and does not equate current numerical gates with paper-figure equivalence.",
            "evidence_scope": "54-figure visual correctness audit",
            "evidence_paths": rel(FIGURE_AUDIT),
            "acceptance_rule": "exact 54-row registry coverage and explicit priority",
            "observed": figure_observed,
            "status": "supported_with_correction_queue",
            "authority_boundary": "visual defects remain a separate correction queue",
            "adviser_decision_use": "prevents visibly incorrect reproduction figures from being reused as paper-equivalent evidence",
        },
        {
            "claim_id": "SC19",
            "claim_text_zh": "中英文稿件、双语导师摘要、claim–evidence matrix 和哈希清单构成可审阅包。",
            "claim_text_en": "Chinese and English manuscripts, a bilingual adviser brief, a claim–evidence matrix, and hash manifests form a reviewable package.",
            "evidence_scope": "submission-candidate package",
            "evidence_paths": "research/invariant_bundles/submission_candidate/package/",
            "acceptance_rule": "all required Markdown, DOCX, CSV, JSON, and hash files present",
            "observed": "bilingual review package generated",
            "status": "supported",
            "authority_boundary": "document completeness is not peer-review acceptance",
            "adviser_decision_use": "enables an explicit go/revise/hold decision",
        },
        {
            "claim_id": "SC20",
            "claim_text_zh": "本包可交导师决定是否进入选刊与投稿准备，但尚未选刊、未获外部投稿授权。",
            "claim_text_en": "This package is ready for an adviser’s venue/submission-preparation decision, but no venue is selected and no external submission is authorized.",
            "evidence_scope": "package status and adviser brief",
            "evidence_paths": rel(CONFIG) + ";research/invariant_bundles/submission_candidate/package/adviser_decision_summary.md",
            "acceptance_rule": "status exact; external_submission_authorized=false; target_journal_selected=false",
            "observed": "adviser_submission_decision_candidate",
            "status": "supported_with_authorization_boundary",
            "authority_boundary": "external submission is outside the authorized scope",
            "adviser_decision_use": "the decision requested from the adviser",
        },
    ]


def adviser_summary(e: dict[str, Any]) -> str:
    counts = e["figure_counts"]
    figure_line = (
        ", ".join(f"{key}={value}" for key, value in counts.items())
        if counts
        else "图像审计未纳入本次输入"
    )
    return f"""# 导师投稿决策摘要 / Adviser Submission Decision Brief

- 学生 / Student：兀文昊 / Wuwenhao Wu
- 导师 / Adviser：张晨 / Chen Zhang
- 状态 / Status：`adviser_submission_decision_candidate`
- 日期 / Date：2026-07-21

## 一句话判断 / One-line assessment

Stage H 已按预注册补齐旧稿明确点名的稳定子束、二维 Route H 流形、三周期传播和三个新增本地 Sun–Earth 源，并形成双语、可追溯的导师决策包；建议现在由导师决定“选刊并进入针对性修改”或“先补理论/外部验证”，但本包不代表已经选刊、获得投稿授权或完成外部投稿。

Stage H has closed the four explicitly named computational evidence gaps under preregistered caps and produced a bilingual, traceable decision package. The appropriate next step is an adviser decision on venue-directed revision versus further theory/external validation—not an automatic submission.

## 本轮新增证据 / What is new

- H2：3 个稳定一维子束 benchmark，改进方法 6/6 accepted；稳定流形 54 行，其中改进方法 36 accepted、点式 18 fail。
- H3：2 个 physical Route H 二维实共轭案例；real-Schur 产生 4 个 accepted 二维流形对象；QR/SVD 三种初始化共 6 次有界失败，未降维。
- H4：3 个案例固定三周期传播；12 行中 8 accepted、4 物理 boundary；每案至少一个无碰撞 accepted 结果。
- H5：3 个不同本地 Sun–Earth 源；三源映射残差通过，但 6 个改进 bundle 和 12 个改进流形均保持 boundary。
- 交付：中英文 Markdown/Word 稿件、20 行 claim–evidence matrix、最终验收审计入口和 SHA256 清单。

## 最强可辩护贡献 / Strongest defensible contribution

1. 把“局部点式特征向量”与“相位平移 cocycle 实子束”严格分开，并以统一门槛比较点式 eig、partial real-Schur 和 shifted QR/SVD。
2. 把复共轭谱保留为二维实对象；H3 进一步证明在两个 physical Route H 案例上，二维 Schur 对象可以产生可验收的有限时流形，而一维失败仍保持失败。
3. 同时保存 accepted、boundary 和 fail，包括 QR/SVD 有界不收敛、月球物理半径穿越、Sun–Earth 源权威边界和低分辨率全片边界。
4. 通过注册表、CSV/NPZ、独立 MATLAB 后端、全新进程、哈希与回归测试形成可审计证据链。

## 不能越过的边界 / Non-negotiable boundaries

- McCarthy 54 图只达到完整工程覆盖，不是整篇学位论文严格等价复现。
- Chapter 4 冻结 holdout 仍为 `0/4`、`paper_projection=fail`、`paper_3d=false`。
- H5 的“独立”只表示 3 个不同本地源工件，不表示外部独立求解器或外部数据。
- 本文没有新的存在性、唯一性、可约化性或收敛率定理。
- 图像正确性审计当前分布为 {figure_line}；其 P0/P1 修正队列不能被数值 gate 掩盖。
- `adviser_submission_decision_candidate` 只表示材料足以作导师决策；目标期刊选择和外部投稿均不在已授权范围内。

## 建议导师作出的四个决定 / Four decisions requested

1. 主贡献是否采用“可审计数值框架 + 系统比较 + 有界扩展”，还是要求把 Route H 二维失败/成功语义提升为主标题。
2. 是否先选定目标期刊，再按其篇幅、理论深度和图表规范修改；本包不预设期刊。
3. H5 boundary 结果放正文、附录，还是要求外部求解器复核后再使用。
4. 是否把 P0/P1 复现图修正列为投稿前硬门槛，尤其是 Fig. 5.1、5.13、5.14、5.5 与 Chapter 4 投影图。

## 推荐决策口径 / Recommended decision wording

“同意将当前材料作为 submission-decision candidate，进入目标期刊筛选和针对性修改；在选刊、理论深度、外部验证和 P0/P1 图像修正方案确定前，不对外投稿，也不声明 McCarthy 全文等价复现。”

“Approve the current materials as a submission-decision candidate and begin venue selection and venue-specific revision. Do not submit externally or claim thesis-wide McCarthy equivalence until the venue, theory depth, external-validation need, and P0/P1 figure-correction plan are resolved.”
"""


def package_readme(e: dict[str, Any]) -> str:
    return """# Invariant-bundle submission-candidate package

This directory is the adviser-facing decision package created after the preregistered Stage-H campaign.

## Primary review files

- `adviser_decision_summary.docx` / `.md`: bilingual decision brief.
- `manuscript_zh.docx` / `.md`: updated Chinese manuscript.
- `manuscript_en.docx` / `.md`: updated English manuscript.
- `claim_evidence_matrix.csv`: claim-by-claim evidence, threshold, status, and authority boundary.
- `submission_candidate_summary.json`: machine-readable package summary.
- `artifact_hashes.csv`: repository-relative size and SHA256 manifest.
- `acceptance/`: final full-stack validation log and acceptance audit, written only after the validation runner passes.

## Exact status

`adviser_submission_decision_candidate` means the package is ready for an adviser to decide whether and how to proceed toward a submission. It does not mean that a target journal has been selected, that the work has passed peer review, or that external submission is authorized.

## Authority boundary

The frozen 54-figure reproduction baseline, the Chapter-4 0/4 projection holdout, and all reproduction/research authority boundaries remain unchanged. Stage-H evidence is research evidence only.
"""


def discover_node() -> tuple[Path, Path | None]:
    explicit = os.environ.get("CODEX_NODE_EXE")
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    user = Path(os.environ.get("USERPROFILE", ""))
    candidates.append(
        user
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / "node.exe"
    )
    found = shutil.which("node")
    if found:
        candidates.append(Path(found))
    bundled_modules = (
        user
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "node_modules"
    )
    for candidate in candidates:
        if candidate.is_file():
            modules = (
                candidate.parents[1] / "node_modules"
                if candidate.name.lower() == "node.exe"
                else None
            )
            if modules is not None and not modules.is_dir():
                modules = None
            if modules is None and bundled_modules.is_dir():
                modules = bundled_modules
            return candidate, modules
    raise RuntimeError("Node.js executable not found for docx-js builder")


def run_docx_builder(*, check: bool) -> None:
    node, modules = discover_node()
    environment = dict(os.environ)
    if modules is not None:
        old = environment.get("NODE_PATH", "")
        environment["NODE_PATH"] = str(modules) + (os.pathsep + old if old else "")
    command = [str(node), str(DOCX_BUILDER), "--check" if check else "--write"]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "docx-js builder failed: " + (result.stderr or result.stdout).strip()
        )


def inspect_docx(path: Path) -> dict[str, Any]:
    if path.stat().st_size < 10_000:
        raise RuntimeError(f"DOCX unexpectedly small: {rel(path)}")
    with zipfile.ZipFile(path) as archive:
        required = {"[Content_Types].xml", "word/document.xml"}
        if not required.issubset(archive.namelist()):
            raise RuntimeError(f"DOCX structure incomplete: {rel(path)}")
        root = ElementTree.fromstring(archive.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        text = "".join(node.text or "" for node in root.iter(ns + "t"))
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    if "adviser_submission_decision_candidate" not in text:
        raise RuntimeError(f"DOCX status token missing: {rel(path)}")
    return {
        "bytes": path.stat().st_size,
        "text_characters": len(text),
        "embedded_media": len(media),
    }


def summary_payload(e: dict[str, Any], docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    h2b = e["summaries"]["h2_bundle"]
    h2m = e["summaries"]["h2_manifold"]
    h3 = e["summaries"]["h3"]
    h4 = e["summaries"]["h4"]
    h5 = e["summaries"]["h5"]
    return {
        "schema_version": "invariant_bundle_submission_candidate_summary_v1",
        "status": "pass_with_explicit_boundaries",
        "package_status": e["config"]["package_status"],
        "author": e["config"]["author"],
        "adviser": e["config"]["adviser"],
        "package_date": e["config"]["package_date"],
        "external_submission_authorized": False,
        "target_journal_selected": False,
        "reproduction_target_rows": 54,
        "chapter4_frozen_holdout": "0/4",
        "figure_audit_priority_counts": e["figure_counts"],
        "h2_stable_bundle": {
            "cases": h2b["cases"],
            "method_rows": h2b["method_rows"],
            "accepted_improved_rows": h2b["accepted_improved_rows"],
            "gate": h2b["h2_gate_status"],
        },
        "h2_stable_manifold": {
            "rows": h2m["rows"],
            "accepted_improved_rows": h2m["accepted_improved_rows"],
            "gate": h2m["h2_stable_manifold_gate_status"],
        },
        "h3_route_h_2d": {
            "cases": h3["cases"],
            "diagnostic_rows": h3["diagnostic_rows"],
            "accepted_schur_manifold_rows": h3["accepted_schur_manifold_rows"],
            "qr_bounded_failure_cases": h3["qr_bounded_failure_cases"],
            "never_one_dimensional": h3["never_one_dimensional"],
            "gate": h3["h3_gate_status"],
        },
        "h4_long_propagation": {
            "cases": h4["cases"],
            "event_rows": h4["event_rows"],
            "accepted_rows": count(e["h4_rows"], "status").get("accepted", 0),
            "physical_boundary_rows": h4["secondary_radius_boundary_rows"],
            "trajectory_rows": h4["trajectory_rows"],
            "gate": h4["h4_gate_status"],
        },
        "h5_sun_earth": {
            "distinct_local_sources": h5["independent_new_source_benchmarks"],
            "benchmark_status_counts": count(e["h5_benchmarks"], "research_status"),
            "manifold_status_counts": count(e["h5_manifolds"], "status"),
            "source_authority_boundary_cases": h5["source_authority_boundary_cases"],
            "gate": h5["h5_gate_status"],
        },
        "claim_evidence_rows": 20,
        "documents": docs,
        "authority_boundaries_preserved": True,
    }


def manifest_rows() -> list[dict[str, Any]]:
    generated = [
        PACKAGE / "manuscript_zh.md",
        PACKAGE / "manuscript_zh.docx",
        PACKAGE / "manuscript_en.md",
        PACKAGE / "manuscript_en.docx",
        PACKAGE / "claim_evidence_matrix.csv",
        PACKAGE / "adviser_decision_summary.md",
        PACKAGE / "adviser_decision_summary.docx",
        PACKAGE / "package_readme.md",
        PACKAGE / "submission_candidate_summary.json",
    ]
    evidence = [BASELINE, HOLDOUT, *SUMMARY_PATHS.values()]
    if FIGURE_AUDIT.is_file():
        evidence.append(FIGURE_AUDIT)
    source = [CONFIG, Path(__file__), DOCX_BUILDER]
    rows: list[dict[str, Any]] = []
    for role, paths in (
        ("generated_package", generated),
        ("frozen_or_stage_h_evidence", evidence),
        ("package_source", source),
    ):
        for path in paths:
            if not path.is_file():
                raise RuntimeError(f"manifest input missing: {rel(path)}")
            rows.append(
                {
                    "artifact_role": role,
                    "path_root": "repository",
                    "path": rel(path),
                    **fingerprint_fields(path),
                }
            )
    return rows


def validate_manifest() -> None:
    path = PACKAGE / "artifact_hashes.csv"
    rows = read_csv(path)
    if not rows:
        raise RuntimeError("package artifact hash manifest is empty")
    for row in rows:
        if row["path_root"] != "repository":
            raise RuntimeError(f"manifest path root drift: {row['path']}")
        artifact = ROOT / row["path"]
        if not artifact.is_file():
            raise RuntimeError(f"manifest artifact missing: {row['path']}")
        if not fingerprint_matches(
            artifact,
            expected_bytes=int(row["bytes"]),
            expected_sha256=row["sha256"],
            hash_mode=row["hash_mode"],
        ):
            raise RuntimeError(f"manifest fingerprint drift: {row['path']}")


def build(*, check: bool) -> None:
    e = collect_evidence()
    claims = claim_rows(e)
    if len(claims) != 20 or [row["claim_id"] for row in claims] != [
        f"SC{index:02d}" for index in range(1, 21)
    ]:
        raise RuntimeError("claim matrix ID contract drifted")
    expected_text = {
        "manuscript_zh.md": build_zh(e),
        "manuscript_en.md": build_en(e),
        "claim_evidence_matrix.csv": csv_text(claims, CLAIM_FIELDS),
        "adviser_decision_summary.md": adviser_summary(e).rstrip() + "\n",
        "package_readme.md": package_readme(e).rstrip() + "\n",
    }

    if check:
        for name, expected in expected_text.items():
            path = PACKAGE / name
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                raise RuntimeError(f"submission-candidate package drifted: {name}")
        run_docx_builder(check=True)
    else:
        PACKAGE.mkdir(parents=True, exist_ok=True)
        for name, text in expected_text.items():
            (PACKAGE / name).write_text(text, encoding="utf-8")
        run_docx_builder(check=False)

    docs = {
        name: inspect_docx(PACKAGE / name)
        for name in (
            "manuscript_zh.docx",
            "manuscript_en.docx",
            "adviser_decision_summary.docx",
        )
    }
    if docs["manuscript_zh.docx"]["embedded_media"] < 6:
        raise RuntimeError("Chinese manuscript embeds fewer than six figures")
    if docs["manuscript_en.docx"]["embedded_media"] < 3:
        raise RuntimeError("English manuscript embeds fewer than three figures")
    summary_text = json.dumps(
        summary_payload(e, docs), ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    summary_path = PACKAGE / "submission_candidate_summary.json"
    if check:
        if not summary_path.is_file() or summary_path.read_text(encoding="utf-8") != summary_text:
            raise RuntimeError("submission-candidate summary drifted")
        validate_manifest()
        print("SUBMISSION-CANDIDATE PACKAGE CHECK PASS claims=20 documents=3")
        return

    summary_path.write_text(summary_text, encoding="utf-8")
    (PACKAGE / "artifact_hashes.csv").write_text(
        csv_text(manifest_rows(), HASH_FIELDS), encoding="utf-8"
    )
    validate_manifest()
    print("SUBMISSION-CANDIDATE PACKAGE WRITE PASS claims=20 documents=3")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    build(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
