"""Load and locate statement sources.

Centralises reading sources.csv into validated `SourceRow`s and the on-disk
naming convention `{company_slug}_{year}` for raw PDFs and extracted text, so
every stage refers to the same files.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .config import Config
from .schemas import SourceRow


def load_sources(cfg: Config) -> list[SourceRow]:
    """Read sources.csv into validated rows. Blank and '#'-commented rows are skipped."""
    rows: list[SourceRow] = []
    with open(cfg.path("sources_csv"), newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            slug = (raw.get("company_slug") or "").strip()
            if not slug or slug.startswith("#"):
                continue
            rows.append(
                SourceRow(
                    company_slug=slug,
                    company_name=(raw.get("company_name") or "").strip(),
                    sector=(raw.get("sector") or "").strip(),
                    year=int(raw["year"]),
                    pdf_url=(raw.get("pdf_url") or "").strip(),
                )
            )
    return rows


def raw_pdf_path(cfg: Config, row: SourceRow) -> Path:
    return cfg.path("raw_dir") / f"{row.company_slug}_{row.year}.pdf"


def text_path(cfg: Config, row: SourceRow) -> Path:
    return cfg.path("text_dir") / f"{row.company_slug}_{row.year}.txt"
