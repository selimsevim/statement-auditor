"""Pass 0b — extract and clean plain text from downloaded PDFs.

Reads each PDF in data/raw/ (matched to sources.csv by slug+year), extracts text
with PyMuPDF, and writes cleaned text to data/text/{slug}_{year}.txt.

Modern-slavery statements are magazine-style, multi-column PDFs. PyMuPDF's
`get_text("blocks")` groups text into layout blocks in reading order, keeping
whole paragraphs contiguous — so a quote taken from within a paragraph appears
verbatim in the output even where column *order* is imperfect. (A prior
word-level column-detection approach on pdfplumber scored markedly worse on the
verbatim-match rate that Pass 2's evidence verifier depends on.)

Cleaning then de-hyphenates line-break splits, normalises whitespace, drops
standalone page-number lines, and strips running headers/footers (exact lines
recurring as the first/last line on most pages). Each page is prefixed with a
"--- Page N ---" marker so the extraction pass can cite pages.

The cleaned text is the single canonical form: the LLM reads it and quotes from
it, and evidence quotes are later matched against this same text — so cleaning
only needs to be consistent, not perfect.

CLI:
    python -m src.ingest.extract [--company SLUG] [--force]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from ..config import Config, load_config
from ..schemas import SourceRow
from ..sources import load_sources, raw_pdf_path, text_path

_HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")
_MULTISPACE = re.compile(r"[ \t]+")
_PAGE_NUM_LINE = re.compile(r"^(page\s*)?\d{1,4}$", re.IGNORECASE)
_PAGE_FRAC_LINE = re.compile(r"^\d{1,4}\s*/\s*\d{1,4}$")


@dataclass
class ExtractResult:
    row: SourceRow
    status: str  # extracted | cached | skipped
    detail: str
    n_pages: int = 0
    n_words: int = 0
    path: Path | None = None


def _page_lines(page: pymupdf.Page) -> list[str]:
    """Lines for one page, in PyMuPDF block (reading) order, with block breaks."""
    lines: list[str] = []
    for block in page.get_text("blocks"):
        # block = (x0, y0, x1, y1, text, block_no, block_type); type 0 == text
        if block[6] != 0 or not block[4].strip():
            continue
        for line in block[4].split("\n"):
            lines.append(line)
        lines.append("")  # blank line between blocks → paragraph-break signal
    return lines


def _running_lines(pages_lines: list[list[str]], n_pages: int, min_fraction: float = 0.6) -> set[str]:
    """Exact lines recurring as the first/last line of many pages (headers/footers)."""
    if n_pages < 3:
        return set()
    firsts: Counter[str] = Counter()
    lasts: Counter[str] = Counter()
    for lines in pages_lines:
        if lines:
            firsts[lines[0]] += 1
            lasts[lines[-1]] += 1
    threshold = max(2, int(n_pages * min_fraction))
    recurring: set[str] = set()
    for counter in (firsts, lasts):
        for line, count in counter.items():
            if count >= threshold and len(line) < 120:
                recurring.add(line)
    return recurring


def _clean_lines(lines: list[str], recurring: set[str]) -> str:
    out: list[str] = []
    for line in lines:
        line = _MULTISPACE.sub(" ", line).strip()
        if not line:
            out.append("")  # preserve paragraph-break signal
            continue
        if line in recurring or _PAGE_NUM_LINE.match(line) or _PAGE_FRAC_LINE.match(line):
            continue
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_pdf(pdf_path: Path) -> tuple[str, int]:
    """Return (cleaned_text, n_pages) for one PDF."""
    pages_lines: list[list[str]] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            pages_lines.append(_page_lines(page))

    nonempty = [[ln.strip() for ln in pl if ln.strip()] for pl in pages_lines]
    recurring = _running_lines(nonempty, len(pages_lines))

    parts = [
        f"--- Page {i} ---\n{_clean_lines(pl, recurring)}".rstrip()
        for i, pl in enumerate(pages_lines, start=1)
    ]
    text = "\n\n".join(parts).strip() + "\n"
    text = _HYPHEN_LINEBREAK.sub(r"\1\2", text)  # de-hyphenate line-break splits
    return text, len(pages_lines)


def extract_one(cfg: Config, row: SourceRow, *, force: bool = False) -> ExtractResult:
    pdf_path = raw_pdf_path(cfg, row)
    out_path = text_path(cfg, row)
    if not pdf_path.exists():
        return ExtractResult(row, "skipped", "no PDF on disk (run fetch first)")
    if out_path.exists() and not force:
        return ExtractResult(row, "cached", f"{out_path.name} already present", path=out_path)
    try:
        text, n_pages = extract_pdf(pdf_path)
    except Exception as exc:  # a corrupt PDF must not crash the batch
        return ExtractResult(row, "skipped", f"extraction failed: {type(exc).__name__}: {exc}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    n_words = len(text.split())
    return ExtractResult(
        row, "extracted", f"{n_pages} pages, {n_words:,} words -> {out_path.name}",
        n_pages=n_pages, n_words=n_words, path=out_path,
    )


def extract_all(cfg: Config, rows: list[SourceRow], *, force: bool = False) -> list[ExtractResult]:
    results: list[ExtractResult] = []
    for row in rows:
        result = extract_one(cfg, row, force=force)
        results.append(result)
        print(f"  [{result.status:>9}] {row.company_slug}_{row.year}: {result.detail}")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.ingest.extract",
        description="Extract cleaned text from downloaded statement PDFs.",
    )
    ap.add_argument("--company", metavar="SLUG", help="Only extract this company.")
    ap.add_argument("--force", action="store_true", help="Re-extract even if text exists.")
    args = ap.parse_args()

    cfg = load_config()
    cfg.ensure_dirs()
    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]
    if not rows:
        print("No matching rows in sources.csv.")
        return

    print(f"Extracting {len(rows)} statement(s):")
    results = extract_all(cfg, rows, force=args.force)
    counts = Counter(r.status for r in results)
    print(f"\nSummary: {dict(counts)}")


if __name__ == "__main__":
    main()
