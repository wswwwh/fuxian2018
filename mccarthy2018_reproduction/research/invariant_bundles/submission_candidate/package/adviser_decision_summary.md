# 导师投稿决策摘要 / Adviser Submission Decision Brief

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
- 图像正确性审计当前分布为 P0_OBVIOUS_MISMATCH=18, P1_MATERIAL_PARTIAL=7, P2_ACCEPTABLE_BOUNDARY=17, P3_SCHEMATIC_PROXY=12；其 P0/P1 修正队列不能被数值 gate 掩盖。
- `adviser_submission_decision_candidate` 只表示材料足以作导师决策；目标期刊选择和外部投稿均不在已授权范围内。

## 建议导师作出的四个决定 / Four decisions requested

1. 主贡献是否采用“可审计数值框架 + 系统比较 + 有界扩展”，还是要求把 Route H 二维失败/成功语义提升为主标题。
2. 是否先选定目标期刊，再按其篇幅、理论深度和图表规范修改；本包不预设期刊。
3. H5 boundary 结果放正文、附录，还是要求外部求解器复核后再使用。
4. 是否把 P0/P1 复现图修正列为投稿前硬门槛，尤其是 Fig. 5.1、5.13、5.14、5.5 与 Chapter 4 投影图。

## 推荐决策口径 / Recommended decision wording

“同意将当前材料作为 submission-decision candidate，进入目标期刊筛选和针对性修改；在选刊、理论深度、外部验证和 P0/P1 图像修正方案确定前，不对外投稿，也不声明 McCarthy 全文等价复现。”

“Approve the current materials as a submission-decision candidate and begin venue selection and venue-specific revision. Do not submit externally or claim thesis-wide McCarthy equivalence until the venue, theory depth, external-validation need, and P0/P1 figure-correction plan are resolved.”
