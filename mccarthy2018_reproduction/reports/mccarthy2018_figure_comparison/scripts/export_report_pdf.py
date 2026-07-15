"""Update Word fields, export the report PDF, and perform a LibreOffice cross-check."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from pypdf import PdfReader


SCRIPT_DIR = Path(__file__).resolve().parent
REPORT_ROOT = SCRIPT_DIR.parent
STAGE_E = REPORT_ROOT / "stage_e"
DEFAULT_DOCX = REPORT_ROOT / "McCarthy2018_54图逐图复现对照报告.docx"
DEFAULT_PDF = REPORT_ROOT / "McCarthy2018_54图逐图复现对照报告.pdf"
SOFFICE = Path("C:/Program Files/LibreOffice/program/soffice.com")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_pages(path: Path) -> int:
    reader = PdfReader(path)
    if not reader.pages:
        raise RuntimeError(f"PDF has no pages: {path}")
    return len(reader.pages)


def export_with_word(docx: Path, output: Path) -> dict[str, object]:
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    word = document = None
    quit_error = ""
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        document = word.Documents.Open(
            str(docx.resolve()),
            ConfirmConversions=False,
            ReadOnly=False,
            AddToRecentFiles=False,
        )
        word_version = str(word.Version)
        toc_count = int(document.TablesOfContents.Count)
        field_count = int(document.Fields.Count)
        if field_count:
            document.Fields.Update()
        for index in range(1, toc_count + 1):
            document.TablesOfContents(index).Update()
        for story_type in range(1, 18):
            try:
                story = document.StoryRanges(story_type)
            except Exception:
                continue
            while story is not None:
                try:
                    if story.Fields.Count:
                        story.Fields.Update()
                except Exception:
                    pass
                try:
                    story = story.NextStoryRange
                except Exception:
                    story = None
        document.Repaginate()
        page_count = int(document.ComputeStatistics(2))
        document.Save()
        output.parent.mkdir(parents=True, exist_ok=True)
        document.ExportAsFixedFormat(
            str(output.resolve()),
            17,
            OpenAfterExport=False,
            OptimizeFor=0,
            Range=0,
            Item=0,
            IncludeDocProps=True,
            KeepIRM=True,
            CreateBookmarks=1,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
        return {
            "engine": "Microsoft Word COM",
            "word_version": word_version,
            "toc_count": toc_count,
            "field_count": field_count,
            "word_page_count": page_count,
        }
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception as error:
                quit_error = f"{type(error).__name__}: {error}"
        document = None
        word = None
        pythoncom.CoUninitialize()
        if quit_error:
            print(f"word_quit_warning={quit_error}")


def export_with_libreoffice(docx: Path, output_dir: Path) -> tuple[Path, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for existing in output_dir.glob("*.pdf"):
        existing.unlink()
    command = [str(SOFFICE), "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(docx)]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    candidates = sorted(output_dir.glob("*.pdf"), key=lambda path: path.stat().st_mtime, reverse=True)
    if completed.returncode != 0 or not candidates:
        raise RuntimeError(
            f"LibreOffice export failed: code={completed.returncode} stdout={completed.stdout} stderr={completed.stderr}"
        )
    return candidates[0], (completed.stdout + completed.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", type=Path, default=DEFAULT_DOCX)
    parser.add_argument("--output", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--no-cross-check", action="store_true")
    args = parser.parse_args()
    STAGE_E.mkdir(parents=True, exist_ok=True)
    if not args.docx.is_file():
        raise FileNotFoundError(args.docx)

    status: dict[str, object] = {
        "status": "FAIL",
        "docx": str(args.docx.resolve()),
        "docx_pre_export_sha256": sha256(args.docx),
        "word_error": "",
        "fallback": False,
    }
    started = time.perf_counter()
    try:
        status.update(export_with_word(args.docx, args.output))
    except Exception as error:
        status["word_error"] = f"{type(error).__name__}: {error}"
        status["fallback"] = True
        fallback_dir = STAGE_E / "libreoffice_final_fallback"
        exported, message = export_with_libreoffice(args.docx, fallback_dir)
        shutil.copy2(exported, args.output)
        status.update({"engine": "LibreOffice fallback", "libreoffice_message": message})

    if not args.output.is_file() or args.output.stat().st_size == 0:
        raise RuntimeError("PDF export did not produce a nonempty file")
    status.update(
        {
            "status": "PASS",
            "elapsed_seconds": time.perf_counter() - started,
            "docx_post_export_bytes": args.docx.stat().st_size,
            "docx_post_export_sha256": sha256(args.docx),
            "pdf": str(args.output.resolve()),
            "pdf_bytes": args.output.stat().st_size,
            "pdf_sha256": sha256(args.output),
            "pdf_pages": pdf_pages(args.output),
        }
    )

    if not args.no_cross_check:
        cross_dir = STAGE_E / "libreoffice_crosscheck"
        exported, message = export_with_libreoffice(args.docx, cross_dir)
        crosscheck = STAGE_E / "libreoffice_crosscheck.pdf"
        shutil.copy2(exported, crosscheck)
        exported.unlink()
        status.update(
            {
                "libreoffice_crosscheck": str(crosscheck.resolve()),
                "libreoffice_crosscheck_bytes": crosscheck.stat().st_size,
                "libreoffice_crosscheck_sha256": sha256(crosscheck),
                "libreoffice_crosscheck_pages": pdf_pages(crosscheck),
                "libreoffice_crosscheck_message": message,
                "page_count_delta_word_minus_libreoffice": status["pdf_pages"] - pdf_pages(crosscheck),
            }
        )

    (STAGE_E / "pdf_export_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"pdf_export=PASS engine={status['engine']} pages={status['pdf_pages']} "
        f"bytes={status['pdf_bytes']} fallback={status['fallback']}"
    )
    if "libreoffice_crosscheck_pages" in status:
        print(
            f"libreoffice_crosscheck_pages={status['libreoffice_crosscheck_pages']} "
            f"delta={status['page_count_delta_word_minus_libreoffice']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
