# 阶段 E 门槛

状态：**PASS**

## 完整 Word

- DOCX 可被 Microsoft Word 12.0 正常打开、更新目录并保存。
- 54/54 图号进入正文；嵌入媒体 54 个；中文逐图图题 54 个；英文逐图图题 54 个。
- 文档含中英文摘要、关键词、引言、公共模型与方法、复现范围和评价方法、Chapter 2—5 的 54 组逐图论证、综合讨论、限制、结论、参考文献及附录 A—D。
- 116 组有编号双语表题、121 个实际表对象、6 个 OMML 公式对象、28 张核心数值图量化表均已写入。

## 自动目录与 PDF

- TOC 数量：1；Word 目录字段：1；页码字段存在；多级标题自动编号存在。
- Word 导出 PDF：122 页，12,968,768 bytes，SHA-256 `04d519277488a3f4c174c8169979e932f860f61bdc822d92e7fb2ffabf049cdf`。
- Word 更新后 DOCX：12,260,624 bytes，SHA-256 `f1f19f5ca51e9552b3b6d19d4005be3d015c374943737100947cc856576edbab`。
- LibreOffice 交叉导出：127 页；54 图与双语图题完整，未见 `MERGEFORMAT` 或域错误。跨引擎页数差 -5 页已记录，不把分页完全相同作为科学等价门槛。

## 自动审计

- `stage_e_precheck_validation.json/md`：`PASS`，25 项门槛全部通过。
- registry、原图 manifest、复现图 manifest、panel manifest 均为 54 行；DOCX/PDF 图号覆盖均为 54/54。
- 真正空白页和近空白孤页均为 0；Word/PDF 中无引用错误、书签错误和 `MERGEFORMAT` 泄漏。
- A/B/C/D=`7/30/5/12`，accepted/boundary/diagnostic/proxy=`7/30/5/12`，与阶段 C 权威 registry 一致。

## 真实性边界

- registry 中仍有 6 个统一坐标元数据字段为 `【待核实】`，封面另有姓名、单位、导师 3 个 `【待核实】` 占位；未用猜测填充。
- q=8 单步闭合、Route H 单体冷启动、Chapter 4 冻结投影 holdout、Fig. 5.10 论文等价等失败/边界均进入正文和附录。
- 本阶段统一包装 54 张 panel，但没有重算、重绘或覆盖底层科学图。
