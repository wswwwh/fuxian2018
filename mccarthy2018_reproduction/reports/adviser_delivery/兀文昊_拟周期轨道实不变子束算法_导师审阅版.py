# -*- coding: utf-8 -*-
"""
拟周期轨道实不变子束算法（导师审阅单文件版）
================================================

作者：兀文昊
整理日期：2026-07-21

一、代码用途
------------
本文件用于计算离散拟周期余循环（quasi-periodic cocycle）的实不变子束，
对应的基本方程为

    A(theta) E(theta) = E(theta + rho) R(theta)

其中：

1. theta 是环面上的相位；
2. rho 是一次映射对应的相位平移量；
3. A(theta) 是相位 theta 处的局部线性映射矩阵；
4. E(theta) 的列向量张成待求的不变子空间；
5. R(theta) 是不变子空间内部的局部降维映射。

代码特别区分“逐点矩阵特征向量”和“满足相位平移关系的不变子束”。
当目标谱为复共轭对时，代码保留其二维实不变子空间，不把它错误地
投影成一维实方向。

二、文件内容
------------
本文件把原工程中用于导师审阅的核心数值逻辑整理为一个独立文件，包括：

1. 周期 Fourier 插值矩阵；
2. 离散余循环整体算子的组装；
3. 子空间正交化、相位连续化和主角度计算；
4. 传统逐点特征分解基线方法；
5. 有序局部实 Schur 子空间跟踪方法；
6. 平移 QR/SVD 余循环迭代方法；
7. 不变性残差、相位连续性和跨分辨率误差指标；
8. 可直接运行的两个合成算例与自动自检。

三、输入与输出
--------------
主要输入：

    cocycle : 形状为 (N, d, d) 的实矩阵数组
    phases  : 形状为 (N,) 的相位节点，N 必须为不小于 3 的奇数
    rho     : 相位平移量

主要输出为 InvariantBundleResult，其中保存：

    bases                         子束在各相位节点处的正交基
    local_reduced_maps            子空间内部的局部降维映射
    invariance_residuals          归一化余循环不变性残差
    phase_principal_angles_deg    相邻相位子空间主角
    selected_spectrum             选中的谱信息
    converged / iterations        收敛状态与迭代次数
    classification                一维实子束或二维实共轭子空间分类

四、运行环境
------------
依赖：Python 3.10 及以上、NumPy。

推荐运行命令：

    D:\miniconda3\envs\cislunar\python.exe 兀文昊_拟周期轨道实不变子束算法_导师审阅版.py

直接运行本文件会执行一维实双曲子束和二维复共轭子空间两个合成算例，
并在全部自检通过后输出“全部自检通过”。

五、说明与边界
--------------
这是便于导师阅读和运行的核心算法单文件，不包含 54 张论文图的批量生成、
报告排版、数据审计及持续集成脚本。文件末尾的合成算例用于检查数学语义和
程序行为，不替代真实 CR3BP 轨道数据上的研究结论。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np


# 稳定分支与不稳定分支采用同一套接口。
Branch = Literal["stable", "unstable"]


@dataclass(frozen=True)
class InvariantBundleResult:
    """保存一维或二维实不变子束的完整、可审计计算结果。"""

    method: str
    branch: Branch
    bundle_dimension: int
    bases: np.ndarray
    local_reduced_maps: np.ndarray
    invariance_residuals: np.ndarray
    phase_principal_angles_deg: np.ndarray
    selected_spectrum: np.ndarray
    relative_imaginary: float
    selection_residual: float
    iterations: int
    converged: bool
    convergence_history: np.ndarray
    classification: str
    sign_or_orientation_flips: int

    @property
    def max_invariance_residual(self) -> float:
        """所有相位节点上的最大归一化不变性残差。"""

        return float(np.max(self.invariance_residuals))

    @property
    def mean_invariance_residual(self) -> float:
        """所有相位节点上的平均归一化不变性残差。"""

        return float(np.mean(self.invariance_residuals))

    @property
    def max_phase_principal_angle_deg(self) -> float:
        """相邻相位子空间之间的最大主角，单位为度。"""

        return float(np.max(self.phase_principal_angles_deg, initial=0.0))

    @property
    def mean_phase_principal_angle_deg(self) -> float:
        """相邻相位子空间之间的平均主角，单位为度。"""

        return float(np.mean(self.phase_principal_angles_deg))


# ---------------------------------------------------------------------------
# 第一部分：输入检查与周期 Fourier 插值
# ---------------------------------------------------------------------------


def _validate_inputs(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
) -> tuple[np.ndarray, np.ndarray, float]:
    """检查余循环矩阵、相位节点和相位平移量是否满足算法要求。"""

    matrices = np.asarray(cocycle, dtype=float)
    nodes = np.asarray(phases, dtype=float)
    rotation = float(rho)

    if matrices.ndim != 3 or matrices.shape[1] != matrices.shape[2]:
        raise ValueError("cocycle 必须具有形状 (样本数, 状态维数, 状态维数)")
    if nodes.shape != (matrices.shape[0],):
        raise ValueError("phases 的长度必须与余循环样本数一致")
    if matrices.shape[0] < 3 or matrices.shape[0] % 2 == 0:
        raise ValueError("样本数必须为不小于 3 的奇数")
    if not np.all(np.isfinite(matrices)) or not np.all(np.isfinite(nodes)):
        raise ValueError("cocycle 和 phases 中不能包含 NaN 或无穷值")
    if not np.isfinite(rotation):
        raise ValueError("rho 必须是有限实数")

    # 不可逆局部矩阵会破坏稳定分支中的反向求解，因此在入口处统一拒绝。
    minimum_singular_value = np.min(
        np.linalg.svd(matrices, compute_uv=False)
    )
    if minimum_singular_value <= np.finfo(float).tiny:
        raise ValueError("每个余循环矩阵都必须可逆")

    # 相位按 2*pi 取模后仍应互不相同。
    wrapped = np.mod(nodes, 2.0 * np.pi)
    distances = np.abs(wrapped[:, None] - wrapped[None, :])
    distances += np.eye(nodes.size) * 2.0 * np.pi
    if float(np.min(distances)) < 1.0e-12:
        raise ValueError("phases 在模 2*pi 意义下必须互不相同")

    return matrices, nodes, rotation


def _trigonometric_interpolation_matrix(
    source_phases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """构造奇数等距节点上的周期三角插值权重矩阵。

    对 N 个奇数节点，使用从 -((N-1)/2) 到 +(N-1)/2 的 Fourier 模态。
    返回矩阵 W 满足：

        values_at_evaluation = W @ values_at_source
    """

    source = np.asarray(source_phases, dtype=float)
    evaluation = np.asarray(evaluation_phases, dtype=float)

    if source.ndim != 1 or evaluation.ndim != 1:
        raise ValueError("相位数组必须是一维数组")

    sample_count = source.size
    if sample_count < 3 or sample_count % 2 == 0:
        raise ValueError("周期三角插值要求不小于 3 的奇数样本数")

    harmonic_count = (sample_count - 1) // 2
    matrix = np.empty((evaluation.size, sample_count), dtype=float)

    for index, phase in enumerate(evaluation):
        delta = phase - source
        row = np.ones(sample_count, dtype=float)
        for harmonic in range(1, harmonic_count + 1):
            row += 2.0 * np.cos(harmonic * delta)
        matrix[index, :] = row / sample_count

    return matrix


def periodic_interpolation_matrix(
    source_phases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """返回余循环计算所用的周期 Fourier 插值矩阵。"""

    return _trigonometric_interpolation_matrix(
        source_phases,
        evaluation_phases,
    )


def assemble_discrete_cocycle_operator(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
) -> np.ndarray:
    """组装定义在全部相位节点上的离散余循环整体算子。

    先用块对角矩阵在每个节点施加局部映射 A(theta_i)，再用 Fourier
    插值把 theta_i + rho 上的向量场映回基础相位网格。整体算子维数为
    (N*d) × (N*d)。
    """

    matrices, nodes, rotation = _validate_inputs(cocycle, phases, rho)
    samples, dimension, _ = matrices.shape

    shifted_to_base = periodic_interpolation_matrix(
        nodes + rotation,
        nodes,
    )
    block_diagonal = np.zeros(
        (samples * dimension, samples * dimension),
        dtype=float,
    )

    for index, matrix in enumerate(matrices):
        start = index * dimension
        block_diagonal[
            start : start + dimension,
            start : start + dimension,
        ] = matrix

    return (
        np.kron(shifted_to_base, np.eye(dimension))
        @ block_diagonal
    )


# ---------------------------------------------------------------------------
# 第二部分：子空间正交化、相位对齐和误差度量
# ---------------------------------------------------------------------------


def _orthonormalize(values: np.ndarray) -> np.ndarray:
    """逐相位节点对基向量做薄 QR 分解，并固定 QR 对角符号。"""

    vectors = np.asarray(values, dtype=float)
    if vectors.ndim != 3:
        raise ValueError(
            "子束基必须具有形状 (样本数, 状态维数, 子束维数)"
        )

    result = np.empty_like(vectors)
    for index, basis in enumerate(vectors):
        q, r = np.linalg.qr(basis, mode="reduced")

        # 若 R 的对角元素接近零，说明局部基发生秩亏。
        if (
            q.shape[1] != vectors.shape[2]
            or np.min(np.abs(np.diag(r))) < 1.0e-14
        ):
            raise RuntimeError(
                f"相位索引 {index} 处的子束基发生秩亏"
            )

        # 统一 QR 的符号约定，使相同子空间的表示尽量确定。
        diagonal_sign = np.sign(np.diag(r))
        diagonal_sign[diagonal_sign == 0.0] = 1.0
        result[index] = q * diagonal_sign

    return result


def _principal_angles_deg(
    left: np.ndarray,
    right: np.ndarray,
) -> np.ndarray:
    """计算两个正交子空间之间的全部主角，单位为度。"""

    singular_values = np.linalg.svd(
        left.T @ right,
        compute_uv=False,
    )
    singular_values = np.clip(singular_values, -1.0, 1.0)
    return np.degrees(np.arccos(singular_values))


def _align_to_reference(
    bases: np.ndarray,
    references: np.ndarray,
) -> tuple[np.ndarray, int]:
    """把每个局部基对齐到对应参考基，并统计符号或定向翻转次数。"""

    aligned = np.asarray(bases, dtype=float).copy()
    flips = 0

    for index in range(aligned.shape[0]):
        if aligned.shape[2] == 1:
            # 一维子束只需检查方向符号。
            overlap = float(
                aligned[index, :, 0]
                @ references[index, :, 0]
            )
            if overlap < 0.0:
                aligned[index, :, 0] *= -1.0
                flips += 1
        else:
            # 二维子空间使用正交 Procrustes 对齐内部基框架。
            u, _, vt = np.linalg.svd(
                aligned[index].T @ references[index]
            )
            rotation = u @ vt
            if np.linalg.det(rotation) < 0.0:
                flips += 1
            aligned[index] = aligned[index] @ rotation

    return aligned, flips


def align_bundle_phase(
    bases: np.ndarray,
    phases: np.ndarray,
) -> tuple[np.ndarray, int]:
    """沿相位递增方向连续化一维符号或二维子空间内部框架。"""

    values = _orthonormalize(bases)
    nodes = np.asarray(phases, dtype=float)
    if nodes.shape != (values.shape[0],):
        raise ValueError("phases 的长度必须与子束样本数一致")

    order = np.argsort(np.mod(nodes, 2.0 * np.pi))
    aligned = values.copy()
    flips = 0

    for position in range(1, order.size):
        current = order[position]
        previous = order[position - 1]
        updated, count = _align_to_reference(
            aligned[current : current + 1],
            aligned[previous : previous + 1],
        )
        aligned[current] = updated[0]
        flips += count

    # 最后检查周期首尾是否存在定向不一致。
    first = order[0]
    last = order[-1]
    if values.shape[2] == 1:
        flips += int(
            float(
                aligned[first, :, 0]
                @ aligned[last, :, 0]
            )
            < 0.0
        )
    else:
        flips += int(
            np.linalg.det(aligned[last].T @ aligned[first]) < 0.0
        )

    return aligned, flips


def phase_principal_angles_deg(
    bases: np.ndarray,
    phases: np.ndarray,
) -> np.ndarray:
    """计算周期相位网格上每对相邻子空间的最大主角。"""

    values = _orthonormalize(bases)
    order = np.argsort(
        np.mod(np.asarray(phases, dtype=float), 2.0 * np.pi)
    )
    angles = np.empty(order.size, dtype=float)

    for position, current in enumerate(order):
        following = order[(position + 1) % order.size]
        angles[position] = float(
            np.max(
                _principal_angles_deg(
                    values[current],
                    values[following],
                )
            )
        )

    return angles


def bundle_invariance_metrics(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    bases: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """计算局部降维映射和归一化余循环不变性残差。

    对每个相位节点，先计算 transported = A_i E_i，再把 E(theta_i+rho)
    插值到目标相位。局部降维映射和缺陷分别为

        R_i = E_shifted_i.T @ transported
        defect_i = transported - E_shifted_i @ R_i

    返回的 residual_i 是 defect_i 的 Frobenius 范数除以 transported
    的 Frobenius 范数。
    """

    matrices, nodes, rotation = _validate_inputs(
        cocycle,
        phases,
        rho,
    )
    values = _orthonormalize(bases)
    if values.shape[:2] != matrices.shape[:2]:
        raise ValueError("子束基的样本数或状态维数与 cocycle 不一致")

    base_to_shifted = periodic_interpolation_matrix(
        nodes,
        nodes + rotation,
    )
    shifted = np.einsum(
        "ij,jdk->idk",
        base_to_shifted,
        values,
    )
    shifted = _orthonormalize(shifted)

    rank = values.shape[2]
    reduced_maps = np.empty(
        (matrices.shape[0], rank, rank),
        dtype=float,
    )
    residuals = np.empty(matrices.shape[0], dtype=float)

    for index, matrix in enumerate(matrices):
        transported = matrix @ values[index]
        reduced_maps[index] = shifted[index].T @ transported
        defect = (
            transported
            - shifted[index] @ reduced_maps[index]
        )
        denominator = max(
            np.linalg.norm(transported, ord="fro"),
            np.finfo(float).tiny,
        )
        residuals[index] = float(
            np.linalg.norm(defect, ord="fro") / denominator
        )

    return reduced_maps, residuals


# ---------------------------------------------------------------------------
# 第三部分：传统逐点特征分解基线
# ---------------------------------------------------------------------------


def _branch_candidates(
    eigenvalues: np.ndarray,
    branch: Branch,
    hyperbolic_tolerance: float,
) -> np.ndarray:
    """按模长筛选稳定或不稳定的双曲谱候选。"""

    magnitudes = np.abs(eigenvalues)

    if branch == "unstable":
        candidates = np.flatnonzero(
            magnitudes > 1.0 + hyperbolic_tolerance
        )
    elif branch == "stable":
        candidates = np.flatnonzero(
            magnitudes < 1.0 - hyperbolic_tolerance
        )
    else:
        raise ValueError("branch 必须为 'stable' 或 'unstable'")

    if candidates.size == 0:
        raise RuntimeError(
            f"余循环算子中不存在 {branch} 双曲谱候选"
        )

    return candidates


def traditional_pointwise_eigen_bundle(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    hyperbolic_tolerance: float = 1.0e-3,
) -> InvariantBundleResult:
    """计算传统逐点特征向量基线。

    该方法故意保留一个常见问题：它在每个局部矩阵上独立选择特征向量，
    并在选中复向量时只取其实部。该结果可作为对照，但不保证满足跨相位
    的余循环不变方程。classification 和 relative_imaginary 会明确记录
    复向量被压成一维实方向的情况。
    """

    matrices, nodes, rotation = _validate_inputs(
        cocycle,
        phases,
        rho,
    )
    samples, dimension, _ = matrices.shape

    bases = np.empty((samples, dimension, 1), dtype=float)
    spectrum = np.empty(samples, dtype=complex)
    eigenpair_residuals = np.empty(samples, dtype=float)
    relative_imaginary = np.empty(samples, dtype=float)

    for index, matrix in enumerate(matrices):
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        candidates = _branch_candidates(
            eigenvalues,
            branch,
            hyperbolic_tolerance,
        )

        if branch == "unstable":
            selected = int(
                candidates[
                    np.argmax(np.abs(eigenvalues[candidates]))
                ]
            )
        else:
            selected = int(
                candidates[
                    np.argmin(np.abs(eigenvalues[candidates]))
                ]
            )

        eigenvalue = complex(eigenvalues[selected])
        eigenvector = eigenvectors[:, selected]

        # 传统基线把复特征向量投影到实部；实部过小时才退回虚部。
        direction = np.real(eigenvector)
        if np.linalg.norm(direction) < 1.0e-13:
            direction = np.imag(eigenvector)
        if np.linalg.norm(direction) < 1.0e-13:
            raise RuntimeError(
                f"相位索引 {index} 处选中的逐点特征向量消失"
            )

        bases[index, :, 0] = (
            direction / np.linalg.norm(direction)
        )
        spectrum[index] = eigenvalue
        relative_imaginary[index] = (
            abs(eigenvalue.imag)
            / max(abs(eigenvalue), np.finfo(float).tiny)
        )

        numerator = np.linalg.norm(
            matrix @ eigenvector - eigenvalue * eigenvector
        )
        denominator = max(
            np.linalg.norm(matrix @ eigenvector),
            np.finfo(float).tiny,
        )
        eigenpair_residuals[index] = float(
            numerator / denominator
        )

    bases, flips = align_bundle_phase(bases, nodes)
    reduced_maps, residuals = bundle_invariance_metrics(
        matrices,
        nodes,
        rotation,
        bases,
    )

    complex_misuse = bool(
        np.max(relative_imaginary) > 1.0e-10
    )

    return InvariantBundleResult(
        method="traditional_pointwise_eigendecomposition",
        branch=branch,
        bundle_dimension=1,
        bases=bases,
        local_reduced_maps=reduced_maps,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(
            bases,
            nodes,
        ),
        selected_spectrum=spectrum,
        relative_imaginary=float(np.max(relative_imaginary)),
        selection_residual=float(np.max(eigenpair_residuals)),
        iterations=0,
        converged=not complex_misuse,
        convergence_history=np.empty(0, dtype=float),
        classification=(
            "complex_vector_projected_to_real_1d_failure"
            if complex_misuse
            else "real_1d_pointwise_candidate"
        ),
        sign_or_orientation_flips=flips,
    )


# ---------------------------------------------------------------------------
# 第四部分：有序局部实 Schur 子空间跟踪
# ---------------------------------------------------------------------------


def _target_operator_eigenvalue(
    eigenvalues: np.ndarray,
    *,
    branch: Branch,
    hyperbolic_tolerance: float,
) -> complex:
    """从整体算子谱中选取最靠近实轴的目标双曲特征值。"""

    candidates = _branch_candidates(
        eigenvalues,
        branch,
        hyperbolic_tolerance,
    )
    values = eigenvalues[candidates]

    relative_imaginary = (
        np.abs(np.imag(values))
        / np.maximum(np.abs(values), np.finfo(float).tiny)
    )
    minimum = float(np.min(relative_imaginary))
    near_real_axis = np.flatnonzero(
        relative_imaginary <= minimum + 1.0e-12
    )

    if branch == "unstable":
        chosen = near_real_axis[
            np.argmax(np.abs(values[near_real_axis]))
        ]
    else:
        chosen = near_real_axis[
            np.argmin(np.abs(values[near_real_axis]))
        ]

    return complex(values[chosen])


def real_schur_bundle_tracking(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    hyperbolic_tolerance: float = 1.0e-3,
    real_relative_imaginary_tolerance: float = 1.0e-10,
    refinement_iterations: int = 0,
) -> InvariantBundleResult:
    """选择并跟踪有序的局部实 Schur 不变子空间。

    实现首先在离散余循环整体算子上选择最靠近实轴的目标双曲谱块。
    若目标特征值在容差内为实数，则返回一维实子束；若目标属于真正的
    复共轭对，则用特征向量的实部和虚部构造二维实不变子空间。

    这里的“实 Schur”指选定不变谱块的局部实正交表示。实现保留二维
    共轭子空间的真实维数，不把二维结果重新命名为一维方向。
    """

    if real_relative_imaginary_tolerance <= 0.0:
        raise ValueError(
            "real_relative_imaginary_tolerance 必须为正数"
        )
    if refinement_iterations < 0:
        raise ValueError("refinement_iterations 不能为负数")

    matrices, nodes, rotation = _validate_inputs(
        cocycle,
        phases,
        rho,
    )
    operator = assemble_discrete_cocycle_operator(
        matrices,
        nodes,
        rotation,
    )

    eigenvalues, eigenvectors = np.linalg.eig(operator)
    target = _target_operator_eigenvalue(
        eigenvalues,
        branch=branch,
        hyperbolic_tolerance=hyperbolic_tolerance,
    )

    relative_imaginary = (
        abs(target.imag)
        / max(abs(target), np.finfo(float).tiny)
    )
    target_is_real = (
        relative_imaginary
        <= real_relative_imaginary_tolerance
    )

    selected_index = int(
        np.argmin(np.abs(eigenvalues - target))
    )
    selected_vector = eigenvectors[:, selected_index]

    if target_is_real:
        candidate = np.real(selected_vector)[:, None]
        if np.linalg.norm(candidate) < 1.0e-13:
            candidate = np.imag(selected_vector)[:, None]
        selected_dimension = 1
    else:
        # 一个复特征向量的实部和虚部共同张成二维实不变子空间。
        candidate = np.column_stack(
            (
                np.real(selected_vector),
                np.imag(selected_vector),
            )
        )
        selected_dimension = 2

    selected_vectors, factor = np.linalg.qr(
        candidate,
        mode="reduced",
    )
    if (
        selected_vectors.shape[1] != selected_dimension
        or np.min(np.abs(np.diag(factor))) < 1.0e-13
    ):
        raise RuntimeError(
            f"目标谱 {target} 对应的实 Schur 块发生秩亏"
        )

    reduced_operator = (
        selected_vectors.T
        @ operator
        @ selected_vectors
    )
    schur_defect = (
        operator @ selected_vectors
        - selected_vectors @ reduced_operator
    )
    schur_residual = float(
        np.linalg.norm(schur_defect, ord="fro")
        / max(
            np.linalg.norm(
                operator @ selected_vectors,
                ord="fro",
            ),
            np.finfo(float).tiny,
        )
    )

    samples, dimension, _ = matrices.shape
    bases = selected_vectors.reshape(
        samples,
        dimension,
        selected_dimension,
    )
    bases = _orthonormalize(bases)
    bases, flips = align_bundle_phase(bases, nodes)

    history: list[float] = []
    if refinement_iterations:
        bases, history, extra_flips = _graph_transform(
            matrices,
            nodes,
            rotation,
            bases,
            branch=branch,
            max_iterations=refinement_iterations,
            tolerance=0.0,
        )
        flips += extra_flips

    local_maps, residuals = bundle_invariance_metrics(
        matrices,
        nodes,
        rotation,
        bases,
    )
    selected_spectrum = np.linalg.eigvals(reduced_operator)

    return InvariantBundleResult(
        method="ordered_real_schur_tracking",
        branch=branch,
        bundle_dimension=selected_dimension,
        bases=bases,
        local_reduced_maps=local_maps,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(
            bases,
            nodes,
        ),
        selected_spectrum=selected_spectrum,
        relative_imaginary=float(relative_imaginary),
        selection_residual=schur_residual,
        iterations=refinement_iterations,
        converged=bool(schur_residual < 1.0e-8),
        convergence_history=np.asarray(history, dtype=float),
        classification=(
            "real_1d_hyperbolic_bundle"
            if selected_dimension == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        sign_or_orientation_flips=flips,
    )


# ---------------------------------------------------------------------------
# 第五部分：平移 QR/SVD 余循环迭代
# ---------------------------------------------------------------------------


def _initial_svd_bases(
    matrices: np.ndarray,
    rank: int,
    branch: Branch,
) -> np.ndarray:
    """用每个局部矩阵的右奇异向量构造迭代初始子空间。"""

    samples, dimension, _ = matrices.shape
    bases = np.empty((samples, dimension, rank), dtype=float)

    for index, matrix in enumerate(matrices):
        _, _, vt = np.linalg.svd(matrix)
        if branch == "unstable":
            bases[index] = vt[:rank].T
        else:
            bases[index] = vt[-rank:].T

    return _orthonormalize(bases)


def _graph_transform(
    matrices: np.ndarray,
    nodes: np.ndarray,
    rotation: float,
    initial_bases: np.ndarray,
    *,
    branch: Branch,
    max_iterations: int,
    tolerance: float,
) -> tuple[np.ndarray, list[float], int]:
    """执行带相位平移的子空间图变换迭代。"""

    bases = _orthonormalize(initial_bases)
    shifted_to_base = periodic_interpolation_matrix(
        nodes + rotation,
        nodes,
    )
    base_to_shifted = periodic_interpolation_matrix(
        nodes,
        nodes + rotation,
    )

    history: list[float] = []
    flips = 0

    for _ in range(max_iterations):
        if branch == "unstable":
            # 不稳定分支向前传播 A(theta) E(theta)。
            transported = np.einsum(
                "nij,njk->nik",
                matrices,
                bases,
            )
            transported = _orthonormalize(transported)
            transported, transport_flips = align_bundle_phase(
                transported,
                nodes + rotation,
            )
            flips += transport_flips

            # 将平移网格上的结果插值回基础相位网格。
            candidate = np.einsum(
                "ij,jdk->idk",
                shifted_to_base,
                transported,
            )
        else:
            # 稳定分支先把基插值到 theta+rho，再解 A(theta) x = E(theta+rho)。
            shifted = np.einsum(
                "ij,jdk->idk",
                base_to_shifted,
                bases,
            )
            shifted = _orthonormalize(shifted)
            shifted, transport_flips = align_bundle_phase(
                shifted,
                nodes + rotation,
            )
            flips += transport_flips

            candidate = np.empty_like(shifted)
            for index, matrix in enumerate(matrices):
                candidate[index] = np.linalg.solve(
                    matrix,
                    shifted[index],
                )

        candidate = _orthonormalize(candidate)

        # 先与上一轮结果对齐，再沿相位方向连续化，避免无意义的符号跳变。
        candidate, iteration_flips = _align_to_reference(
            candidate,
            bases,
        )
        candidate, phase_flips = align_bundle_phase(
            candidate,
            nodes,
        )
        flips += iteration_flips + phase_flips

        max_angle = max(
            float(
                np.max(
                    _principal_angles_deg(
                        bases[index],
                        candidate[index],
                    )
                )
            )
            for index in range(bases.shape[0])
        )
        history.append(max_angle)
        bases = candidate

        if tolerance > 0.0 and max_angle <= tolerance:
            break

    return bases, history, flips


def qr_svd_cocycle_bundle_iteration(
    cocycle: np.ndarray,
    phases: np.ndarray,
    rho: float,
    *,
    branch: Branch = "unstable",
    bundle_dimension: int | None = None,
    max_iterations: int = 200,
    angle_tolerance_deg: float = 2.0e-6,
    initial_bases: np.ndarray | None = None,
    hyperbolic_tolerance: float = 1.0e-3,
    real_relative_imaginary_tolerance: float = 1.0e-10,
) -> InvariantBundleResult:
    """用平移 QR/SVD 图迭代计算实不变子束。

    若 bundle_dimension 未给出，先调用实 Schur 方法判断目标谱应保留
    一维实方向还是二维实共轭子空间。随后在相位平移、局部映射、QR
    正交化和相位对齐之间迭代，直至相邻两轮子空间主角低于阈值。
    """

    if max_iterations < 1:
        raise ValueError("max_iterations 必须为正整数")
    if angle_tolerance_deg <= 0.0:
        raise ValueError("angle_tolerance_deg 必须为正数")

    matrices, nodes, rotation = _validate_inputs(
        cocycle,
        phases,
        rho,
    )

    schur_seed: InvariantBundleResult | None = None
    if bundle_dimension is None:
        schur_seed = real_schur_bundle_tracking(
            matrices,
            nodes,
            rotation,
            branch=branch,
            hyperbolic_tolerance=hyperbolic_tolerance,
            real_relative_imaginary_tolerance=(
                real_relative_imaginary_tolerance
            ),
        )
        bundle_dimension = schur_seed.bundle_dimension

    if bundle_dimension not in (1, 2):
        raise ValueError("bundle_dimension 只能为 1 或 2")
    if bundle_dimension > matrices.shape[1]:
        raise ValueError("bundle_dimension 不能超过状态维数")

    if initial_bases is None:
        bases = _initial_svd_bases(
            matrices,
            bundle_dimension,
            branch,
        )
    else:
        bases = np.asarray(initial_bases, dtype=float)
        expected_shape = (
            matrices.shape[0],
            matrices.shape[1],
            bundle_dimension,
        )
        if bases.shape != expected_shape:
            raise ValueError(
                f"initial_bases 应具有形状 {expected_shape}"
            )
        bases = _orthonormalize(bases)

    bases, history, flips = _graph_transform(
        matrices,
        nodes,
        rotation,
        bases,
        branch=branch,
        max_iterations=max_iterations,
        tolerance=angle_tolerance_deg,
    )

    local_maps, residuals = bundle_invariance_metrics(
        matrices,
        nodes,
        rotation,
        bases,
    )

    if schur_seed is None:
        operator_eigenvalues = np.linalg.eigvals(
            assemble_discrete_cocycle_operator(
                matrices,
                nodes,
                rotation,
            )
        )
        target = _target_operator_eigenvalue(
            operator_eigenvalues,
            branch=branch,
            hyperbolic_tolerance=hyperbolic_tolerance,
        )
        relative_imaginary = (
            abs(target.imag)
            / max(abs(target), np.finfo(float).tiny)
        )
        selected_spectrum = np.asarray(
            [target, np.conj(target)]
        )[:bundle_dimension]
    else:
        relative_imaginary = schur_seed.relative_imaginary
        selected_spectrum = schur_seed.selected_spectrum

    converged = bool(
        history
        and history[-1] <= angle_tolerance_deg
    )

    return InvariantBundleResult(
        method="qr_svd_shifted_cocycle_iteration",
        branch=branch,
        bundle_dimension=bundle_dimension,
        bases=bases,
        local_reduced_maps=local_maps,
        invariance_residuals=residuals,
        phase_principal_angles_deg=phase_principal_angles_deg(
            bases,
            nodes,
        ),
        selected_spectrum=np.asarray(selected_spectrum),
        relative_imaginary=float(relative_imaginary),
        selection_residual=float(
            history[-1] if history else np.nan
        ),
        iterations=len(history),
        converged=converged,
        convergence_history=np.asarray(history, dtype=float),
        classification=(
            "real_1d_hyperbolic_bundle"
            if bundle_dimension == 1
            else "real_2d_complex_pair_invariant_subspace"
        ),
        sign_or_orientation_flips=flips,
    )


# ---------------------------------------------------------------------------
# 第六部分：跨分辨率重采样与收敛检查
# ---------------------------------------------------------------------------


def resample_bundle(
    source_phases: np.ndarray,
    source_bases: np.ndarray,
    evaluation_phases: np.ndarray,
) -> np.ndarray:
    """把实不变子束 Fourier 重采样到新相位网格并重新正交化。"""

    source = np.asarray(source_phases, dtype=float)
    bases = _orthonormalize(source_bases)
    evaluation = np.asarray(evaluation_phases, dtype=float)

    if source.shape != (bases.shape[0],):
        raise ValueError("源相位节点数与源子束样本数不一致")

    interpolation = periodic_interpolation_matrix(
        source,
        evaluation,
    )
    values = np.einsum(
        "ij,jdk->idk",
        interpolation,
        bases,
    )
    return _orthonormalize(values)


def cross_resolution_principal_angles_deg(
    coarse_phases: np.ndarray,
    coarse_bases: np.ndarray,
    fine_phases: np.ndarray,
    fine_bases: np.ndarray,
) -> np.ndarray:
    """在细网格上比较两种分辨率结果的最大主角。"""

    fine = _orthonormalize(fine_bases)
    lifted = resample_bundle(
        coarse_phases,
        coarse_bases,
        fine_phases,
    )

    if lifted.shape != fine.shape:
        raise ValueError(
            "粗细网格子束必须具有相同的状态维数和子束维数"
        )

    return np.asarray(
        [
            float(
                np.max(
                    _principal_angles_deg(
                        lifted[index],
                        fine[index],
                    )
                )
            )
            for index in range(fine.shape[0])
        ]
    )


# ---------------------------------------------------------------------------
# 第七部分：可直接运行的合成算例和自动自检
# ---------------------------------------------------------------------------


def _rotation_2d(angle: float) -> np.ndarray:
    """返回二维旋转矩阵。"""

    return np.array(
        [
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)],
        ]
    )


def _one_dimensional_frame(theta: float) -> np.ndarray:
    """构造三维算例中的相位相关正交坐标框架。"""

    frame = np.eye(3)
    frame[:2, :2] = _rotation_2d(theta)
    return frame


def _build_real_1d_demo(
    sample_count: int = 9,
) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    """构造具有一维不稳定实子束的合成余循环。"""

    phases = np.linspace(
        0.0,
        2.0 * np.pi,
        sample_count,
        endpoint=False,
    )
    rho = 0.41
    normal_map = np.diag([1.8, 0.55, 0.8])

    cocycle = np.asarray(
        [
            _one_dimensional_frame(theta + rho)
            @ normal_map
            @ _one_dimensional_frame(theta).T
            for theta in phases
        ]
    )

    exact_unstable_bases = np.asarray(
        [
            _one_dimensional_frame(theta)[:, [0]]
            for theta in phases
        ]
    )

    return cocycle, phases, rho, exact_unstable_bases


def _complex_pair_frame(theta: float) -> np.ndarray:
    """构造四维算例中的相位相关正交坐标框架。"""

    frame = np.eye(4)
    cosine = np.cos(theta)
    sine = np.sin(theta)

    frame[0, 0] = frame[2, 2] = cosine
    frame[0, 2] = -sine
    frame[2, 0] = sine
    frame[1, 1] = frame[3, 3] = cosine
    frame[1, 3] = -sine
    frame[3, 1] = sine

    return frame


def _build_complex_pair_demo(
    sample_count: int = 9,
) -> tuple[np.ndarray, np.ndarray, float]:
    """构造目标谱为复共轭对的二维实不变子空间算例。"""

    phases = np.linspace(
        0.0,
        2.0 * np.pi,
        sample_count,
        endpoint=False,
    )
    rho = 0.37

    normal_map = np.zeros((4, 4))
    normal_map[:2, :2] = 1.7 * _rotation_2d(0.23)
    normal_map[2:, 2:] = 0.55 * _rotation_2d(0.11)

    cocycle = np.asarray(
        [
            _complex_pair_frame(theta + rho)
            @ normal_map
            @ _complex_pair_frame(theta).T
            for theta in phases
        ]
    )

    return cocycle, phases, rho


def _print_result(
    title: str,
    result: InvariantBundleResult,
) -> None:
    """以便于导师快速阅读的格式打印一个算法结果。"""

    print(f"\n{title}")
    print("-" * len(title))
    print(f"方法：{result.method}")
    print(f"分支：{result.branch}")
    print(f"子束维数：{result.bundle_dimension}")
    print(f"分类：{result.classification}")
    print(f"是否收敛：{result.converged}")
    print(f"迭代次数：{result.iterations}")
    print(
        "最大不变性残差："
        f"{result.max_invariance_residual:.3e}"
    )
    print(
        "最大相邻相位主角："
        f"{result.max_phase_principal_angle_deg:.6f} 度"
    )
    print(
        "目标谱相对虚部："
        f"{result.relative_imaginary:.3e}"
    )


def run_self_check() -> None:
    """运行三个核心方法、两类谱结构和跨分辨率指标的自动自检。"""

    print("开始运行兀文昊拟周期轨道实不变子束算法自检……")

    # 算例一：已知存在一维不稳定实子束。
    cocycle_1d, phases_1d, rho_1d, exact_bases = (
        _build_real_1d_demo()
    )
    schur_1d = real_schur_bundle_tracking(
        cocycle_1d,
        phases_1d,
        rho_1d,
    )
    qr_svd_1d = qr_svd_cocycle_bundle_iteration(
        cocycle_1d,
        phases_1d,
        rho_1d,
        bundle_dimension=1,
        initial_bases=exact_bases,
        max_iterations=60,
    )

    _print_result("算例一：实 Schur 一维子束", schur_1d)
    _print_result("算例一：QR/SVD 一维子束", qr_svd_1d)

    assert schur_1d.bundle_dimension == 1
    assert schur_1d.classification == "real_1d_hyperbolic_bundle"
    assert schur_1d.max_invariance_residual < 1.0e-10
    assert qr_svd_1d.converged
    assert qr_svd_1d.max_invariance_residual < 1.0e-8

    # 算例二：传统逐点法把复向量压成一维，而实 Schur 保留二维子空间。
    cocycle_2d, phases_2d, rho_2d = _build_complex_pair_demo()
    pointwise_2d = traditional_pointwise_eigen_bundle(
        cocycle_2d,
        phases_2d,
        rho_2d,
    )
    schur_2d = real_schur_bundle_tracking(
        cocycle_2d,
        phases_2d,
        rho_2d,
    )

    _print_result("算例二：传统逐点特征向量基线", pointwise_2d)
    _print_result("算例二：实 Schur 二维共轭子空间", schur_2d)

    assert (
        pointwise_2d.classification
        == "complex_vector_projected_to_real_1d_failure"
    )
    assert pointwise_2d.bundle_dimension == 1
    assert schur_2d.bundle_dimension == 2
    assert (
        schur_2d.classification
        == "real_2d_complex_pair_invariant_subspace"
    )
    assert schur_2d.max_invariance_residual < 1.0e-10
    assert (
        schur_2d.max_invariance_residual
        < pointwise_2d.max_invariance_residual
    )

    # 跨分辨率检查：同一个解析一维子束在 N=9 和 N=17 网格上应一致。
    coarse_phases = np.linspace(
        0.0,
        2.0 * np.pi,
        9,
        endpoint=False,
    )
    fine_phases = np.linspace(
        0.0,
        2.0 * np.pi,
        17,
        endpoint=False,
    )

    def analytic_bundle(nodes: np.ndarray) -> np.ndarray:
        values = np.zeros((nodes.size, 3, 1))
        values[:, 0, 0] = np.cos(nodes)
        values[:, 1, 0] = np.sin(nodes)
        return values

    resolution_angles = cross_resolution_principal_angles_deg(
        coarse_phases,
        analytic_bundle(coarse_phases),
        fine_phases,
        analytic_bundle(fine_phases),
    )
    maximum_resolution_angle = float(
        np.max(resolution_angles)
    )
    print(
        "\n跨分辨率最大主角："
        f"{maximum_resolution_angle:.6e} 度"
    )
    assert maximum_resolution_angle < 2.0e-6

    print("\n全部自检通过。该文件可以独立发送、阅读和运行。")


if __name__ == "__main__":
    run_self_check()
