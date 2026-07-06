"""CLI entrypoint: python -m src.run --all | --company <slug> [--force].

Orchestrates the full pipeline end-to-end — fetch -> extract -> claims -> score
-> diff -> aggregate -> persist -> export dashboard JSON. Every stage is
idempotent and cache-backed, so re-runs are cheap and deterministic.
"""
from __future__ import annotations

import argparse
from statistics import mean

from . import store
from .config import Config, load_config, require_api_key
from .ingest.extract import extract_all
from .ingest.fetch import fetch_all
from .pipeline.diff import analyze_yoy
from .pipeline.score import score_for_row
from .schemas import BoilerplateResult, DimensionScore, SourceRow, StatementScore
from .sources import load_sources, text_path


def build_statement_score(
    cfg: Config, row: SourceRow, dim_scores: list[DimensionScore], boilerplate: BoilerplateResult
) -> StatementScore:
    """Overall = mean of dims 1-6, penalized by boilerplate (cap + flag if share > threshold)."""
    overall = round(mean(s.score for s in dim_scores), 2) if dim_scores else 0.0
    flags: list[str] = []
    boilerplate_flag = False
    share = boilerplate.boilerplate_share
    cap_share = float(cfg.thresholds["boilerplate_cap_share"])
    cap = float(cfg.thresholds["boilerplate_overall_cap"])
    if share is not None and share > cap_share:
        boilerplate_flag = True
        flags.append(
            f"Substantially unchanged from prior year "
            f"({round(share * 100)}% of paragraphs identical to {boilerplate.prior_year})"
        )
        overall = min(overall, cap)
    return StatementScore(
        company_slug=row.company_slug, company_name=row.company_name, sector=row.sector,
        year=row.year, dimension_scores=dim_scores, boilerplate=boilerplate,
        overall_score=overall, boilerplate_flag=boilerplate_flag, flags=flags,
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.run",
        description="Score corporate modern slavery statements for disclosure quality.",
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="Process every row in sources.csv.")
    g.add_argument("--company", metavar="SLUG", help="Process a single company by slug.")
    ap.add_argument("--force", action="store_true", help="Bypass LLM caches (re-extract and re-score).")
    args = ap.parse_args()

    cfg = load_config()
    cfg.ensure_dirs()
    require_api_key()
    all_rows = load_sources(cfg)
    subset = all_rows if args.all else [r for r in all_rows if r.company_slug == args.company]
    if not subset:
        print("No matching rows in sources.csv.")
        return

    print("== fetch ==")
    fetch_all(cfg, subset)
    print("\n== extract ==")
    extract_all(cfg, subset)

    conn = store.connect(cfg)
    store.init_db(conn)
    results: list[StatementScore] = []

    print("\n== claims -> score -> diff -> persist ==")
    for row in subset:
        if not text_path(cfg, row).exists():
            print(f"  {row.company_slug}_{row.year}: no extracted text — skipped")
            continue
        dim_scores = score_for_row(cfg, row, use_cache=not args.force) or []
        boilerplate, pairs = analyze_yoy(cfg, row, all_rows)
        statement = build_statement_score(cfg, row, dim_scores, boilerplate)
        store.save_statement(conn, statement, pairs)
        results.append(statement)
        note = ""
        if statement.boilerplate_flag:
            note = f"  [BOILERPLATE {round(boilerplate.boilerplate_share * 100)}%]"
        print(f"  {row.company_slug}_{row.year}: overall {statement.overall_score}{note}")

    out = store.export_json(cfg, conn)
    conn.close()

    print("\n== leaderboard ==")
    for s in sorted(results, key=lambda x: x.overall_score, reverse=True):
        dims = " ".join(str(d.score) for d in s.dimension_scores)
        flag = "  (boilerplate)" if s.boilerplate_flag else ""
        print(f"  {s.overall_score:>4.2f}  {s.company_name} {s.year} [{dims}]{flag}")

    print(f"\nDB:             {cfg.path('db_path')}")
    print(f"Dashboard data: {out}")


if __name__ == "__main__":
    main()
