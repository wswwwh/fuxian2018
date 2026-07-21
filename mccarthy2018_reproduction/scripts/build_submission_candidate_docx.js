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
  Packer,
  PageBreak,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const PACKAGE = path.join(
  ROOT,
  "research",
  "invariant_bundles",
  "submission_candidate",
  "package"
);
const STATUS = "adviser_submission_decision_candidate";
const MODE = process.argv[2] || "--write";

const documents = [
  {
    source: "manuscript_zh.md",
    target: "manuscript_zh.docx",
    header: "Invariant-bundle submission-candidate — 中文稿",
  },
  {
    source: "manuscript_en.md",
    target: "manuscript_en.docx",
    header: "Invariant-bundle submission-candidate — English manuscript",
  },
  {
    source: "adviser_decision_summary.md",
    target: "adviser_decision_summary.docx",
    header: "导师投稿决策摘要 / Adviser decision brief",
  },
];

const border = { style: BorderStyle.SINGLE, size: 2, color: "B7C7D6" };
const borders = { top: border, bottom: border, left: border, right: border };

function inlineRuns(text, options = {}) {
  const runs = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    if (match.index > cursor) {
      runs.push(new TextRun({ text: text.slice(cursor, match.index), ...options }));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      runs.push(
        new TextRun({ text: token.slice(2, -2), bold: true, ...options })
      );
    } else if (token.startsWith("`")) {
      runs.push(
        new TextRun({
          text: token.slice(1, -1),
          font: "Consolas",
          color: "1F4E79",
          ...options,
        })
      );
    } else {
      runs.push(
        new TextRun({ text: token.slice(1, -1), italics: true, ...options })
      );
    }
    cursor = match.index + token.length;
  }
  if (cursor < text.length) {
    runs.push(new TextRun({ text: text.slice(cursor), ...options }));
  }
  return runs.length ? runs : [new TextRun({ text, ...options })];
}

function pngDimensions(buffer) {
  if (
    buffer.length >= 24 &&
    buffer.subarray(1, 4).toString("ascii") === "PNG"
  ) {
    return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
  }
  return { width: 900, height: 600 };
}

function imageParagraph(markdownPath, link, alt) {
  const imagePath = path.resolve(path.dirname(markdownPath), link);
  if (!fs.existsSync(imagePath)) {
    throw new Error(`missing manuscript image: ${imagePath}`);
  }
  const data = fs.readFileSync(imagePath);
  const dims = pngDimensions(data);
  const width = 540;
  const height = Math.max(120, Math.round((width * dims.height) / dims.width));
  const type = path.extname(imagePath).slice(1).toLowerCase() || "png";
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 80 },
      children: [
        new ImageRun({
          type,
          data,
          transformation: { width, height },
          altText: { title: alt, description: alt, name: alt },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: inlineRuns(alt, { italics: true, size: 19, color: "4F4F4F" }),
    }),
  ];
}

function splitTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isTableSeparator(cells) {
  return cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function tableFromLines(lines) {
  const parsed = lines.map(splitTableRow);
  const data = parsed.filter((row) => !isTableSeparator(row));
  if (!data.length) return null;
  const columns = Math.max(...data.map((row) => row.length));
  const baseWidth = Math.floor(9360 / columns);
  const widths = Array.from({ length: columns }, (_, index) =>
    index === columns - 1 ? 9360 - baseWidth * (columns - 1) : baseWidth
  );
  const rows = data.map(
    (row, rowIndex) =>
      new TableRow({
        tableHeader: rowIndex === 0,
        children: widths.map(
          (width, columnIndex) =>
            new TableCell({
              borders,
              width: { size: width, type: WidthType.DXA },
              shading:
                rowIndex === 0
                  ? { fill: "DCE6F1", type: ShadingType.CLEAR }
                  : { fill: "FFFFFF", type: ShadingType.CLEAR },
              verticalAlign: VerticalAlign.CENTER,
              children: [
                new Paragraph({
                  spacing: { before: 40, after: 40 },
                  alignment:
                    rowIndex === 0 ? AlignmentType.CENTER : AlignmentType.LEFT,
                  children: inlineRuns(row[columnIndex] || "", {
                    size: 18,
                    bold: rowIndex === 0,
                  }),
                }),
              ],
            })
        ),
      })
  );
  return new Table({
    columnWidths: widths,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    rows,
  });
}

function isSpecial(line) {
  const trimmed = line.trim();
  return (
    !trimmed ||
    /^#{1,4}\s/.test(trimmed) ||
    /^!\[[^\]]*\]\([^)]+\)$/.test(trimmed) ||
    /^[-*]\s+/.test(trimmed) ||
    /^\d+\.\s+/.test(trimmed) ||
    /^>\s?/.test(trimmed) ||
    /^\|.*\|$/.test(trimmed) ||
    /^```/.test(trimmed) ||
    /^\$\$/.test(trimmed) ||
    /^<!--/.test(trimmed)
  );
}

function parseMarkdown(markdownPath) {
  const lines = fs.readFileSync(markdownPath, "utf8").replace(/\r\n/g, "\n").split("\n");
  const children = [];
  const numbering = [];
  let index = 0;
  let listSerial = 0;
  let firstTitle = true;
  let lastOrderedNumber = 0;
  let lastOrderedReference = null;

  while (index < lines.length) {
    const raw = lines[index];
    const line = raw.trim();
    if (!line) {
      index += 1;
      continue;
    }
    if (line === "<!-- PAGEBREAK -->") {
      children.push(new Paragraph({ children: [new PageBreak()] }));
      index += 1;
      continue;
    }
    if (line.startsWith("<!--")) {
      index += 1;
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      const level = heading[1].length;
      let style;
      if (level === 1 && firstTitle) {
        style = HeadingLevel.TITLE;
        firstTitle = false;
      } else if (level <= 2) {
        style = HeadingLevel.HEADING_1;
      } else if (level === 3) {
        style = HeadingLevel.HEADING_2;
      } else {
        style = HeadingLevel.HEADING_3;
      }
      children.push(
        new Paragraph({
          heading: style,
          children: inlineRuns(heading[2]),
        })
      );
      index += 1;
      continue;
    }

    const image = line.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (image) {
      children.push(...imageParagraph(markdownPath, image[2], image[1]));
      index += 1;
      continue;
    }

    if (/^\|.*\|$/.test(line)) {
      const tableLines = [];
      while (index < lines.length && /^\|.*\|$/.test(lines[index].trim())) {
        tableLines.push(lines[index].trim());
        index += 1;
      }
      const table = tableFromLines(tableLines);
      if (table) children.push(table);
      children.push(new Paragraph({ spacing: { after: 80 }, children: [] }));
      continue;
    }

    const listMatch = line.match(/^([-*]|\d+\.)\s+(.+)$/);
    if (listMatch) {
      const ordered = /\d+\./.test(listMatch[1]);
      const firstNumber = ordered ? Number.parseInt(listMatch[1], 10) : 0;
      const continuesOrdered =
        ordered &&
        lastOrderedReference !== null &&
        firstNumber === lastOrderedNumber + 1;
      const reference = continuesOrdered
        ? lastOrderedReference
        : `${ordered ? "number" : "bullet"}-${++listSerial}`;
      if (!continuesOrdered) {
        numbering.push({
          reference,
          levels: [
            {
              level: 0,
              format: ordered ? LevelFormat.DECIMAL : LevelFormat.BULLET,
              text: ordered ? "%1. " : "\u2022",
              alignment: AlignmentType.LEFT,
              style: { paragraph: { indent: { left: 600, hanging: 300 } } },
            },
          ],
        });
      }
      while (index < lines.length) {
        const current = lines[index].trim().match(/^([-*]|\d+\.)\s+(.+)$/);
        if (!current || /\d+\./.test(current[1]) !== ordered) break;
        children.push(
          new Paragraph({
            numbering: { reference, level: 0 },
            spacing: { after: 70 },
            children: inlineRuns(current[2]),
          })
        );
        if (ordered) {
          lastOrderedNumber = Number.parseInt(current[1], 10);
          lastOrderedReference = reference;
        }
        index += 1;
      }
      continue;
    }

    if (line.startsWith(">")) {
      const text = line.replace(/^>\s?/, "");
      children.push(
        new Paragraph({
          indent: { left: 480, right: 240 },
          spacing: { before: 100, after: 120 },
          children: inlineRuns(text, { italics: true, color: "3F5366" }),
        })
      );
      index += 1;
      continue;
    }

    if (line.startsWith("```")) {
      index += 1;
      const code = [];
      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index]);
        index += 1;
      }
      if (index < lines.length) index += 1;
      for (const codeLine of code) {
        children.push(
          new Paragraph({
            indent: { left: 360 },
            spacing: { after: 20 },
            children: [
              new TextRun({
                text: codeLine || " ",
                font: "Consolas",
                size: 17,
                color: "333333",
              }),
            ],
          })
        );
      }
      continue;
    }

    if (line.startsWith("$$")) {
      const math = [];
      if (line !== "$$") math.push(line.replace(/^\$\$/, ""));
      index += 1;
      while (index < lines.length && !lines[index].trim().endsWith("$$")) {
        math.push(lines[index].trim());
        index += 1;
      }
      if (index < lines.length) {
        const ending = lines[index].trim().replace(/\$\$$/, "");
        if (ending) math.push(ending);
        index += 1;
      }
      children.push(
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100, after: 120 },
          children: [
            new TextRun({ text: math.join(" "), font: "Cambria Math", size: 21 }),
          ],
        })
      );
      continue;
    }

    const paragraphLines = [line];
    index += 1;
    while (index < lines.length && !isSpecial(lines[index])) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }
    const text = paragraphLines.join(" ").replace(/\s+/g, " ");
    children.push(
      new Paragraph({
        alignment: AlignmentType.JUSTIFIED,
        spacing: { line: 330, after: 110 },
        children: inlineRuns(text),
      })
    );
  }
  return { children, numbering };
}

function makeDocument(markdownPath, headerText) {
  const parsed = parseMarkdown(markdownPath);
  return new Document({
    creator: "Codex / Wuwenhao Wu",
    title: headerText,
    subject: STATUS,
    description: "Bilingual adviser-facing invariant-bundle submission decision package",
    styles: {
      default: {
        document: { run: { font: "Arial", size: 21, color: "111111" } },
      },
      paragraphStyles: [
        {
          id: "Title",
          name: "Title",
          basedOn: "Normal",
          run: { font: "Arial", size: 38, bold: true, color: "17365D" },
          paragraph: {
            alignment: AlignmentType.CENTER,
            spacing: { before: 180, after: 260 },
          },
        },
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 29, bold: true, color: "1F4E79" },
          paragraph: { spacing: { before: 260, after: 120 }, outlineLevel: 0 },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 25, bold: true, color: "365F91" },
          paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 },
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 22, bold: true, color: "4F81BD" },
          paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 },
        },
      ],
    },
    numbering: { config: parsed.numbering },
    sections: [
      {
        properties: {
          page: {
            margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
            pageNumbers: { start: 1, formatType: "decimal" },
          },
        },
        headers: {
          default: new Header({
            children: [
              new Paragraph({
                alignment: AlignmentType.RIGHT,
                children: [
                  new TextRun({ text: headerText, size: 16, color: "6B7785" }),
                ],
              }),
            ],
          }),
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [
                  new TextRun({ text: `${STATUS}  |  Page `, size: 16, color: "6B7785" }),
                  new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "6B7785" }),
                  new TextRun({ text: " of ", size: 16, color: "6B7785" }),
                  new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "6B7785" }),
                ],
              }),
            ],
          }),
        },
        children: parsed.children,
      },
    ],
  });
}

async function writeDocuments() {
  fs.mkdirSync(PACKAGE, { recursive: true });
  for (const item of documents) {
    const source = path.join(PACKAGE, item.source);
    const target = path.join(PACKAGE, item.target);
    const document = makeDocument(source, item.header);
    const buffer = await Packer.toBuffer(document);
    fs.writeFileSync(target, buffer);
  }
  process.stdout.write("DOCX-JS WRITE PASS documents=3\n");
}

function checkDocuments() {
  for (const item of documents) {
    const target = path.join(PACKAGE, item.target);
    if (!fs.existsSync(target)) throw new Error(`missing DOCX: ${target}`);
    const data = fs.readFileSync(target);
    if (data.length < 10000 || data[0] !== 0x50 || data[1] !== 0x4b) {
      throw new Error(`invalid DOCX container: ${target}`);
    }
  }
  process.stdout.write("DOCX-JS CHECK PASS documents=3\n");
}

if (MODE === "--write") {
  writeDocuments().catch((error) => {
    process.stderr.write(`${error.stack || error}\n`);
    process.exitCode = 1;
  });
} else if (MODE === "--check") {
  checkDocuments();
} else {
  throw new Error(`unknown mode: ${MODE}`);
}
