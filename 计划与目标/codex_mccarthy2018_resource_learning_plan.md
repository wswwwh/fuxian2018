# McCarthy 2018 论文复现项目说明

## 1. 项目背景

我正在使用 **Python** 复现 McCarthy 2018 博士论文：

**Characterization of Quasi-Periodic Orbits for Applications in the Sun-Earth and Earth-Moon Systems**

本项目的当前最高优先级是：**忠实复现论文中的核心方法和关键结果**，而不是优先准备投稿、包装创新或做泛泛的研究计划。

后续中文 EI / CSCD 或 SCI 论文，可以建立在复现结果可信、代码可重复、数据和误差表完整的基础上，但不是当前第一目标。

---

## 2. 当前主目标

请先系统学习相关资源，并将它们转化为 Python 复现任务。

重点方向包括：

- Circular Restricted Three-Body Problem, CR3BP
- Earth-Moon DRO
- periodic orbit differential correction
- state transition matrix, STM
- variational equations
- monodromy matrix
- Floquet multipliers
- stability index
- stroboscopic mapping
- invariant curve
- 2D invariant torus
- quasi-periodic orbit
- quasi-DRO
- constant energy family
- constant frequency ratio family
- constant mapping time family
- 后续可能扩展到 ephemeris model、eclipse avoidance 和 transfer design

---

## 3. 当前项目语言与实现要求

当前项目使用 **Python**。

主实现应尽量使用：

- NumPy
- SciPy
- Matplotlib
- pandas
- 必要时可以参考或使用 heyoka.py

注意：

1. MATLAB 资源只能作为算法参考，不能把项目改成 MATLAB。
2. 不要机械翻译 MATLAB 仓库。
3. 不要编造 McCarthy 2018 的官方代码仓库。
4. 所有核心结果必须可重复运行、可保存、可检查。
5. 图表必须由脚本自动生成。
6. 关键数值结果必须保存为 CSV / JSON / NPZ / MAT 等格式，不能只保存在图里。

---

## 4. 请优先学习的资源

### 4.1 McCarthy 2018 博士论文

Purdue Hammer 页面：

https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658

Purdue Engineering PDF：

https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2018_McCarthy.pdf

学习重点：

- 论文整体章节结构
- CR3BP 基础模型
- 周期轨道与 quasi-periodic orbit 的关系
- stroboscopic mapping
- invariant curve discretization
- 2D invariant torus
- constant energy family
- constant frequency ratio family
- constant mapping time family
- quasi-DRO
- Sun-Earth-Moon ephemeris model
- eclipse avoidance
- transfer design
- 哪些图表和数值结果适合作为第一阶段复现目标

---

### 4.2 Olikara & Howell 2010

Conference paper PDF：

https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf

Master thesis PDF：

https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2010_Olikara.pdf

学习重点：

- quasi-periodic invariant tori
- natural parameterization
- invariant curve discretization
- torus invariance equation
- continuation scheme
- 如何从周期轨道的中心特征向量构造初始 invariant curve
- mapping time
- rotation angle
- frequency ratio
- McCarthy 2018 如何继承这些方法

---

### 4.3 McCarthy & Howell 2019 AAS 论文

Trajectory Design Using Quasi-Periodic Orbits in the Multi-Body Problem：

https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf

学习重点：

- quasi-periodic orbit 在 trajectory design 中的用途
- QPO stability
- quasi-DRO eclipse strategy
- NRHO transfer design
- trajectory arcs from QPOs
- McCarthy 2018 应用章节的背景理解

---

### 4.4 JPL Three-Body Periodic Orbits API

API 文档：

https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html

可视化工具：

https://ssd.jpl.nasa.gov/tools/periodic_orbits.html

学习重点：

- 如何查询 Earth-Moon 系统
- 如何查询 DRO、halo、Lyapunov、vertical、axial 等周期轨道族
- period、Jacobi constant、stability index、initial state 等字段
- 如何用 JPL 数据验证 Python 复现结果

注意：

JPL API 主要用于周期轨道验证，不直接提供 McCarthy 2018 的 quasi-periodic torus 复现结果。

---

### 4.5 CR3BP MATLAB Library

GitHub 仓库：

https://github.com/JackCrusoe47/CR3BP_MATLAB_Library

学习重点：

- CR3BP propagation
- STM propagation
- Jacobi constant
- Lagrange point computation
- differential correction
- DRO corrector
- LPO corrector
- continuation
- monodromy matrix
- characteristic values
- stability index

注意：

这是 MATLAB 仓库。只总结算法结构、函数接口和数值流程，不要把项目切换为 MATLAB。

---

### 4.6 heyoka.py CR3BP notebooks

Continuation of Periodic Orbits in the CR3BP：

https://bluescarni.github.io/heyoka.py/notebooks/Periodic%20orbits%20in%20the%20CR3BP.html

Pseudo arc-length continuation in the CR3BP：

https://bluescarni.github.io/heyoka.py/notebooks/Pseudo%20arc-length%20continuation%20in%20the%20CR3BP.html

学习重点：

- Python 中如何构造 CR3BP 方程
- variational equations
- state + STM 联合积分
- periodic orbit correction
- continuation
- pseudo-arclength continuation
- 哪些代码结构可迁移到当前 Python 项目

---

## 5. 学习阶段输出文档

请先不要大规模改代码。请先创建或更新以下文档。

### 5.1 `docs/resource_links.md`

记录每个资源：

- 名称
- URL
- 是否成功访问
- 类型：论文 / API / GitHub / notebook / 数据库
- 与 McCarthy 2018 复现的关系
- 是否适合直接用于 Python 实现
- 备注

---

### 5.2 `docs/mccarthy2018_reading_notes.md`

记录：

- McCarthy 2018 的章节结构
- 每章主要研究内容
- 每章涉及的动力学模型
- 每章涉及的算法
- 每章可能需要复现的图表
- 哪些内容属于第一阶段
- 哪些内容属于第二阶段
- 哪些内容属于后续扩展

---

### 5.3 `docs/algorithm_extraction_notes.md`

请提取以下算法条目：

- CR3BP equations
- Jacobi constant
- Lagrange points
- variational equations
- STM
- differential correction
- periodic orbit correction
- monodromy matrix
- Floquet multipliers
- stability index
- stroboscopic mapping
- invariant curve discretization
- rotation angle
- mapping time
- frequency ratio
- torus correction
- continuation scheme

每个算法条目需要说明：

- 来自哪个资源
- 对应 McCarthy 2018 哪一节或哪类结果
- 输入是什么
- 输出是什么
- Python 中建议如何实现
- 当前项目是否已有对应模块
- 如果没有，需要新增什么模块

---

### 5.4 `docs/python_reproduction_plan.md`

请制定 Python 复现计划，按以下顺序：

#### 阶段 1：CR3BP 基础模块

目标：

- Earth-Moon CR3BP 方程
- Jacobi constant
- Lagrange points
- numerical propagation
- error checking

#### 阶段 2：STM 与 differential correction

目标：

- variational equations
- state transition matrix
- periodic orbit correction
- closure error
- Jacobi drift

#### 阶段 3：周期轨道复现

目标：

- DRO
- Lyapunov orbit
- Halo orbit 或论文中生成 QPO 所需的母轨道
- period
- Jacobi constant
- monodromy matrix
- Floquet multipliers
- stability index
- 与 JPL API 交叉验证

#### 阶段 4：quasi-periodic orbit 初步复现

目标：

- 从一个已验证周期轨道出发
- 利用中心特征向量构造 invariant curve 初值
- 实现 stroboscopic map
- 实现 invariant curve residual
- 生成一个最小可行的 2D torus / quasi-periodic orbit 示例

#### 阶段 5：复现 McCarthy 2018 的代表性图表

目标：

- 建立 reproduction target table
- 明确每个目标图需要哪些代码、数据和误差指标
- 优先选择最适合当前 Python 基础的图或结果

---

### 5.5 `docs/reproduction_target_table.md`

表格字段包括：

- McCarthy 2018 章节
- 图号或结果名称
- 结果类型
- 动力学模型
- 需要的算法
- 当前项目是否已有基础
- 难度等级
- 第一轮是否建议复现
- 需要的数据
- 预期输出
- 验收标准

---

### 5.6 `docs/reproduction_assumptions.md`

记录所有不确定或需要假设的内容：

- 质量参数
- 归一化单位
- 坐标系定义
- 时间单位
- 初值来源
- 数值积分器
- 积分精度
- differential correction 收敛阈值
- continuation 步长
- 与论文可能不同的实现细节
- 无法从论文确认的地方

不要静默假设。所有不确定内容必须写入该文档。

---

## 6. 后续代码结构建议

学习阶段结束后，请根据当前 Python 项目情况，建议是否建立以下结构：

```text
src/
  cr3bp/
    eom.py
    jacobi.py
    lagrange_points.py
    variational.py
    propagation.py

  periodic_orbits/
    differential_correction.py
    monodromy.py
    stability.py
    continuation.py

  quasiperiodic/
    stroboscopic_map.py
    invariant_curve.py
    torus_correction.py
    qpo_continuation.py

scripts/
  reproduce_mccarthy2018/
    step01_validate_cr3bp.py
    step02_dro_correction.py
    step03_monodromy_stability.py
    step04_initial_qpo.py

data/
  periodic_orbits/
  quasiperiodic_tori/

results/
  mccarthy2018/
    figures/
    tables/

docs/
  resource_links.md
  mccarthy2018_reading_notes.md
  algorithm_extraction_notes.md
  python_reproduction_plan.md
  reproduction_target_table.md
  reproduction_assumptions.md
```

---

## 7. 当前不要做的事情

请暂时不要：

1. 直接大规模重构项目。
2. 一开始就强行实现完整 quasi-periodic torus。
3. 为了快速出图牺牲数值正确性。
4. 把 JPL API 的结果直接当成 McCarthy 2018 的复现结果。
5. 把 MATLAB 仓库作为主项目依赖。
6. 优先写投稿大纲。
7. 编造论文没有给出的初值、图表数据或官方代码。

---

## 8. 当前应完成的第一轮任务

请按以下顺序执行：

1. 检查当前 Python 项目结构。
2. 访问并学习上面列出的资源。
3. 创建 `docs/resource_links.md`。
4. 创建 `docs/mccarthy2018_reading_notes.md`。
5. 创建 `docs/algorithm_extraction_notes.md`。
6. 创建 `docs/python_reproduction_plan.md`。
7. 创建 `docs/reproduction_target_table.md`。
8. 创建 `docs/reproduction_assumptions.md`。
9. 判断 McCarthy 2018 中最适合作为第一轮复现目标的结果。
10. 给出下一步最小可执行代码任务。

---

## 9. 汇报格式

完成学习阶段后，请汇报：

- 成功访问了哪些资源
- 哪些资源无法访问
- 每个资源提取了什么内容
- 已创建或修改哪些文档
- 当前 Python 项目缺哪些模块
- 建议下一步从哪个最小任务开始
- 下一步任务对应 McCarthy 2018 的哪一部分

请注意：当前阶段的目标是让你理解论文和资源，并把它们转化为可执行的 Python 复现计划。不要先泛泛讨论，也不要先直接写大段代码。
