"use strict";

const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  Header,
  HeadingLevel,
  ImageRun,
  LevelFormat,
  Math: MathElement,
  MathRun,
  Packer,
  PageBreak,
  PageNumber,
  PageOrientation,
  Paragraph,
  SectionType,
  ShadingType,
  Table,
  TableCell,
  TableLayoutType,
  TableOfContents,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} = require("docx");

const PENDING = "【待核实】";
const FONT = { ascii: "Times New Roman", hAnsi: "Times New Roman", eastAsia: "SimSun" };
const FONT_SANS = { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" };
const GREEN = "3A7D5A";
const LIGHT_GREEN = "E9F3EC";
const GRAY = "6B7280";
const BLACK = "111827";
const PAGE_WIDTH = 11906;
const PAGE_HEIGHT = 16838;
const CONTENT_WIDTH = 9500;
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const GREEN_LINE = { style: BorderStyle.SINGLE, size: 8, color: GREEN };

function clip(value, limit = 600) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim() || PENDING;
  return text.length <= limit ? text : `${text.slice(0, limit - 18)}…（详见注册表）`;
}

function sortFigure(a, b) {
  const pa = a.target_id.split(".").map(Number);
  const pb = b.target_id.split(".").map(Number);
  return pa[0] - pb[0] || pa[1] - pb[1];
}

function textRun(text, options = {}) {
  return new TextRun({ text: clip(text, options.limit || 5000), font: options.font || FONT, ...options });
}

function body(text, options = {}) {
  return new Paragraph({
    style: options.style || "BodyText",
    pageBreakBefore: options.pageBreakBefore || false,
    keepNext: options.keepNext || false,
    keepLines: true,
    children: [textRun(text, { limit: options.limit || 5000 })],
  });
}

function centered(text, style = "CenteredText", options = {}) {
  return new Paragraph({
    style,
    alignment: AlignmentType.CENTER,
    keepNext: options.keepNext || false,
    children: [textRun(text, { bold: options.bold, size: options.size, font: options.font || FONT })],
  });
}

function heading1(text, pageBreakBefore = false) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    numbering: { reference: "heading-numbering", level: 0 },
    pageBreakBefore,
    keepNext: true,
    children: [textRun(text, { bold: true, font: FONT_SANS })],
  });
}

function heading2(text, pageBreakBefore = false) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    numbering: { reference: "heading-numbering", level: 1 },
    pageBreakBefore,
    keepNext: true,
    children: [textRun(text, { bold: true, font: FONT_SANS })],
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    numbering: { reference: "heading-numbering", level: 2 },
    keepNext: true,
    children: [textRun(text, { bold: true, font: FONT_SANS })],
  });
}

function appendixHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    pageBreakBefore: true,
    keepNext: true,
    children: [textRun(text, { bold: true, font: FONT_SANS })],
  });
}

function fieldParagraph(value, options = {}) {
  const text = clip(value, options.limit || 900);
  const pending = text.includes(PENDING);
  return new Paragraph({
    style: options.style || "TableText",
    alignment: options.alignment || AlignmentType.LEFT,
    keepLines: true,
    children: [
      new TextRun({
        text,
        font: options.font || FONT,
        size: options.size || 17,
        bold: options.bold || pending,
        color: pending ? "B91C1C" : options.color || BLACK,
      }),
    ],
  });
}

function cell(value, width, borders, options = {}) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    borders,
    shading: options.shading ? { fill: options.shading, type: ShadingType.CLEAR } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    children: [fieldParagraph(value, options)],
  });
}

function rowBorders(isHeader, isLast) {
  return {
    top: isHeader ? GREEN_LINE : NONE,
    bottom: isHeader || isLast ? GREEN_LINE : NONE,
    left: NONE,
    right: NONE,
    insideHorizontal: NONE,
    insideVertical: NONE,
  };
}

function threeLineTable(headers, rows, widths, options = {}) {
  const tableRows = [
    new TableRow({
      tableHeader: true,
      cantSplit: true,
      children: headers.map((header, index) =>
        cell(header, widths[index], rowBorders(true, false), {
          bold: true,
          alignment: AlignmentType.CENTER,
          shading: LIGHT_GREEN,
          size: options.fontSize || 17,
        }),
      ),
    }),
  ];
  rows.forEach((values, rowIndex) => {
    const last = rowIndex === rows.length - 1;
    tableRows.push(
      new TableRow({
        cantSplit: true,
        children: values.map((value, index) =>
          cell(value, widths[index], rowBorders(false, last), {
            bold: options.firstColumnBold && index === 0,
            alignment: options.centerColumns && options.centerColumns.includes(index)
              ? AlignmentType.CENTER
              : AlignmentType.LEFT,
            size: options.fontSize || 17,
            limit: options.limit || 900,
          }),
        ),
      }),
    );
  });
  return new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    alignment: AlignmentType.CENTER,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    rows: tableRows,
  });
}

function tableCaptions(number, chinese, english) {
  return [
    centered(`表 ${number}  ${chinese}`, "TableCaptionCN", { keepNext: true }),
    centered(`Table ${number}  ${english}`, "TableCaptionEN", { keepNext: true }),
  ];
}

function figureCaptions(number, row) {
  return [
    centered(
      `图 ${number}  McCarthy 原文结果与本文复现结果对照（原论文 Fig. ${row.target_id}）：（a）原论文图；（b）本项目复现图`,
      "FigureCaptionCN",
      { keepNext: true },
    ),
    centered(
      `Fig. ${number}  Comparison between the original result of McCarthy (Fig. ${row.target_id}) and the result reproduced in this work: (a) original; (b) reproduced`,
      "FigureCaptionEN",
      { keepNext: true },
    ),
  ];
}

function equation(text, number, width = 4500) {
  const widths = [350, width - 700, 350];
  const borders = { top: NONE, bottom: NONE, left: NONE, right: NONE };
  return new Table({
    columnWidths: widths,
    width: { size: width, type: WidthType.DXA },
    layout: TableLayoutType.FIXED,
    alignment: AlignmentType.CENTER,
    margins: { top: 40, bottom: 40, left: 0, right: 0 },
    rows: [
      new TableRow({
        cantSplit: true,
        children: [
          new TableCell({ width: { size: widths[0], type: WidthType.DXA }, borders, children: [new Paragraph({})] }),
          new TableCell({
            width: { size: widths[1], type: WidthType.DXA },
            borders,
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new MathElement({ children: [new MathRun(text)] })],
              }),
            ],
          }),
          new TableCell({
            width: { size: widths[2], type: WidthType.DXA },
            borders,
            children: [fieldParagraph(`(${number})`, { alignment: AlignmentType.RIGHT, size: 18 })],
          }),
        ],
      }),
    ],
  });
}

function imageParagraph(projectRoot, row) {
  const panelPath = path.join(projectRoot, row.comparison_asset);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    keepNext: true,
    keepLines: true,
    children: [
      new ImageRun({
        type: "png",
        data: fs.readFileSync(panelPath),
        transformation: { width: 630, height: 368 },
        altText: {
          title: `McCarthy Fig. ${row.target_id} comparison`,
          description: `Original and reproduced comparison panel for McCarthy Fig. ${row.target_id}`,
          name: `fig_${row.target_id.replace(".", "_")}_comparison`,
        },
      }),
    ],
  });
}

function makeHeader() {
  return new Header({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [textRun("McCarthy（2018）拟周期轨道数值复现与 54 图逐图对照", { size: 16, color: GRAY })],
      }),
    ],
  });
}

function makeFooter() {
  return new Footer({
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          textRun("— ", { size: 16, color: GRAY }),
          new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: GRAY }),
          textRun(" —", { size: 16, color: GRAY }),
        ],
      }),
    ],
  });
}

function sectionProperties(columns = 1, first = false, type = SectionType.NEXT_PAGE) {
  return {
    type,
    page: {
      size: { width: PAGE_WIDTH, height: PAGE_HEIGHT, orientation: PageOrientation.PORTRAIT },
      margin: { top: 1440, bottom: 1276, left: 1134, right: 1134, header: 620, footer: 620 },
      pageNumbers: first ? { start: 1 } : undefined,
    },
    column: { count: columns, equalWidth: true, space: columns === 2 ? 600 : 0 },
  };
}

function coreMetricRows(metrics, figureId) {
  const priority = {
    "论文目标/关键物理量": 0,
    "逐图源层最佳指标": 1,
    "动力学/校正残差": 2,
    "Jacobi 一致性": 3,
    "周期/相位闭合": 4,
    "稳定性指标误差": 5,
  };
  return metrics
    .filter((item) => item.target_id === figureId)
    .sort((a, b) => (priority[a.metric] ?? 20) - (priority[b.metric] ?? 20))
    .slice(0, 5)
    .map((item) => [
      clip(item.metric, 90),
      clip(item.paper_value_or_target, 300),
      clip(item.project_result, 380),
      clip(item.error_or_status, 180),
    ]);
}

function evidenceRows(row) {
  return [
    ["原论文图号/页码/图题", `Fig. ${row.target_id}；论文 p. ${row.paper_page}（PDF p. ${row.pdf_page}）；${clip(row.paper_caption, 500)}`],
    ["研究对象", row.research_object],
    ["动力学模型", row.model],
    ["坐标系", row.coordinate_system],
    ["主要参数", clip(row.main_parameters, 650)],
    ["数值方法", row.numerical_method],
    ["项目脚本", row.script],
    ["数据文件/证据", clip(`${row.data_source}；${row.evidence}`, 900)],
    ["定量验证", clip(row.quantitative_validation, 900)],
    ["一致之处", row.consistency_cn],
    ["主要差异", row.difference_cn],
    ["差异原因", row.difference_reason_cn],
    ["当前复现等级", `${row.reproduction_grade}；${row.grade_boundary}；${row.limitation_cn}`],
  ];
}

async function main() {
  const inputPath = process.argv[2];
  const outputPath = process.argv[3];
  if (!inputPath || !outputPath) throw new Error("Usage: node build_word_report.js <input.json> <output.docx>");
  const input = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  const registry = input.registry.slice().sort(sortFigure);
  const metrics = input.metrics;
  const summary = input.summary;
  const meta = input.build_meta;
  const projectRoot = meta.project_root;
  const gradeCounts = summary.grade_counts;
  const evidenceCounts = summary.evidence_counts;

  let tableCounter = 0;
  let figureCounter = 0;

  const front = [
    new Paragraph({ style: "Title", children: [textRun("McCarthy（2018）拟周期轨道计算与应用的数值复现及逐图对照", { bold: true, font: FONT_SANS })] }),
    new Paragraph({ style: "Subtitle", children: [textRun("Numerical Reproduction and Figure-by-Figure Assessment of the Quasi-Periodic Orbit Computations and Applications in McCarthy (2018)", { font: FONT })] }),
    centered("【待核实】姓名", "AuthorLine", { bold: true }),
    centered("【待核实】单位", "AuthorLine"),
    centered("【待核实】导师", "AuthorLine"),
    centered(`构建日期：${meta.build_date}`, "MetadataLine"),
    centered("内部复现审查稿；原论文图仅用于研究复现对照", "MetadataLine"),
    centered("摘  要", "AbstractTitle", { bold: true }),
    body(
      [
        "本文面向 McCarthy（2018）学位论文中 Chapter 2—5 的 54 张目标图，建立原图、当前项目数值图、脚本、数据和审计证据的一一对应关系，并形成可重复构建的逐图对照报告。",
        "复现链覆盖 CR3BP 基础几何、周期轨道差分修正与延拓、不变曲线/环面校正、DG/STM 稳定性、稳定与不稳定流形、打靶转移以及 BCR4BP/DE421 扩展。",
        `当前分级为 A=${gradeCounts.A}、B=${gradeCounts.B}、C=${gradeCounts.C}、D=${gradeCounts.D}；证据状态为 accepted=${evidenceCounts.accepted}、boundary=${evidenceCounts.boundary}、diagnostic=${evidenceCounts.diagnostic}、proxy=${evidenceCounts.proxy}。`,
        "Route H 定映射时间源层含 30 条验证记录，最大 |z| 为 14573.10318409037 km，最大映射残差为 6.469474407020314×10^-10。",
        "与此同时，q=8 单步闭合、Route H 单体冷启动、Chapter 4 冻结投影 holdout 和 Fig. 5.10 论文等价仍保留明确失败或边界。",
        `现有 6 条统一坐标元数据无法从当前材料唯一核实，均以${PENDING}标记。`,
        "因此，本文结论限于当前权威 CSV/NPZ、逐图审计和实际生成资产，不作整篇论文全部数值等价的声明。",
      ].join(""),
      { style: "AbstractText" },
    ),
    body("关键词：拟周期轨道；不变曲线；不变环面；稳定性分析；不变流形；数值复现", { style: "Keywords" }),
    centered("Abstract", "AbstractTitle", { bold: true }),
    body(
      "This report maps all 54 target figures in Chapters 2–5 of McCarthy (2018) to current project figures, scripts, data, and audit evidence. The evidence is classified into seven project-level quantitative acceptances, thirty physical-consistency boundaries, five diagnostic or partial source layers, and twelve schematic/proxy figures. Failures and incomplete equivalence claims are retained explicitly, including the period-8 single-shoot closure boundary, the Route H monolithic cold-start failure, the Chapter 4 frozen projection holdout failure, and the Fig. 5.10 paper-equivalence boundary. The report therefore supports auditable, figure-level conclusions rather than a blanket claim of complete thesis equivalence.",
      { style: "AbstractText" },
    ),
    body("Keywords: quasi-periodic orbit; invariant curve; invariant torus; stability analysis; invariant manifold; numerical reproduction", { style: "Keywords" }),
    new Paragraph({ children: [new PageBreak()] }),
    centered("目  录", "TOCTitle", { bold: true }),
    new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),
  ];

  const methods = [
    heading1("引言"),
    body(
      "McCarthy（2018）围绕日地与地月系统中的拟周期轨道表征、稳定性、流形及任务应用展开研究[1]。本项目的目标不是逐像素临摹原图，而是检验模型、参数、数值解、误差指标、物理趋势和可追溯性是否形成闭合证据链。",
    ),
    body(
      "本文覆盖原论文 Fig. 2.1—2.15、Fig. 3.1—3.17、Fig. 4.1—4.8 与 Fig. 5.1—5.14。每个目标图均给出原图、复现图、状态、A—E 等级、脚本、数据、数值验证、一致性、差异和限制；失败结果不删除，未核实字段不猜测。",
    ),
    body(
      "全文首先概述公共动力学与数值方法，随后说明数据与评价体系，再按 Chapter 2—5 逐图论证，最后总结定量成果、物理一致性、失败边界和可重复构建信息。",
    ),
    heading1("动力学模型与数值方法"),
    heading2("圆型限制性三体问题"),
    body("在主星—次星质心旋转坐标系中，采用无量纲 CR3BP 方程表示航天器运动。式（1）给出旋转系运动方程，式（2）给出伪势函数。具体质量参数、长度与时间尺度由各图脚本绑定；未在 registry 中明确的换算不作统一猜测。"),
    equation("ẍ − 2ẏ = ∂Ω/∂x;  ÿ + 2ẋ = ∂Ω/∂y;  z̈ = ∂Ω/∂z", 1),
    equation("Ω = (x² + y²)/2 + (1 − μ)/r₁ + μ/r₂", 2),
    body("Jacobi 常数用于检查自治 CR3BP 传播的一致性。式（3）中的漂移只作为本项目内部数值门槛；原论文未报告相应误差时，定量表明确写作“原论文未报告”。"),
    equation("C_J = 2Ω − (ẋ² + ẏ² + ż²)", 3),
    heading2("周期轨道、不变曲线与环面"),
    body("周期轨道通过单步或多步打靶差分修正获得，并沿自然参数或伪弧长方向延拓。拟周期环面以不变曲线离散，并要求映射后的曲线与旋转后的离散曲线一致。"),
    equation("Φ_T(X(θ)) = X(θ + ρ)", 4),
    body("离散残差、相位条件、Jacobi 漂移与多返回误差共同限定接受层。period-q 轨道另以单步全周期闭合和多段连续性区分严格接受与局部接受。"),
    heading2("DG、STM 与不变流形"),
    body("对不变曲线映射求导得到 DG，并结合 STM 或离散差分验证特征方向。稳定/不稳定方向经小扰动后传播形成流形。单一三维截图不能证明状态空间逐点等价，故 Chapter 4 另保留冻结相机与投影 holdout。"),
    equation("DG(X) v = λv", 5),
    heading2("转移与高保真扩展"),
    body("转移问题采用多步打靶、端点修正、近地点搜索和脉冲统计。部分 Chapter 5 结果增加 DE421 初始化的 BCR4BP 或星历几何检查，但扩展工况与论文自主 CR3BP 工况分层记录。"),
    equation("Δv_total = Σᵢ ‖Δvᵢ‖", 6),
    heading2("积分、容差与误差边界"),
    body("项目脚本按任务使用自适应数值积分、Newton/打靶修正、STM/DG 谱分析和逐图审计。积分器、容差、节点数、相位和相机参数均以对应脚本与 CSV/NPZ 为准；本文不把不同脚本的设置合并为一个未核实的全局参数。"),
  ];

  const figuresSection = [
    heading1("复现范围、数据来源与评价方法"),
    body(
      `原论文主版本为 Brian P. McCarthy 于 2018 年提交 Purdue University 的学位论文，当前本地 PDF 共 137 页。原图由 PyMuPDF 以 4.2 倍页面渲染提取，54 张图均保留坐标轴与子图；名义 302.4 dpi 不代表提升内嵌栅格的固有分辨率。`,
    ),
    body(
      "复现图来自当前项目中 54 个脚本生成的非空 PNG/PDF 权威输出。本报告只做哈希保持复制和统一 panel 包装，没有重算或覆盖底层科学图；全部输入、输出和 SHA-256 记录于 manifest。",
    ),
  ];

  tableCounter += 1;
  figuresSection.push(...tableCaptions(tableCounter, "A—E 复现等级定义", "Definitions of reproduction grades A–E"));
  figuresSection.push(
    threeLineTable(
      ["等级", "定义", "本文边界"],
      [
        ["A", "定量数值复现", "当前项目门槛内通过；不自动等于原作者节点逐点等价"],
        ["B", "物理一致性复现", "真实数值解、对象和主要趋势一致；严格论文等价仍有边界"],
        ["C", "数值源层或部分复现", "只覆盖局部区间、分支、投影或诊断门槛"],
        ["D", "示意图复现", "用于坐标、几何、算法或概念，不报告数值等价"],
        ["E", "尚未完成", `证据不足时保留${PENDING}`],
      ],
      [900, 3100, 5500],
      { firstColumnBold: true, centerColumns: [0], fontSize: 18 },
    ),
  );
  const gradeTableNumber = tableCounter;

  tableCounter += 1;
  figuresSection.push(...tableCaptions(tableCounter, "当前复现等级与证据状态统计", "Current grade and evidence-status counts"));
  figuresSection.push(
    threeLineTable(
      ["统计项", "A/accepted", "B/boundary", "C/diagnostic", "D/proxy"],
      [["图数", String(gradeCounts.A), String(gradeCounts.B), String(gradeCounts.C), String(gradeCounts.D)]],
      [2300, 1800, 1800, 1800, 1800],
      { centerColumns: [1, 2, 3, 4], fontSize: 18 },
    ),
  );
  const countTableNumber = tableCounter;

  tableCounter += 1;
  figuresSection.push(...tableCaptions(tableCounter, "报告数据与资产真值源", "Authoritative data and asset sources"));
  figuresSection.push(
    threeLineTable(
      ["类别", "路径/数量", "用途"],
      [
        ["原论文图", "source_figure_manifest.csv；54/54", "原图页码、图题、裁切与哈希"],
        ["复现图", "reproduction_figure_manifest.csv；54/54", "脚本生成资产、矢量 PDF 与哈希"],
        ["逐图状态", "figure_comparison_registry.csv；54/54", "模型、方法、数据、差异、等级与限制"],
        ["定量指标", `quantitative_metrics_registry.csv；${metrics.length} 行`, "原文目标、本项目结果、误差/状态与证据"],
        ["对照 panel", "comparison_panel_manifest.csv；54/54", "等比、无裁切、无拉伸双图对照"],
      ],
      [1700, 3700, 4100],
      { fontSize: 17 },
    ),
  );
  const sourceTableNumber = tableCounter;
  figuresSection.push(
    body(`等级与数据边界分别见表 ${gradeTableNumber}—表 ${sourceTableNumber}。全文的 A 级仅表示当前项目审计语义下的定量通过，不构成整篇论文全部复现成功的结论。`),
  );

  const chapterTitles = {
    "2": "Chapter 2 逐图对照",
    "3": "Chapter 3 逐图对照",
    "4": "Chapter 4 逐图对照",
    "5": "Chapter 5 逐图对照",
  };
  for (const chapter of ["2", "3", "4", "5"]) {
    figuresSection.push(heading1(chapterTitles[chapter], true));
    const rows = registry.filter((item) => item.chapter === chapter);
    rows.forEach((row, chapterIndex) => {
      figureCounter += 1;
      const evidenceTableNumber = ++tableCounter;
      const metricRows = coreMetricRows(metrics, row.target_id);
      const metricTableNumber = metricRows.length > 0 ? ++tableCounter : null;
      figuresSection.push(heading2(`McCarthy Fig. ${row.target_id}：${row.research_object}`, chapterIndex > 0));
      figuresSection.push(
        body(
          `如图 ${figureCounter} 所示，左侧为 McCarthy 原论文 Fig. ${row.target_id}，右侧为本项目当前复现结果。逐图证据字段见表 ${evidenceTableNumber}${metricTableNumber ? `，核心定量指标见表 ${metricTableNumber}` : ""}。当前主等级为 ${row.reproduction_grade}，证据状态为 ${row.status}。`,
          { keepNext: true },
        ),
      );
      figuresSection.push(imageParagraph(projectRoot, row));
      figuresSection.push(...figureCaptions(figureCounter, row));
      figuresSection.push(...tableCaptions(evidenceTableNumber, `原论文 Fig. ${row.target_id} 逐图证据记录`, `Evidence record for original Fig. ${row.target_id}`));
      figuresSection.push(
        threeLineTable(["字段", "内容"], evidenceRows(row), [2100, 7400], {
          firstColumnBold: true,
          fontSize: 16,
          limit: 950,
        }),
      );
      if (metricTableNumber) {
        figuresSection.push(...tableCaptions(metricTableNumber, `原论文 Fig. ${row.target_id} 核心定量指标`, `Core quantitative metrics for original Fig. ${row.target_id}`));
        figuresSection.push(
          threeLineTable(["指标", "原论文值或目标值", "本项目结果", "误差/状态"], metricRows, [1800, 2700, 3100, 1900], {
            fontSize: 15,
            limit: 430,
          }),
        );
      }
      figuresSection.push(body(`证据边界：${row.limitation_cn} ${row.next_action ? `下一动作：${clip(row.next_action, 420)}。` : ""}`));
    });
  }

  const closing = [
    heading1("综合结果与讨论", true),
    body(
      "项目已经形成从 CR3BP 基础量、周期轨道修正、不变曲线/环面延拓、DG/STM 稳定性、不变流形传播到任务转移审计的独立实现链。54 图工程覆盖完整，但不同图的证据强度不相同：A 级 7 张，B 级 30 张，C 级 5 张，D 级 12 张。",
    ),
    body(
      "Chapter 3 的定能量与定频率环面族构成当前最稳定的定量层；Route H 将定映射时间拟 DRO 图源层扩展至最大 |z|=14573.10318409037 km。Chapter 4 的内部动力学证据较强，但论文投影等价仍受冻结 holdout 失败约束。Chapter 5 已将多张代理图替换为真实 CR3BP/BCR4BP 数值结果，同时保留高保真和论文工况差异。",
    ),
  ];

  tableCounter += 1;
  const resultTableNumber = tableCounter;
  closing.push(...tableCaptions(resultTableNumber, "代表性定量结果与边界", "Representative quantitative results and boundaries"));
  closing.push(
    threeLineTable(
      ["原论文图", "当前结果", "边界"],
      [
        ["Fig. 3.10", "q=2/q=3 严格闭合；局部残差最差 7.654092149144291×10^-14", "q=8 单步闭合误差 3.906984451743337"],
        ["Fig. 3.16", "Route H 30 行；max |z|=14573.10318409037 km；max residual=6.469474407020314×10^-10", "monolithic cold-start=fail，hybrid=pass"],
        ["Fig. 4.2", "公共区间 coverage=0.8902665099213599；RMSE=0.3710034126027414", "尾段缺口 0.04945011318863024 day"],
        ["Fig. 4.3—4.6", "状态空间与局部 STM 行通过", "冻结投影 holdout=0/4，paper_3d=false"],
        ["Fig. 5.10", "BCR4BP 数值接受 2/2；最差端点误差 4.819078×10^-5 km", "paper_equivalence=0/2"],
        ["Fig. 5.12", "36 行；覆盖 -24..+11 h；最小 Δv 差 -6.029648133534657 m/s", "+12..+24 h 未覆盖"],
        ["Fig. 5.13", "近地点 7034.029835374918 km；目标误差 1.029835374917639 km", "论文热图逐点比较与高保真修正待完成"],
        ["Fig. 5.14", "近地点 7034.028970727035 km；转移时间 433.0873004386989 day", "BCR4BP/星历修正待完成"],
      ],
      [1500, 5100, 2900],
      { fontSize: 16 },
    ),
  );
  closing.push(body(`表 ${resultTableNumber} 先给出当前可追溯数值，再给出不能跨越的论文等价边界；该顺序与参考投稿稿“文字—图—表—定量分析”的证据链一致。`));

  closing.push(
    heading1("复现限制"),
    body("第一，原论文未公开大多数图的完整初始状态、连续分支节点与离散环面数据，当前独立重建不能用于证明状态空间逐点等价。"),
    body("第二，相位、扰动幅值、稳定/不稳定分支选择、三维相机、投影、轴范围与绘图参数并非全部公开；单视图相似不能升级为三维等价。"),
    body("第三，Chapter 4 的冻结投影 holdout 为失败结果；任何后验相机、epsilon 或源成员调整均不得重新命名为独立 holdout。"),
    body("第四，部分 Chapter 5 任务的边界状态、交点相位、优化约束与高保真环境不完整；项目 BCR4BP/DE421 扩展与论文自主 CR3BP 工况必须分层。"),
    body("第五，Fig. 5.2、5.3、5.4、5.6、5.7 和 5.10 的统一坐标元数据尚不能从现有材料唯一核实，报告中继续标注【待核实】。"),
    heading1("结论"),
    body("（1）工程覆盖方面，54/54 原论文图、54/54 复现图和 54/54 对照 panel 均已映射，逐图字段、等级、定量表和限制完整进入正文或附录。"),
    body("（2）数值方法方面，项目已实现并审计 CR3BP 基础量、周期轨道修正与延拓、不变曲线/环面、DG/STM、流形、转移与部分高保真扩展。"),
    body("（3）定量成果方面，7 张图达到当前项目 A 级门槛；Route H、Fig. 4.2 数字化公共区间、Fig. 5.10 BCR4BP 端点、Fig. 5.13/5.14 目标近地点等均形成可追溯数值记录。"),
    body("（4）物理一致性方面，30 张图达到 B 级，5 张达到 C 级；这些图给出真实数值解或局部源层，但严格论文等价尚未证明。"),
    body("（5）证明边界方面，当前证据不支持“整篇论文全部成功复现”的表述；失败门槛、代理图、未公开源数据与【待核实】字段均必须保留。"),
    heading1("参考文献"),
    new Paragraph({
      numbering: { reference: "reference-list", level: 0 },
      style: "ReferenceText",
      children: [textRun("McCarthy B. P. Characterization of Quasi-Periodic Orbits for Applications in the Sun-Earth and Earth-Moon Systems. Purdue University, 2018.", { size: 16 })],
    }),
  );

  closing.push(appendixHeading("附录 A  54 图状态总表"));
  tableCounter += 1;
  closing.push(...tableCaptions(tableCounter, "54 图复现等级与边界索引", "Index of grades and boundaries for all 54 figures"));
  closing.push(
    threeLineTable(
      ["原图", "研究对象", "等级", "状态", "proxy", "主要限制"],
      registry.map((row) => [
        `Fig. ${row.target_id}`,
        clip(row.research_object, 80),
        row.reproduction_grade,
        row.status,
        row.uses_proxy,
        clip(row.limitation_cn, 180),
      ]),
      [850, 2350, 600, 1000, 750, 3950],
      { centerColumns: [0, 2, 3, 4], fontSize: 14, limit: 220 },
    ),
  );

  closing.push(appendixHeading("附录 B  核心参数与误差索引"));
  tableCounter += 1;
  const coreIds = Array.from(new Set(metrics.filter((item) => item.priority_core === "true").map((item) => item.target_id))).sort((a, b) => sortFigure({ target_id: a }, { target_id: b }));
  const appendixMetricRows = coreIds.map((figureId) => {
    const choices = metrics.filter((item) => item.target_id === figureId);
    const chosen = choices.find((item) => item.metric === "逐图源层最佳指标") || choices.find((item) => item.metric === "论文目标/关键物理量") || choices[0];
    return [`Fig. ${figureId}`, clip(chosen.metric, 80), clip(chosen.paper_value_or_target, 220), clip(chosen.project_result, 300), clip(chosen.error_or_status, 150)];
  });
  closing.push(...tableCaptions(tableCounter, "28 张核心数值图代表性定量记录", "Representative quantitative records for 28 core figures"));
  closing.push(
    threeLineTable(["原图", "指标", "原文/目标", "本项目", "状态"], appendixMetricRows, [750, 1550, 2300, 3150, 1750], {
      centerColumns: [0],
      fontSize: 14,
      limit: 320,
    }),
  );

  closing.push(appendixHeading("附录 C  程序、数据、环境与构建索引"));
  tableCounter += 1;
  const hashRows = Object.entries(meta.manifest_hashes).map(([name, hash]) => [name, hash]);
  closing.push(...tableCaptions(tableCounter, "报告关键清单 SHA-256", "SHA-256 hashes of key report manifests"));
  closing.push(threeLineTable(["文件", "SHA-256"], hashRows, [3300, 6200], { fontSize: 14 }));
  closing.push(body(`构建基线 Git HEAD：${meta.git_head}。阶段提交和最终提交以 document_build_log.md 与仓库 Git 历史为准。`, { style: "CodeText" }));
  meta.git_log.forEach((line) => closing.push(body(line, { style: "CodeText" })));
  closing.push(body(`Python：${meta.python}`, { style: "CodeText" }));
  closing.push(body(`Node.js：${meta.node}`, { style: "CodeText" }));
  closing.push(body("构建命令：D:\\miniconda3\\envs\\cislunar\\python.exe reports\\mccarthy2018_figure_comparison\\scripts\\build_word_report.py", { style: "CodeText" }));
  closing.push(body("导出命令：D:\\miniconda3\\envs\\cislunar\\python.exe reports\\mccarthy2018_figure_comparison\\scripts\\export_report_pdf.py", { style: "CodeText" }));
  closing.push(body("资产验证：D:\\miniconda3\\envs\\cislunar\\python.exe reports\\mccarthy2018_figure_comparison\\scripts\\validate_report_assets.py", { style: "CodeText" }));

  closing.push(appendixHeading("附录 D  【待核实】事项"));
  tableCounter += 1;
  closing.push(...tableCaptions(tableCounter, "字段级待核实清单", "Field-level items pending verification"));
  closing.push(
    threeLineTable(
      ["原图", "字段", "当前值"],
      input.pending.map((item) => [`Fig. ${item.target_id}`, item.field, item.value]),
      [1000, 2200, 6300],
      { firstColumnBold: true, fontSize: 16 },
    ),
  );
  closing.push(body("以上占位符是最终报告的显式真实性边界。后续人工补充必须同时更新权威 registry、构建日志和 Word/PDF，不得只在文档中手工替换。"));

  const styles = {
    default: {
      document: { run: { font: FONT, size: 21, language: { value: "en-US", eastAsia: "zh-CN" } }, paragraph: { spacing: { line: 300 } } },
    },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", next: "Subtitle", quickFormat: true, run: { font: FONT_SANS, size: 36, bold: true, color: BLACK }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 240, after: 160 }, keepNext: true, outlineLevel: 0 } },
      { id: "Subtitle", name: "Subtitle", basedOn: "Normal", next: "AuthorLine", run: { font: FONT, size: 26, color: "374151" }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 200 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "BodyText", quickFormat: true, run: { font: FONT_SANS, size: 28, bold: true, color: BLACK }, paragraph: { spacing: { before: 240, after: 140 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "BodyText", quickFormat: true, run: { font: FONT_SANS, size: 24, bold: true, color: BLACK }, paragraph: { spacing: { before: 180, after: 100 }, keepNext: true, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "BodyText", quickFormat: true, run: { font: FONT_SANS, size: 21, bold: true, color: BLACK }, paragraph: { spacing: { before: 120, after: 80 }, keepNext: true, outlineLevel: 2 } },
      { id: "BodyText", name: "Body Text", basedOn: "Normal", next: "BodyText", quickFormat: true, run: { font: FONT, size: 21, color: BLACK }, paragraph: { alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 420 }, spacing: { line: 300, after: 100 }, widowControl: true } },
      { id: "AbstractText", name: "Abstract Text", basedOn: "BodyText", next: "Keywords", run: { font: FONT, size: 19 }, paragraph: { alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 0 }, spacing: { line: 280, after: 100 } } },
      { id: "Keywords", name: "Keywords", basedOn: "BodyText", next: "AbstractTitle", run: { font: FONT, size: 19 }, paragraph: { alignment: AlignmentType.JUSTIFIED, indent: { firstLine: 0 }, spacing: { after: 180 } } },
      { id: "AbstractTitle", name: "Abstract Title", basedOn: "Normal", next: "AbstractText", run: { font: FONT_SANS, size: 22, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 160, after: 80 }, keepNext: true } },
      { id: "AuthorLine", name: "Author Line", basedOn: "Normal", next: "AuthorLine", run: { font: FONT, size: 20 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 50 }, keepNext: true } },
      { id: "MetadataLine", name: "Metadata Line", basedOn: "Normal", next: "AbstractTitle", run: { font: FONT, size: 16, color: GRAY }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 40 }, keepNext: true } },
      { id: "CenteredText", name: "Centered Text", basedOn: "Normal", next: "BodyText", run: { font: FONT, size: 20 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 80 } } },
      { id: "TOCTitle", name: "TOC Title", basedOn: "Normal", next: "Normal", run: { font: FONT_SANS, size: 28, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 180 }, keepNext: true } },
      { id: "FigureCaptionCN", name: "Figure Caption CN", basedOn: "Normal", next: "FigureCaptionEN", run: { font: FONT, size: 18 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 80, after: 20 }, keepNext: true } },
      { id: "FigureCaptionEN", name: "Figure Caption EN", basedOn: "Normal", next: "TableCaptionCN", run: { font: FONT, size: 17 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 100 }, keepNext: true } },
      { id: "TableCaptionCN", name: "Table Caption CN", basedOn: "Normal", next: "TableCaptionEN", run: { font: FONT, size: 18, bold: true }, paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 100, after: 20 }, keepNext: true } },
      { id: "TableCaptionEN", name: "Table Caption EN", basedOn: "Normal", next: "TableText", run: { font: FONT, size: 16 }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 60 }, keepNext: true } },
      { id: "TableText", name: "Table Text", basedOn: "Normal", next: "TableText", run: { font: FONT, size: 17 }, paragraph: { alignment: AlignmentType.LEFT, spacing: { line: 240, after: 20 }, widowControl: false } },
      { id: "CodeText", name: "Code Text", basedOn: "Normal", next: "CodeText", run: { font: "Courier New", size: 16 }, paragraph: { alignment: AlignmentType.LEFT, spacing: { after: 40 }, widowControl: false } },
      { id: "ReferenceText", name: "Reference Text", basedOn: "Normal", next: "ReferenceText", run: { font: FONT, size: 16 }, paragraph: { alignment: AlignmentType.JUSTIFIED, spacing: { line: 220, after: 40 }, indent: { left: 540, hanging: 540 } } },
    ],
  };

  const numbering = {
    config: [
      {
        reference: "heading-numbering",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "%1", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 0, hanging: 0 } } } },
          { level: 1, format: LevelFormat.DECIMAL, text: "%1.%2", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 0, hanging: 0 } } } },
          { level: 2, format: LevelFormat.DECIMAL, text: "%1.%2.%3", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 0, hanging: 0 } } } },
        ],
      },
      {
        reference: "reference-list",
        levels: [
          { level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 540 } } } },
        ],
      },
    ],
  };

  const doc = new Document({
    creator: "Codex",
    title: "McCarthy（2018）拟周期轨道计算与应用的数值复现及逐图对照",
    description: "Auditable 54-figure reproduction comparison report",
    styles,
    numbering,
    settings: { updateFields: true, compatibilityModeVersion: 12, defaultTabStop: 420 },
    sections: [
      { properties: sectionProperties(1, true), headers: { default: makeHeader() }, footers: { default: makeFooter() }, children: front },
      { properties: sectionProperties(2, false, SectionType.CONTINUOUS), headers: { default: makeHeader() }, footers: { default: makeFooter() }, children: methods },
      { properties: sectionProperties(1), headers: { default: makeHeader() }, footers: { default: makeFooter() }, children: figuresSection },
      { properties: sectionProperties(1), headers: { default: makeHeader() }, footers: { default: makeFooter() }, children: closing },
    ],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, buffer);
  console.log(`docx_js=PASS figures=${registry.length} tables=${tableCounter} images=${figureCounter} bytes=${buffer.length}`);
}

main().catch((error) => {
  console.error(error.stack || String(error));
  process.exit(1);
});
