"""Pass 1 — claim extraction (haiku).

Extracts, for each of the six s.54(5) dimensions, verbatim claim quotes from a
statement's cleaned text, each tagged with a claim type. Long statements are
split into page-aware chunks; claims from all chunks are merged. Each structured
call is cached and validated (see src/llm.py); a chunk that fails after one retry
is logged and skipped rather than crashing the batch.

CLI:
    python -m src.pipeline.claims [--company SLUG] [--force]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter

from ..config import Config, load_config, require_api_key
from ..llm import LLMError, cached_structured
from ..schemas import ClaimsExtraction, SourceRow
from ..sources import load_sources, text_path
from ..taxonomy import CLAIM_TYPE_GUIDANCE, DIMENSIONS
from ..verify import normalize_for_match, quote_in_text


def _dimension_block() -> str:
    lines = []
    for num, d in DIMENSIONS.items():
        lines.append(f"  {num}. {d['name']} [s.{d['s54']}]: {d['description']}")
    return "\n".join(lines)


def _claim_type_block() -> str:
    return "\n".join(f"  - {name}: {desc}" for name, desc in CLAIM_TYPE_GUIDANCE.items())


CLAIMS_SYSTEM = f"""You analyse corporate modern slavery statements for DISCLOSURE QUALITY. \
You never assert that a company uses forced labour; you only extract what the \
statement says, so its specificity can be assessed.

Extract claims that speak to any of these six dimensions (from section 54(5) of \
the UK Modern Slavery Act 2015):
{_dimension_block()}

For every claim, assign exactly one claim_type:
{_claim_type_block()}

Rules:
- The `quote` MUST be copied VERBATIM from the provided text — an exact, \
contiguous substring. Do not paraphrase, summarise, fix typos, translate, or \
merge text across gaps. Copy the characters exactly as they appear.
- Keep each quote focused: one sentence or a short passage that stands on its own.
- `dimension` is the integer 1-6 the quote speaks to. If a quote speaks to more \
than one, pick the single best fit and emit one claim.
- `page_or_position` is the page the quote appears under, formatted like "p.7" \
(use the nearest preceding "--- Page N ---" marker).
- Extract the substantive claims for each dimension. It is fine for a dimension \
to have no claims if the text says nothing about it. Prefer specific, mechanism- \
or metric-bearing sentences, but include commitments/policies/generic statements \
too, tagged accordingly.
- Ignore navigation banners, headers, footers, page numbers, and contents lists."""


def build_user_prompt(text_chunk: str) -> str:
    return (
        "Extract all claims from the modern slavery statement text below. "
        "Remember: every quote must be an exact, contiguous substring of this text.\n\n"
        "=== STATEMENT TEXT ===\n"
        f"{text_chunk}"
    )


def chunk_pages(text: str, budget: int) -> list[str]:
    """Split into page-aware chunks under `budget` characters, keeping page markers."""
    parts = [p for p in re.split(r"(?=--- Page \d+ ---)", text) if p]
    chunks: list[str] = []
    current = ""
    for part in parts:
        if current and len(current) + len(part) > budget:
            chunks.append(current)
            current = part
        else:
            current += part
    if current.strip():
        chunks.append(current)
    return chunks or [text]


def extract_claims(cfg: Config, text: str, *, use_cache: bool = True) -> ClaimsExtraction:
    model = cfg.models["extraction"]
    max_tokens = int(cfg.llm["max_tokens"])
    retries = int(cfg.llm.get("parse_retries", 1))
    chunks = chunk_pages(text, int(cfg.llm["chunk_char_budget"]))

    all_claims = []
    for i, chunk in enumerate(chunks, start=1):
        try:
            part = cached_structured(
                cfg,
                model=model,
                system=CLAIMS_SYSTEM,
                user=build_user_prompt(chunk),
                response_model=ClaimsExtraction,
                max_tokens=max_tokens,
                use_cache=use_cache,
                retries=retries,
            )
        except LLMError as exc:
            print(f"      chunk {i}/{len(chunks)}: skipped ({exc})")
            continue
        all_claims.extend(part.claims)
    return ClaimsExtraction(claims=all_claims)


def extract_for_row(cfg: Config, row: SourceRow, *, use_cache: bool = True) -> ClaimsExtraction | None:
    path = text_path(cfg, row)
    if not path.exists():
        return None
    return extract_claims(cfg, path.read_text(encoding="utf-8"), use_cache=use_cache)


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.pipeline.claims",
        description="Extract dimension claims from statement text (LLM pass 1).",
    )
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--force", action="store_true", help="Bypass the response cache.")
    args = ap.parse_args()

    cfg = load_config()
    require_api_key()
    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]

    for row in rows:
        path = text_path(cfg, row)
        if not path.exists():
            print(f"{row.company_slug}_{row.year}: no extracted text (run extract first) — skipped")
            continue
        print(f"\n{row.company_slug}_{row.year} ({cfg.models['extraction']}):")
        extraction = extract_for_row(cfg, row, use_cache=not args.force)
        claims = extraction.claims if extraction else []

        by_dim = Counter(c.dimension for c in claims)
        by_type = Counter(c.claim_type.value for c in claims)
        normalized_source = normalize_for_match(path.read_text(encoding="utf-8"))
        verbatim = sum(quote_in_text(c.quote, normalized_source) for c in claims)

        print(f"  claims: {len(claims)}")
        print("  by dimension: " + ", ".join(f"{DIMENSIONS[d]['name']}={by_dim.get(d, 0)}" for d in DIMENSIONS))
        print(f"  by type: {dict(by_type)}")
        pct = (100 * verbatim / len(claims)) if claims else 0.0
        print(f"  verbatim quotes matched in source: {verbatim}/{len(claims)} ({pct:.0f}%)")
        for c in claims[:2]:
            ok = "OK" if quote_in_text(c.quote, normalized_source) else "NO-MATCH"
            print(f"    [{ok}] dim {c.dimension} {c.claim_type.value} {c.page_or_position}: {c.quote[:90]!r}")


if __name__ == "__main__":
    main()
