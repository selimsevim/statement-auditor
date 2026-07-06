"""Pass 0a — download statement PDFs listed in sources.csv.

Downloads each `pdf_url`, following redirects, and saves it to
data/raw/{company_slug}_{year}.pdf. Sends a browser User-Agent (some hosts
block naive clients). Validation is by magic bytes (%PDF within the first
1 KB), so HTML landing pages returned with HTTP 200 are caught. Every failure
mode — 403, 404, timeout, non-PDF body — is logged and skipped; a single bad
URL never crashes the batch.

CLI:
    python -m src.ingest.fetch [--company SLUG] [--force]
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import requests

from ..config import Config, load_config
from ..schemas import SourceRow
from ..sources import load_sources, raw_pdf_path

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = (10, 60)  # (connect, read) seconds


@dataclass
class FetchResult:
    row: SourceRow
    status: str  # downloaded | cached | skipped | error
    detail: str
    path: Path | None = None


def _looks_like_pdf(content: bytes) -> bool:
    return b"%PDF" in content[:1024]


def fetch_one(
    cfg: Config, row: SourceRow, session: requests.Session, *, force: bool = False
) -> FetchResult:
    dest = raw_pdf_path(cfg, row)
    if dest.exists() and not force:
        return FetchResult(row, "cached", f"{dest.name} already present", dest)
    try:
        resp = session.get(
            row.pdf_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True
        )
    except requests.RequestException as exc:
        return FetchResult(row, "error", f"request failed: {type(exc).__name__}: {exc}")

    ctype = resp.headers.get("Content-Type", "?")
    if resp.status_code != 200:
        note = " (blocked)" if resp.status_code == 403 else ""
        return FetchResult(row, "skipped", f"HTTP {resp.status_code}{note}, Content-Type {ctype}")

    content = resp.content
    if not _looks_like_pdf(content):
        return FetchResult(
            row,
            "skipped",
            f"not a PDF: HTTP 200, Content-Type {ctype}, {len(content):,} bytes "
            "(likely a landing page)",
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return FetchResult(row, "downloaded", f"{len(content):,} bytes, Content-Type {ctype}", dest)


def fetch_all(cfg: Config, rows: list[SourceRow], *, force: bool = False) -> list[FetchResult]:
    results: list[FetchResult] = []
    with requests.Session() as session:
        for row in rows:
            result = fetch_one(cfg, row, session, force=force)
            results.append(result)
            print(f"  [{result.status:>10}] {row.company_slug}_{row.year}: {result.detail}")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.ingest.fetch",
        description="Download statement PDFs listed in sources.csv.",
    )
    ap.add_argument("--company", metavar="SLUG", help="Only fetch this company.")
    ap.add_argument("--force", action="store_true", help="Re-download even if present.")
    args = ap.parse_args()

    cfg = load_config()
    cfg.ensure_dirs()
    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]
    if not rows:
        print("No matching rows in sources.csv.")
        return

    print(f"Fetching {len(rows)} statement(s):")
    results = fetch_all(cfg, rows, force=args.force)
    counts = Counter(r.status for r in results)
    print(f"\nSummary: {dict(counts)}")


if __name__ == "__main__":
    main()
