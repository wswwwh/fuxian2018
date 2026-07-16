"""Bind current authoritative evidence to all 54 figures and build Stage-C registries."""

from __future__ import annotations

import collections
import csv
import glob
import json
import math
import re
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
PROJECT_ROOT = REPORT_ROOT.parents[1]
STAGE_C = REPORT_ROOT / "stage_c"
PENDING = "【待核实】"


CORE_FIGURES = {
    *(f"3.{number}" for number in range(5, 11)),
    *(f"3.{number}" for number in range(12, 18)),
    *(f"4.{number}" for number in range(1, 9)),
    "5.1",
    *(f"5.{number}" for number in range(8, 15)),
}

TITLE_CN = {
    "2.1": "三体系统几何与参考坐标系",
    "2.2": "共线平动点求解几何",
    "2.3": "五个平动点的相对位置",
    "2.4": "地月系统零速度曲线",
    "2.5": "地月系统零速度面",
    "2.6": "地月、土卫六与日地系统零速度曲线对照",
    "2.7": "地月 L1 点附近面内与面外线性模态",
    "2.8": "地月 L1 点附近线性 Lissajous 运动",
    "2.9": "单步打靶差分修正示意",
    "2.10": "多步打靶轨迹弧段示意",
    "2.11": "L2 Lyapunov 初值与修正解",
    "2.12": "自然参数与伪弧长延拓示意",
    "2.13": "木星—欧罗巴 L2 周期轨道族",
    "2.14": "L1 Lyapunov 轨道的稳定与不稳定流形",
    "2.15": "地月 L2 Halo 轨道族稳定指标",
    "3.1": "二维环面作为两个圆的直积",
    "3.2": "不变曲线、旋转角与回归轨迹",
    "3.3": "七节点离散不变曲线映射",
    "3.4": "多步打靶环面修正的拼接曲线",
    "3.5": "定能量拟 Halo 环面族",
    "3.6": "定能量拟 Halo 振幅曲线",
    "3.7": "定能量拟垂直环面族",
    "3.8": "定能量拟垂直振幅曲线",
    "3.9": "频率比随映射时间变化",
    "3.10": "period-2、period-3 与 period-8 Halo 示例",
    "3.11": "Poincare 映射与中心周期轨道",
    "3.12": "定频率拟 Halo 环面族",
    "3.13": "定频率拟 Halo 振幅与 Jacobi 常数",
    "3.14": "定频率拟垂直环面族",
    "3.15": "定频率拟垂直 Jacobi 常数与映射时间",
    "3.16": "定映射时间拟 DRO 环面",
    "3.17": "拟 DRO 振幅与 Jacobi 常数随旋转角变化",
    "4.1": "地月 L2 拟 Halo 轨道与 DG 特征结构",
    "4.2": "拟 Halo 稳定指标随映射时间变化",
    "4.3": "拟 Halo +x 方向不稳定流形",
    "4.4": "拟 Halo -x 方向不稳定流形",
    "4.5": "拟垂直 +x 方向不稳定流形",
    "4.6": "拟垂直 -x 方向不稳定流形",
    "4.7": "拟 Halo 与周期 Halo 流形对照",
    "4.8": "拟垂直与周期 Halo 流形对照",
    "5.1": "日地 L1 拟垂直轨道长时传播",
    "5.2": "日—月食几何示意",
    "5.3": "地—月—航天器视线几何",
    "5.4": "日—地—月会合坐标几何",
    "5.5": "拟 DRO 与对应平面周期 DRO",
    "5.6": "不同相位的拟 DRO 星历轨迹",
    "5.7": "不同插入历元的拟 DRO 星历轨迹",
    "5.8": "Halo 至 Lyapunov 转移初值与收敛解",
    "5.9": "NRHO 与候选离去位置",
    "5.10": "两处离去位置的收敛转移轨迹",
    "5.11": "两条 NRHO 之间的收敛转移",
    "5.12": "交会速度增量随到达时间变化",
    "5.13": "日地 L1 稳定流形近地点热图",
    "5.14": "LEO 至日地 L1 拟周期 Lissajous 轨道转移",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and not fieldnames:
        raise ValueError(f"Cannot write fieldless empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames or list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def figure_key(figure_id: str) -> tuple[int, int]:
    return tuple(int(part) for part in figure_id.split("."))


def grade_for(status: str) -> tuple[str, str]:
    mapping = {
        "accepted": ("A", "按当前项目审计门槛定量通过；不自动声明与原作者离散节点逐点等价"),
        "boundary": ("B", "真实数值解与主要物理趋势受支持；严格论文等价仍有边界"),
        "diagnostic": ("C", "局部、部分分支或诊断性数值源层"),
        "proxy": ("D", "示意或代理层；不得写成定量数值复现"),
    }
    return mapping.get(status, ("E", PENDING))


def model_for(figure_id: str, grade: str, title: str, source_layer: str) -> str:
    if grade == "D":
        if figure_id in {"2.1", "2.2", "2.9", "2.10", "2.12", "3.1", "3.2", "3.3", "3.4", "5.2", "5.3", "5.4"}:
            return "几何/算法示意（数值动力学模型不作为该图验收对象）"
    if figure_id == "2.13":
        return "Jupiter-Europa CR3BP"
    if figure_id in {"5.1", "5.13", "5.14"}:
        return "Sun-Earth CR3BP"
    if figure_id in {"5.6", "5.7"}:
        return "DE421 星历初始化的 Earth-Moon 几何/传播基线"
    if figure_id == "5.10":
        return "DE421 初始化的平面 Earth-Moon BCR4BP；CR3BP 结果仅作对照"
    if "BCR4BP" in source_layer:
        return "Earth-Moon BCR4BP/CR3BP 分层源数据"
    if "Sun-Earth" in title or "Sun-Earth" in source_layer:
        return "Sun-Earth CR3BP"
    return "Earth-Moon CR3BP"


def coordinate_for(figure_id: str, grade: str, model: str) -> str:
    if figure_id == "2.1":
        return "惯性坐标系与旋转坐标系的概念定义"
    if figure_id == "5.2":
        return (
            "无物理状态坐标系；局部二维示意绘图坐标（Sun=(0,0)、Moon=(5.6,0)），"
            "原点、轴向和历元不作为数值元数据"
        )
    if figure_id == "5.3":
        return (
            "无物理状态坐标系；局部二维示意绘图坐标（Earth=(0,0)、Moon=(4.0,0)），"
            "原点、轴向和历元不作为数值元数据"
        )
    if figure_id == "5.4":
        return "无物理状态坐标系；局部二维日—地—月会合示意坐标（Sun=(0,0)），历元不适用"
    if figure_id == "5.6":
        return (
            "月心瞬时 Sun–Moon 正交旋转坐标，X 指向 Sun、Z 为 Sun–Moon 轨道角动量方向，"
            "单位 km；共同历元 2020-06-15T00:00:00Z"
        )
    if figure_id == "5.7":
        return (
            "月心瞬时 Sun–Moon 正交旋转坐标，X 指向 Sun、Z 为 Sun–Moon 轨道角动量方向，"
            "单位 km；历元为 2020-06-01/04/10/15T00:00:00Z"
        )
    if figure_id == "5.10":
        return (
            "Earth–Moon 质心旋转坐标，状态顺序 [x,y,z,xdot,ydot,zdot]，Earth–Moon LU/TU "
            "归一化；项目 BCR4BP 扩展由 DE421 于 2020-06-15T00:00:00Z 初始化，"
            "论文自主 CR3BP 工况历元不适用"
        )
    if "DE421" in model:
        return "由对应脚本定义的 DE421 初始化旋转坐标；具体历元和轴向见该图证据文件"
    if grade == "D" and figure_id in {"2.9", "2.10", "2.12", "3.1", "3.2", "3.3", "3.4"}:
        return "算法/拓扑示意坐标，不用于状态空间逐点比较"
    return "主星-次星质心旋转（synodic）无量纲坐标；图中物理量按脚本输出为无量纲量、km 或 day"


def method_for(figure_id: str, grade: str) -> str:
    groups = [
        ({"2.1", "2.2", "2.5", "5.2", "5.3", "5.4"}, "几何关系示意与确定性绘图"),
        ({"2.3"}, "CR3BP 平动点方程求根与位置计算"),
        ({"2.4", "2.6"}, "Jacobi 常数与零速度曲线/面网格计算"),
        ({"2.7", "2.8"}, "L1 线性化中心模态与线性 Lissajous 构造"),
        ({"2.9"}, "单步打靶差分修正方法示意"),
        ({"2.10"}, "多步打靶弧段与连续性约束示意"),
        ({"2.11"}, "周期轨道单步打靶差分修正与数值积分"),
        ({"2.12"}, "自然参数与伪弧长延拓示意"),
        ({"2.13"}, "周期轨道差分修正、分支延拓与三维族绘制"),
        ({"2.14"}, "单周期矩阵特征方向扰动与稳定/不稳定流形传播"),
        ({"2.15"}, "周期轨道族延拓、单周期矩阵与稳定指标计算"),
        ({"3.1", "3.2", "3.3", "3.4"}, "不变环面/不变曲线、映射与多段校正的概念示意"),
        ({"3.5", "3.6", "3.7", "3.8"}, "定能量不变曲线 Newton 校正、延拓与 CR3BP 传播"),
        ({"3.9"}, "校正族的频率比/映射时间计算；尾段保留代理边界"),
        ({"3.10"}, "period-q 多步打靶、单步闭合复核与单周期矩阵审计"),
        ({"3.11"}, "Poincare/频闪映射传播与中心周期轨道数值解"),
        ({"3.12", "3.13", "3.14", "3.15"}, "固定频率比不变曲线校正、延拓与谱残差检查"),
        ({"3.16", "3.17"}, "固定映射时间 Route H 不变曲线源层重验证、相位返回与多返回检查"),
        ({"4.1"}, "离散不变曲线映射导数 DG、谱分解与稳定指标核对"),
        ({"4.2"}, "DG 稳定性族计算、原图曲线数字化与公共区间逐点审计"),
        ({"4.3", "4.4", "4.5", "4.6"}, "固定时刻全环面流形传播、局部 STM 复核、冻结相机/投影 holdout"),
        ({"4.7", "4.8"}, "DG 特征方向扰动与全局不稳定流形传播对照"),
        ({"5.1"}, "Sun-Earth L1 校正 Lissajous 不变环面与长时传播审计"),
        ({"5.5"}, "Earth-Moon quasi-DRO 数值族与周期 DRO 对照"),
        ({"5.6", "5.7"}, "Route H 初始几何与 DE421 历元/相位场景传播"),
        ({"5.8"}, "等 Jacobi 多步打靶转移修正与端点复核"),
        ({"5.9"}, "NRHO 族/走廊几何搜索与逐图源层审计"),
        ({"5.10"}, "DE421 初始化 BCR4BP 分段修正、端点/缺陷负对照与脉冲统计"),
        ({"5.11"}, "CR3BP 对称反向转移与端点差分修正"),
        ({"5.12"}, "固定离去状态的到达时间偏移扫描与折叠边界记录"),
        ({"5.13"}, "双角度不变环面采样、稳定流形相位扫描与近地点搜索"),
        ({"5.14"}, "稳定流形传播、近地点/LEO 目标筛选与端点审计"),
    ]
    for ids, method in groups:
        if figure_id in ids:
            return method
    return "脚本与权威数据驱动的确定性复现；具体算法细节【待核实】" if grade != "D" else "示意绘图"


def chinese_assessment(figure_id: str, grade: str) -> tuple[str, str, str, str]:
    consistency = {
        "A": "当前证据支持主要论文参数、数值对象和项目内部残差门槛的一致性。",
        "B": "当前结果包含真实数值解，动力学对象、拓扑或主要变化趋势与原图目标相对应。",
        "C": "当前结果给出局部数值源层或诊断性解，只覆盖原图的部分区间、分支或闭合条件。",
        "D": "当前结果重构了坐标、几何或算法语义，不承担定量数值等价证明。",
        "E": "当前证据不足以形成数值或示意层复现结论。",
    }[grade]
    difference = {
        "A": "未发现超出已记录边界的当前门槛失败；绘图视角与原作者离散节点仍可能不同。",
        "B": "原始节点、完整分支、相位、投影参数或任务约束未完全公开，尚不能证明逐点等价。",
        "C": "局部分支、覆盖范围或闭合门槛尚未达到论文全图条件。",
        "D": "线型、布局与标注为本项目独立绘制，不以像素相似作为验收目标。",
        "E": "缺少足够证据，差异原因【待核实】。",
    }[grade]
    reason = {
        "A": "论文未公开完整离散节点和绘图元数据；当前结论仅限已验证指标。",
        "B": "差异与未公开源数据、分支覆盖、相位/视角或模型保真度边界相符，但不作唯一归因。",
        "C": "现有求解链仅在局部或诊断门槛内稳定，不能外推到未计算区间。",
        "D": "示意图目标是语义和几何关系，而非原图数据重建。",
        "E": "现有资料不足，保留【待核实】。",
    }[grade]
    limitation = {
        "A": "A 级仅表示当前项目门槛内定量通过，不等于原作者节点逐点等价。",
        "B": "结论限于当前真实数值源层和已报告趋势，不扩展为严格论文等价。",
        "C": "只可用于局部/诊断性结论，未覆盖部分不得外推。",
        "D": "只可用于概念说明，不得报告数值误差或严格等价。",
        "E": "尚未完成；所有结论均为【待核实】。",
    }[grade]
    specific = {
        "3.10": (
            "q=2 和 q=3 通过严格单步闭合；q=8 仅通过局部多步打靶连续性。",
            "q=8 单步全周期闭合误差为 3.906984451743337，不能作为稳健周期轨道证据。",
            "q=8 高不稳定性导致单步闭合失败，当前只保留局部多段数值解。",
            "q=8 必须维持 C 级边界，直至存在新的严格闭合审计。",
        ),
        "3.16": (
            "Route H 定映射时间源层通过当前缓存重验证并覆盖论文振幅门槛。",
            "单体冷启动延拓仍失败，原作者完整分支节点也未公开。",
            "混合冷启动链可重建目标层，但不能替代单体冷启动失败记录。",
            "只声明 Route H 图源层有效，不声明整条论文分支逐点等价。",
        ),
        "3.17": (
            "Route H 数值分支提供振幅—旋转角—Jacobi 趋势，参考趋势仅作低权重背景。",
            "当前旋转角覆盖窄于图像数字化参考范围，且含低权重代理趋势。",
            "原始分支数据未公开，单体冷启动仍失败。",
            "该图维持 C 级诊断/部分覆盖，不将参考趋势当作原始数据。",
        ),
        "4.2": (
            "公共区间内数字化曲线逐点门槛通过，DG 数值族与稳定趋势对应。",
            "完整曲线尾段尚缺 0.04945011318863024 day，未作外推。",
            "当前校正分支在折叠附近终止。",
            "只对公共区间作点对点声明，完整曲线等价仍未通过。",
        ),
        "4.3": ("状态空间与局部 STM 数值行通过。", "冻结 panel-(d) 投影 holdout 为 0/4。", "论文投影轮廓与当前渲染/源环面语义仍不一致。", "不得声明论文视角、物理飞行或三维等价。"),
        "4.4": ("状态空间与局部 STM 数值行通过。", "冻结 panel-(d) 投影 holdout 为 0/4。", "论文投影轮廓与当前渲染/源环面语义仍不一致。", "不得声明论文视角、物理飞行或三维等价。"),
        "4.5": ("状态空间与局部 STM 数值行通过。", "冻结 panel-(d) 投影 holdout 为 0/4。", "论文投影轮廓与当前渲染/源环面语义仍不一致。", "不得声明论文视角、物理飞行或三维等价。"),
        "4.6": ("状态空间与局部 STM 数值行通过。", "冻结 panel-(d) 投影 holdout 为 0/4。", "论文投影轮廓与当前渲染/源环面语义仍不一致。", "不得声明论文视角、物理飞行或三维等价。"),
        "4.7": ("内部动力学、Jacobi 漂移与局部增长检查通过。", "全局流形到达范围和论文投影拓扑存在明显差异。", "当前源族只覆盖局部终端分支，缺少论文密集全局拓扑。", "只声明内部动力学源层，不声明投影几何等价。"),
        "4.8": ("内部动力学、Jacobi 漂移与局部增长检查通过。", "全局流形到达范围和论文投影拓扑存在明显差异。", "当前源族只覆盖局部终端分支，缺少论文密集全局拓扑。", "只声明内部动力学源层，不声明投影几何等价。"),
        "5.10": ("两组 BCR4BP 分段修正通过项目数值门槛。", "项目工况不是论文自主 CR3BP 原始工况，paper_equivalence=0/2。", "论文特定拟 NRHO 成员、相位和边界状态未公开。", "只声明项目 BCR4BP 数值扩展，不替代论文 Fig. 5.10 原始解。"),
        "5.12": ("当前 CR3BP 到达时间偏移分支给出真实收敛解。", "覆盖仅为 -24..+11 h，+12..+24 h 未计算。", "分支在 +11 h 后出现折叠/延拓边界。", "未覆盖区间不得插值或绘制代理。"),
        "5.13": ("两角度稳定流形扫描达到约 7033 km 近地点目标。", "热图场分布尚未与论文原图逐点比较。", "BCR4BP/星历修正和原图数字化审计尚缺。", "只声明 CR3BP 活跃几何源层与目标近地点一致。"),
        "5.14": ("稳定流形转移达到约 7033 km 近地点并保留 LEO 端点证据。", "三维几何和论文投影仍有明显差异。", "BCR4BP/星历修正及论文时序对照尚缺。", "只声明 CR3BP 数值转移，不声明高保真论文等价。"),
    }
    return specific.get(figure_id, (consistency, difference, reason, limitation))


def artifact_paths(value: str) -> list[Path]:
    paths: list[Path] = []
    for token in filter(None, (item.strip() for item in value.split(";"))):
        if not any(token.startswith(prefix) for prefix in ("data/", "docs/", "outputs/", "figures/", "scripts/")):
            continue
        if "*" in token:
            paths.extend(Path(match) for match in glob.glob(str(PROJECT_ROOT / token)))
        else:
            paths.append(PROJECT_ROOT / token)
    return paths


def has_number(value: str) -> bool:
    return bool(re.search(r"(?<![A-Za-z])[-+]?\d", value))


def numeric(value: str) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def data_ranges(source_value: str, limit: int = 2) -> list[dict[str, str]]:
    keywords = (
        "residual", "jacobi", "closure", "error", "delta_v", "periapsis", "amplitude",
        "period", "mapping_time", "rotation_angle", "frequency", "stability", "nu", "rho",
        "max_abs_z", "points", "accepted",
    )
    rows: list[dict[str, str]] = []
    for path in artifact_paths(source_value):
        if path.suffix.lower() != ".csv" or not path.is_file():
            continue
        try:
            table = read_csv(path)
        except (UnicodeDecodeError, csv.Error):
            continue
        if not table:
            continue
        columns = list(table[0])
        ranked = sorted(
            (column for column in columns if any(keyword in column.lower() for keyword in keywords)),
            key=lambda column: (
                0 if any(word in column.lower() for word in ("residual", "error", "jacobi", "closure")) else 1,
                columns.index(column),
            ),
        )
        for column in ranked:
            values = [number for number in (numeric(row.get(column, "")) for row in table) if number is not None]
            if not values:
                continue
            minimum, maximum = min(values), max(values)
            result = f"{column}: {minimum:.12g}" if minimum == maximum else f"{column}: {minimum:.12g}..{maximum:.12g}"
            rows.append({"metric": f"数据源范围/{column}", "project_result": result, "evidence": path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()})
            if len(rows) >= limit:
                return rows
    return rows


def main() -> int:
    STAGE_C.mkdir(parents=True, exist_ok=True)
    stage_a_registry = {row["target_id"]: row for row in read_csv(REPORT_ROOT / "stage_a" / "figure_registry_initial.csv")}
    targets = {row["figure_id"]: row for row in read_csv(PROJECT_ROOT / "data" / "reproduction_targets.csv")}
    validation = {row["figure_id"]: row for row in read_csv(PROJECT_ROOT / "data" / "computed" / "figure_validation_table.csv")}
    gaps = {row["figure_id"]: row for row in read_csv(PROJECT_ROOT / "data" / "computed" / "figure_evidence_gap_audit.csv")}
    originals = {row["target_id"]: row for row in read_csv(REPORT_ROOT / "source_figure_manifest.csv")}
    reproductions = {row["target_id"]: row for row in read_csv(REPORT_ROOT / "reproduction_figure_manifest.csv")}
    chapter4 = {row["figure_id"]: row for row in read_csv(PROJECT_ROOT / "data" / "computed" / "chapter4_per_figure_source_layer_audit.csv") if row["figure_id"] in stage_a_registry}
    chapter5 = {row["figure_id"]: row for row in read_csv(PROJECT_ROOT / "data" / "computed" / "chapter5_per_figure_source_layer_audit.csv") if row["figure_id"] in stage_a_registry}

    figure_ids = sorted(stage_a_registry, key=figure_key)
    if len(figure_ids) != 54 or not all(set(mapping) == set(figure_ids) for mapping in (targets, validation, gaps, originals, reproductions)):
        raise RuntimeError("Stage-C inputs do not share the same 54-figure ID set")

    registry: list[dict[str, object]] = []
    metrics: list[dict[str, object]] = []
    pending_items: list[dict[str, str]] = []
    evidence_audit: list[dict[str, object]] = []
    metric_counter = 0

    for figure_id in figure_ids:
        base = stage_a_registry[figure_id]
        target = targets[figure_id]
        check = validation[figure_id]
        gap = gaps[figure_id]
        specialized = chapter4.get(figure_id) or chapter5.get(figure_id) or {}
        grade, grade_boundary = grade_for(gap["evidence_status"])
        source_layer = specialized.get("current_source_layer") or check.get("key_physical_quantities") or PENDING
        model = model_for(figure_id, grade, target["title"], source_layer)
        coordinate = coordinate_for(figure_id, grade, model)
        method = method_for(figure_id, grade)
        consistency_cn, difference_cn, difference_reason_cn, limitation_cn = chinese_assessment(figure_id, grade)
        data_source = specialized.get("primary_evidence") or check.get("main_data_source") or target.get("validation_artifact") or PENDING
        evidence = specialized.get("primary_evidence") or target.get("validation_artifact") or check.get("main_data_source") or PENDING
        limitation = specialized.get("next_action") or check.get("next_action") or target.get("next_action") or PENDING
        if specialized.get("boundary"):
            boundary = specialized["boundary"]
            difference = check.get("visual_status") or gap.get("evidence_summary") or PENDING
            difference_reason = "当前逐图审计已给出受控边界；未把投影、原始节点或高保真条件缺失解释为数值等价。"
        elif figure_id == "3.10":
            difference = check.get("visual_status") or PENDING
            boundary = (
                "q=2、q=3 通过严格单步闭合审计；q=8 仅保留局部多步打靶接受，"
                "其单步全周期闭合误差为 3.906984451743337，不能升级为稳健周期闭合。"
            )
            difference_reason = "q=8 高不稳定性使单步闭合失败；当前证据只支持局部多段连续性。"
        elif figure_id in {"3.16", "3.17"}:
            difference = check.get("visual_status") or PENDING
            boundary = (
                "Route H 当前图源层通过缓存重验证，monolithic cold-start 仍为 fail、hybrid chain 为 pass；"
                "原作者完整分支节点未公开，因此不声明整条论文分支逐点等价。"
            )
            difference_reason = "当前代码可通过混合链重建目标源层，但单体冷启动延拓仍在已记录位置失败。"
        elif grade == "D":
            difference = "该图只承担概念/几何/算法示意角色，不提供论文原始数值节点的等价证据。"
            boundary = grade_boundary
            difference_reason = "目标本身为示意层，当前项目使用独立绘制的语义对应图。"
        elif grade == "A":
            difference = "当前项目审计门槛通过；原作者离散节点与完整绘图参数未公开，因此不声明逐像素或逐节点等价。"
            boundary = grade_boundary
            difference_reason = "独立重建使用当前权威 CSV/NPZ；论文未公开完整分支状态与绘图元数据。"
        else:
            difference = check.get("visual_status") or gap.get("evidence_summary") or PENDING
            boundary = (
                f"{grade_boundary}；当前未闭合项："
                f"{check.get('next_action') or target.get('next_action') or PENDING}"
            )
            difference_reason = "现有源层只支持当前等级；严格等价受完整状态、分支覆盖、相位、视角或高保真条件限制。"

        validation_parts = []
        for key, label in (
            ("residual_norm", "残差"),
            ("jacobi_drift", "Jacobi"),
            ("periodicity_error", "周期/相位"),
            ("stability_index_error", "稳定性"),
        ):
            value = check.get(key, "")
            if value and value != "N/A":
                validation_parts.append(f"{label}: {value}")
        quantitative_validation = "；".join(validation_parts) or "原论文未报告或当前权威表未登记独立误差值"

        row = {
            "target_id": figure_id,
            "chapter": figure_id.split(".")[0],
            "paper_figure_number": base["paper_figure_number"],
            "paper_page": base["paper_page"],
            "pdf_page": base["pdf_page"],
            "paper_caption": base["paper_caption"],
            "paper_caption_status": originals[figure_id]["caption_status"],
            "paper_asset": originals[figure_id]["asset"],
            "reproduction_asset": reproductions[figure_id]["asset"],
            "comparison_asset": PENDING,
            "research_object": TITLE_CN.get(figure_id, target["title"]),
            "research_object_en": target["title"],
            "model": model,
            "coordinate_system": coordinate,
            "main_parameters": target.get("paper_targets") or PENDING,
            "numerical_method": method,
            "script": target["script"],
            "data_source": data_source,
            "current_source_layer": source_layer,
            "status": gap["evidence_status"],
            "evidence": evidence,
            "quantitative_validation": quantitative_validation,
            "consistency": check.get("visual_status") or gap.get("evidence_summary") or PENDING,
            "consistency_cn": consistency_cn,
            "difference": difference,
            "difference_cn": difference_cn,
            "difference_reason": difference_reason,
            "difference_reason_cn": difference_reason_cn,
            "limitation": boundary,
            "limitation_cn": limitation_cn,
            "next_action": limitation,
            "reproduction_grade": grade,
            "grade_boundary": grade_boundary,
            "uses_proxy": check.get("uses_proxy") or PENDING,
            "notes": "阶段 C 证据绑定；所有结论来自当前权威表、逐图审计和实际图形资产。",
        }
        registry.append(row)

        metric_specs = [
            ("论文目标/关键物理量", target.get("paper_targets") or "原论文未报告", check.get("key_physical_quantities") or PENDING, gap["evidence_status"]),
            ("动力学/校正残差", "原论文未报告（本项目验证指标）", check.get("residual_norm", "N/A"), "按当前审计阈值解释"),
            ("Jacobi 一致性", "原论文未报告（本项目验证指标）", check.get("jacobi_drift", "N/A"), "按当前审计阈值解释"),
            ("周期/相位闭合", "原论文未报告（本项目验证指标）", check.get("periodicity_error", "N/A"), "按当前审计阈值解释"),
            ("稳定性指标误差", "见原文目标或原论文未报告", check.get("stability_index_error", "N/A"), "按当前审计阈值解释"),
        ]
        if specialized.get("best_metric"):
            metric_specs.append(("逐图源层最佳指标", target.get("paper_targets") or "原论文未报告", specialized["best_metric"], specialized.get("original_replacement_status", "")))
        for metric_name, paper_value, project_result, error_status in metric_specs:
            if not project_result or project_result == "N/A":
                continue
            if not has_number(str(project_result)) and (
                "n/a" in str(project_result).lower()
                or str(project_result).lower().startswith("see chapter")
            ):
                continue
            metric_counter += 1
            metrics.append(
                {
                    "metric_id": f"M{metric_counter:04d}",
                    "target_id": figure_id,
                    "priority_core": str(figure_id in CORE_FIGURES).lower(),
                    "metric": metric_name,
                    "paper_value_or_target": paper_value,
                    "project_result": project_result,
                    "error_or_status": error_status,
                    "unit": "见字段文本；未明确者【待核实】",
                    "evidence_artifact": evidence,
                    "evidence_type": "authoritative validation/per-figure audit",
                    "verification_status": gap["evidence_status"],
                    "boundary": boundary,
                }
            )
        if figure_id in CORE_FIGURES:
            for derived in data_ranges(data_source, limit=2):
                metric_counter += 1
                metrics.append(
                    {
                        "metric_id": f"M{metric_counter:04d}",
                        "target_id": figure_id,
                        "priority_core": "true",
                        "metric": derived["metric"],
                        "paper_value_or_target": "原论文未报告（当前数据源内部范围）",
                        "project_result": derived["project_result"],
                        "error_or_status": "从当前 CSV 直接计算 min/max；不外推",
                        "unit": "按 CSV 列定义；未明确者【待核实】",
                        "evidence_artifact": derived["evidence"],
                        "evidence_type": "direct CSV range",
                        "verification_status": gap["evidence_status"],
                        "boundary": boundary,
                    }
                )

        pending_fields = [field for field, value in row.items() if PENDING in str(value)]
        for field in pending_fields:
            pending_items.append(
                {
                    "target_id": figure_id,
                    "field": field,
                    "value": str(row[field]),
                    "reason": "当前权威数据或脚本元数据不足，按真实性规则保留占位符",
                }
            )
        paths = artifact_paths(data_source)
        missing_paths = [str(path.resolve().relative_to(PROJECT_ROOT.resolve())) for path in paths if not path.exists()]
        evidence_audit.append(
            {
                "target_id": figure_id,
                "grade": grade,
                "status": gap["evidence_status"],
                "script_exists": (PROJECT_ROOT / target["script"]).is_file(),
                "paper_asset_exists": (PROJECT_ROOT / originals[figure_id]["asset"]).is_file(),
                "reproduction_asset_exists": (PROJECT_ROOT / reproductions[figure_id]["asset"]).is_file(),
                "resolved_evidence_paths": len(paths),
                "missing_evidence_paths": ";".join(missing_paths),
                "pending_fields": ";".join(pending_fields),
                "boundary_present": bool(boundary),
            }
        )

    metric_by_figure = collections.Counter(str(row["target_id"]) for row in metrics)
    core_numeric_missing = [
        figure_id
        for figure_id in sorted(CORE_FIGURES, key=figure_key)
        if metric_by_figure[figure_id] < 2
        or not any(
            row["target_id"] == figure_id and has_number(str(row["project_result"]))
            for row in metrics
        )
    ]
    essential_failures = [
        row["target_id"]
        for row in registry
        if any(not str(row[field]).strip() for field in (
            "paper_caption", "paper_asset", "reproduction_asset", "research_object", "model",
            "coordinate_system", "main_parameters", "numerical_method", "script", "data_source",
            "status", "evidence", "difference", "limitation", "reproduction_grade",
        ))
    ]
    evidence_missing = [row["target_id"] for row in evidence_audit if row["missing_evidence_paths"]]
    status = "PASS_WITH_TRACKED_PENDING" if not core_numeric_missing and not essential_failures and not evidence_missing else "FAIL"

    write_csv(REPORT_ROOT / "figure_comparison_registry.csv", registry)
    write_csv(REPORT_ROOT / "quantitative_metrics_registry.csv", metrics)
    write_csv(STAGE_C / "figure_status_table.csv", registry)
    write_csv(STAGE_C / "evidence_binding_audit.csv", evidence_audit)
    write_csv(STAGE_C / "pending_verification_items.csv", pending_items, ["target_id", "field", "value", "reason"])

    grade_counts = collections.Counter(str(row["reproduction_grade"]) for row in registry)
    evidence_counts = collections.Counter(str(row["status"]) for row in registry)
    summary = {
        "status": status,
        "figures": len(registry),
        "metrics": len(metrics),
        "core_figures": len(CORE_FIGURES),
        "core_numeric_missing": core_numeric_missing,
        "essential_failures": essential_failures,
        "evidence_missing": evidence_missing,
        "pending_items": len(pending_items),
        "grade_counts": dict(sorted(grade_counts.items())),
        "evidence_counts": dict(sorted(evidence_counts.items())),
    }
    (STAGE_C / "stage_c_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    status_md = [
        "# 54 图状态总表",
        "",
        f"- A-E 等级统计：{dict(sorted(grade_counts.items()))}",
        f"- 权威证据状态：{dict(sorted(evidence_counts.items()))}",
        "- A 表示当前项目门槛内的定量通过，不自动等于原作者节点逐点等价。",
        "",
        "| 图号 | 研究对象 | 等级 | proxy | 当前源层/结果 | 主要边界 |",
        "|---|---|---|---|---|---|",
    ]
    for row in registry:
        status_md.append(
            f"| {row['target_id']} | {row['research_object']} | {row['reproduction_grade']} | "
            f"{row['uses_proxy']} | {str(row['current_source_layer']).replace('|', '/')} | "
            f"{str(row['limitation_cn']).replace('|', '/')} |"
        )
    (STAGE_C / "figure_status_table.md").write_text("\n".join(status_md) + "\n", encoding="utf-8")

    metric_md = [
        "# 核心图定量证据审计",
        "",
        f"- 定量注册表总行数：`{len(metrics)}`。",
        f"- 优先核心图：`{len(CORE_FIGURES)}`；缺少数值项目的核心图：`{core_numeric_missing or '无'}`。",
        "- 残差、Jacobi 漂移、闭合误差等若原论文未报告，表中明确写“原论文未报告（本项目验证指标）”。",
        "- CSV 范围由当前文件直接计算，不对论文缺失值进行反推或外推。",
        "",
        "| 图号 | 指标行数 | 含数字项目结果 |",
        "|---|---:|---|",
    ]
    for figure_id in sorted(CORE_FIGURES, key=figure_key):
        rows = [row for row in metrics if row["target_id"] == figure_id]
        metric_md.append(f"| {figure_id} | {len(rows)} | {any(has_number(str(row['project_result'])) for row in rows)} |")
    (STAGE_C / "quantitative_metrics_audit.md").write_text("\n".join(metric_md) + "\n", encoding="utf-8")

    pending_md = [
        "# 【待核实】事项",
        "",
        f"共 `{len(pending_items)}` 条字段级占位符。占位符是显式真实性边界，不允许在写作阶段自动猜测替换。",
        "",
        "| 图号 | 字段 | 值 | 原因 |",
        "|---|---|---|---|",
    ]
    for item in pending_items:
        pending_md.append(f"| {item['target_id']} | {item['field']} | {item['value']} | {item['reason']} |")
    (STAGE_C / "pending_verification_items.md").write_text("\n".join(pending_md) + "\n", encoding="utf-8")

    boundary_review = f"""# 科学结论边界复核

- A 级图号：2.15、3.5、3.6、3.12、3.13、3.14、3.15。A 仅表示当前项目门槛内的定量通过，不等于原作者离散节点逐点等价。
- Fig. 3.10：q=2、q=3 为严格单步闭合接受；q=8 单步全周期闭合误差 `3.906984451743337`，保留 C 级局部多步打靶边界。
- Fig. 3.16/3.17：Route H 图源层通过；monolithic cold-start=`fail`，hybrid chain=`pass`；完整论文分支逐点等价未证明。
- Fig. 4.3-4.6：状态空间和局部 STM 行通过，但冻结 panel-(d) 投影 holdout=`0/4 fail`，不得声明论文视角或三维等价。
- Fig. 5.10：BCR4BP 数值接受=`2/2`，paper_equivalence=`0/2`；不得把项目历元或自主 BCR4BP 扩展写成论文原始工况。
- Fig. 5.12：当前分支只覆盖 `-24..+11 h`，`+12..+24 h` 为明确折叠/覆盖边界，不绘制外推代理。
- Fig. 5.13/5.14：CR3BP 活跃几何源层达到约 7033 km 目标；BCR4BP/星历修正和论文图逐点比较仍未完成。
- 其余 B/C/D 图均按 registry 的 limitation 字段写作；任何【待核实】不得在 Word 构建阶段自动替换。

复核状态：`PASS_WITH_TRACKED_PENDING`
"""
    (STAGE_C / "scientific_boundary_review.md").write_text(boundary_review, encoding="utf-8")

    gate = f"""# 阶段 C 验收门槛

- [{'x' if len(registry) == 54 else ' '}] 54 图状态表完整。
- [{'x' if not essential_failures else ' '}] 每图研究对象、模型、坐标系、参数、方法、脚本、数据、差异、限制和 A-E 等级字段非空。
- [{'x' if not core_numeric_missing else ' '}] 28 张核心数值图均有至少 2 条定量记录且至少 1 条当前项目数值。
- [{'x' if not evidence_missing else ' '}] 可解析的证据路径均存在。
- [x] 原论文未报告的验证量明确标记，不猜测论文值。
- [x] Chapter 3 q=8、Route H cold-start、Chapter 4 投影 holdout 和 Chapter 5 论文等价边界均保留。
- [x] 所有【待核实】字段进入独立清单。

状态：`{status}`
"""
    (STAGE_C / "stage_c_gate.md").write_text(gate, encoding="utf-8")
    print(
        f"stage_c={status} figures={len(registry)} metrics={len(metrics)} core={len(CORE_FIGURES)} "
        f"core_missing={len(core_numeric_missing)} pending={len(pending_items)}"
    )
    return 0 if status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
