"""Dimension 7 — year-over-year similarity and boilerplate detection (computed).

No LLM. For a statement with a prior-year counterpart (same slug, year-1):
chunk both into paragraphs, embed with all-MiniLM-L6-v2, and for each current
paragraph take its maximum cosine similarity to any prior-year paragraph. The
boilerplate share is the fraction of current paragraphs at or above the
similarity threshold. Hedge-word density (hedge-lexicon occurrences per 1000
words) is computed for every statement regardless of a prior year.

`--calibrate` prints the similarity distribution plus example flagged-identical
and near-miss paragraph pairs, so the threshold can be set from real data.

CLI:
    python -m src.pipeline.diff [--company SLUG]
    python -m src.pipeline.diff --calibrate --company tesco
"""
from __future__ import annotations

import argparse
import re
from functools import lru_cache

from ..config import Config, load_config
from ..schemas import BoilerplateResult, ParagraphPair, SourceRow
from ..sources import load_sources, text_path

_PAGE_MARK = re.compile(r"^--- Page \d+ ---\s*", re.MULTILINE)


def paragraphs(text: str, min_words: int = 8) -> list[str]:
    """Split cleaned statement text into paragraphs for comparison.

    Page markers are removed, blocks are split on blank lines, internal
    whitespace is collapsed, and short fragments (headings, nav, stray bullets)
    are dropped so they don't pollute the similarity signal.
    """
    text = _PAGE_MARK.sub("", text)
    out: list[str] = []
    for chunk in re.split(r"\n\s*\n", text):
        para = " ".join(chunk.split())
        if len(para.split()) >= min_words:
            out.append(para)
    return out


def hedge_density(text: str, lexicon: list[str]) -> float:
    """Hedge-lexicon occurrences per 1000 words across the whole document."""
    words = len(text.split())
    if not words:
        return 0.0
    low = text.lower()
    hits = sum(low.count(phrase.lower()) for phrase in lexicon)
    return round(1000 * hits / words, 2)


@lru_cache(maxsize=1)
def _model(name: str):
    from sentence_transformers import SentenceTransformer  # heavy import, lazy

    return SentenceTransformer(name)


def max_similarities(cfg: Config, cur_paras: list[str], prev_paras: list[str]):
    """Return (max_sim per current paragraph, index of best prior paragraph)."""
    import numpy as np

    model = _model(cfg.models["embedding"])
    cur = model.encode(cur_paras, normalize_embeddings=True, show_progress_bar=False)
    prev = model.encode(prev_paras, normalize_embeddings=True, show_progress_bar=False)
    sim = np.asarray(cur) @ np.asarray(prev).T  # cosine (embeddings normalized)
    return sim.max(axis=1), sim.argmax(axis=1)


def prior_row(row: SourceRow, rows: list[SourceRow]) -> SourceRow | None:
    for r in rows:
        if r.company_slug == row.company_slug and r.year == row.year - 1:
            return r
    return None


def analyze_yoy(
    cfg: Config, row: SourceRow, rows: list[SourceRow]
) -> tuple[BoilerplateResult, list[ParagraphPair]]:
    """Return (boilerplate result, per-paragraph pairs) for one statement.

    Pairs are empty when there is no prior-year counterpart. They are persisted
    so the diff view can render side-by-side and the leaderboard can cite the
    concrete "N of M paragraphs carried over".
    """
    text = text_path(cfg, row).read_text(encoding="utf-8")
    hedge = hedge_density(text, cfg.hedge_lexicon)

    prev = prior_row(row, rows)
    if prev is None or not text_path(cfg, prev).exists():
        return BoilerplateResult(hedge_density=hedge), []

    threshold = float(cfg.thresholds["boilerplate_similarity"])
    cur_paras = paragraphs(text)
    prev_paras = paragraphs(text_path(cfg, prev).read_text(encoding="utf-8"))
    max_sim, best = max_similarities(cfg, cur_paras, prev_paras)

    pairs = [
        ParagraphPair(
            cur_index=i,
            cur_text=cur_paras[i],
            prior_index=int(best[i]),
            prior_text=prev_paras[int(best[i])],
            similarity=round(float(max_sim[i]), 4),
            unchanged=bool(max_sim[i] >= threshold),
        )
        for i in range(len(cur_paras))
    ]
    n_unchanged = sum(p.unchanged for p in pairs)
    share = round(n_unchanged / len(cur_paras), 3) if cur_paras else None
    result = BoilerplateResult(
        prior_year=prev.year,
        n_paragraphs=len(cur_paras),
        n_unchanged_paragraphs=n_unchanged,
        boilerplate_share=share,
        hedge_density=hedge,
    )
    return result, pairs


def compute_for_row(cfg: Config, row: SourceRow, rows: list[SourceRow]) -> BoilerplateResult:
    return analyze_yoy(cfg, row, rows)[0]


def _calibrate(cfg: Config, row: SourceRow, prev: SourceRow) -> None:
    import numpy as np

    cur_paras = paragraphs(text_path(cfg, row).read_text(encoding="utf-8"))
    prev_paras = paragraphs(text_path(cfg, prev).read_text(encoding="utf-8"))
    max_sim, best = max_similarities(cfg, cur_paras, prev_paras)

    print(f"Calibration: {row.company_slug} {prev.year} -> {row.year}")
    print(f"  current paragraphs: {len(cur_paras)}, prior paragraphs: {len(prev_paras)}")
    for lo in (0.99, 0.95, 0.92, 0.90, 0.85, 0.80, 0.70):
        print(f"  paragraphs with max-sim >= {lo:.2f}: {int((max_sim >= lo).sum())}")

    order = np.argsort(-max_sim)
    identical = [i for i in order if max_sim[i] >= 0.92][:5]
    near = [i for i in order if 0.80 <= max_sim[i] < 0.92][:5]

    def show(indices, label):
        print(f"\n===== {label} =====")
        for i in indices:
            j = int(best[i])
            print(f"[sim={max_sim[i]:.3f}]")
            print(f"  {row.year}: {cur_paras[i][:220]}")
            print(f"  {prev.year}: {prev_paras[j][:220]}")

    show(identical, "FLAGGED IDENTICAL (sim >= 0.92)")
    show(near, "NEAR-MISSES (0.80 <= sim < 0.92)")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.pipeline.diff",
        description="Year-over-year boilerplate + hedge density (dimension 7).",
    )
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--calibrate", action="store_true", help="Print similarity bands + example pairs.")
    args = ap.parse_args()

    cfg = load_config()
    rows = load_sources(cfg)
    subset = [r for r in rows if not args.company or r.company_slug == args.company]

    if args.calibrate:
        for row in subset:
            prev = prior_row(row, rows)
            if prev and text_path(cfg, prev).exists() and text_path(cfg, row).exists():
                _calibrate(cfg, row, prev)
        return

    for row in subset:
        if not text_path(cfg, row).exists():
            print(f"{row.company_slug}_{row.year}: no extracted text — skipped")
            continue
        bp = compute_for_row(cfg, row, rows)
        print(f"\n{row.company_slug}_{row.year}:")
        print(f"  hedge density: {bp.hedge_density} /1000 words")
        if bp.boilerplate_share is None:
            print("  boilerplate: n/a (no prior-year statement)")
        else:
            print(f"  boilerplate share vs {bp.prior_year}: {bp.boilerplate_share} "
                  f"({bp.n_unchanged_paragraphs}/{bp.n_paragraphs} paragraphs "
                  f">= {cfg.thresholds['boilerplate_similarity']} similarity)")


if __name__ == "__main__":
    main()
