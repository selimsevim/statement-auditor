"""Snapshot diff: legacy per-dimension scorer vs combined single-call scorer.

Runs both scorers over the sources and compares them against the committed
`dashboard/data.json` snapshot, making score movement auditable BEFORE any
further optimisation (Batch API, Haiku scorer). It does NOT touch the committed
snapshot or DB — it only reads them and writes a standalone report.

  * Legacy scorer  — run cache-served (deterministic; reproduces the snapshot).
  * Combined scorer — run live (its cache namespace is disjoint from legacy).

For each (statement, dimension) it reports old/new score, delta, old/new
evidence count, and old/new fallback usage; plus per-run parse failures, call
counts, measured NEW token usage, and an estimated cost before/after (pricing
from config.yaml). Cross-cutting credit — a claim filed under one dimension that
the combined scorer credits to another — shows up as a fallback=True dimension
whose score moved off 0, so it is visible here.

CLI:
    python -m src.diff_scorers [--company SLUG] [--limit N]
                               [--snapshot PATH] [--out PATH] [--force-new]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any

from .config import Config, load_config, require_api_key
from .pipeline.score import score_for_row
from .sources import load_sources, text_path
from .taxonomy import DIMENSIONS


def _load_snapshot(path: Path) -> dict[tuple[str, int], dict[int, dict[str, Any]]]:
    """Committed snapshot -> {(slug, year): {dim: {score, ev_count, fallback}}}."""
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[str, int], dict[int, dict[str, Any]]] = {}
    for s in data["statements"]:
        key = (s["slug"], s["year"])
        out[key] = {
            d["dimension"]: {
                "score": d["score"],
                "ev_count": len(d.get("evidence", [])),
                "fallback": bool(d.get("fallback", False)),
            }
            for d in s["dimensions"]
        }
    return out


def _live_calls(sink: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in sink if not r["cached"] and not r["error"]]


def _est_cost(sink: list[dict[str, Any]], pricing: dict[str, dict[str, float]]) -> float:
    """USD cost of the live (non-cached, non-error) calls in a usage sink."""
    total = 0.0
    for r in _live_calls(sink):
        pr = pricing.get(r["model"])
        if not pr:
            continue
        total += r["input_tokens"] / 1e6 * pr["input"] + r["output_tokens"] / 1e6 * pr["output"]
    return total


def _tok_totals(sink: list[dict[str, Any]]) -> dict[str, int]:
    live = _live_calls(sink)
    inp = sum(r["input_tokens"] for r in live)
    out = sum(r["output_tokens"] for r in live)
    return {"input": inp, "output": out, "thinking": 0, "total": inp + out}


def run_diff(cfg: Config, rows, snapshot: dict, *, force_new: bool) -> dict[str, Any]:
    pricing = cfg.pricing
    per_dim_rows: list[dict[str, Any]] = []
    per_statement: list[dict[str, Any]] = []
    old_sink_all: list[dict[str, Any]] = []
    new_sink_all: list[dict[str, Any]] = []
    snapshot_divergences: list[dict[str, Any]] = []
    parse_failures_new = 0
    parse_failures_old = 0

    for row in rows:
        key = (row.company_slug, row.year)
        if not text_path(cfg, row).exists() or key not in snapshot:
            continue
        sid = f"{row.company_slug}_{row.year}"
        print(f"\n== {sid} : legacy (cache) ==", flush=True)
        old_sink: list[dict[str, Any]] = []
        old_scores = score_for_row(cfg, row, use_cache=True, combined=False, usage_sink=old_sink) or []
        print(f"== {sid} : combined (live) ==", flush=True)
        new_sink: list[dict[str, Any]] = []
        new_scores = score_for_row(
            cfg, row, use_cache=not force_new, combined=True, usage_sink=new_sink) or []

        old_sink_all += old_sink
        new_sink_all += new_sink
        parse_failures_old += sum(1 for r in old_sink if r["error"])
        parse_failures_new += sum(1 for r in new_sink if r["error"])

        old_by_dim = {s.dimension: s for s in old_scores}
        new_by_dim = {s.dimension: s for s in new_scores}
        snap = snapshot[key]

        for d in DIMENSIONS:
            snap_d = snap.get(d, {"score": None, "ev_count": None, "fallback": None})
            old = old_by_dim.get(d)
            new = new_by_dim.get(d)
            # data-integrity: cache-served legacy should reproduce the committed snapshot
            if old is not None and snap_d["score"] is not None and old.score != snap_d["score"]:
                snapshot_divergences.append(
                    {"statement": sid, "dimension": d,
                     "snapshot_score": snap_d["score"], "legacy_rerun_score": old.score})
            old_score = snap_d["score"] if snap_d["score"] is not None else (old.score if old else None)
            old_ev = snap_d["ev_count"] if snap_d["ev_count"] is not None else (
                len(old.evidence_quotes) if old else None)
            old_fb = snap_d["fallback"] if snap_d["fallback"] is not None else (
                old.fallback if old else None)
            new_score = new.score if new else None
            delta = (new_score - old_score) if (new_score is not None and old_score is not None) else None
            per_dim_rows.append({
                "statement": sid, "dimension": d, "name": DIMENSIONS[d]["name"],
                "old_score": old_score, "new_score": new_score, "delta": delta,
                "old_evidence": old_ev,
                "new_evidence": len(new.evidence_quotes) if new else None,
                "old_fallback": old_fb,
                "new_fallback": new.fallback if new else None,
            })

        per_statement.append({
            "statement": sid,
            "old_calls": len(old_sink),
            "new_calls": len(new_sink),
            "old_live_calls": len(_live_calls(old_sink)),
            "new_live_calls": len(_live_calls(new_sink)),
        })

    old_calls = sum(p["old_calls"] for p in per_statement)
    new_calls = sum(p["new_calls"] for p in per_statement)
    new_tokens = _tok_totals(new_sink_all)
    new_cost = _est_cost(new_sink_all, pricing)

    # Old token usage is unrecoverable from the committed cache (it stores outputs,
    # not usage), so old cost is ESTIMATED by scaling old call count by the measured
    # per-call token average of the NEW combined calls. This understates the true
    # legacy cost: legacy additionally ran adaptive thinking (extra output tokens)
    # that the combined scorer disables. Treat call-count reduction as the exact
    # before/after signal; this dollar figure is a conservative estimate.
    new_live = _live_calls(new_sink_all)
    old_cost_est = None
    if new_live and pricing:
        avg_in = mean(r["input_tokens"] for r in new_live)
        avg_out = mean(r["output_tokens"] for r in new_live)
        model = cfg.models["scoring"]
        pr = pricing.get(model)
        if pr:
            old_cost_est = old_calls * (avg_in / 1e6 * pr["input"] + avg_out / 1e6 * pr["output"])

    changed = [r for r in per_dim_rows if r["delta"] not in (None, 0)]
    fb_changed = [r for r in per_dim_rows if r["old_fallback"] != r["new_fallback"]]
    largest = max((r for r in per_dim_rows if r["delta"] is not None),
                  key=lambda r: abs(r["delta"]), default=None)

    return {
        "statements_processed": len(per_statement),
        "dimensions_compared": len(per_dim_rows),
        "dimensions_changed": len(changed),
        "fallback_changed": len(fb_changed),
        "largest_delta": largest,
        "parse_failures": {"old": parse_failures_old, "new": parse_failures_new},
        "snapshot_divergences": snapshot_divergences,
        "calls": {
            "old_total": old_calls, "new_total": new_calls,
            "reduction_x": round(old_calls / new_calls, 2) if new_calls else None,
        },
        "tokens_new_measured": new_tokens,
        "cost_usd": {
            "new_measured": round(new_cost, 4),
            "old_estimated": round(old_cost_est, 4) if old_cost_est is not None else None,
            "note": "old_estimated is a rough lower bound (see source); new_measured is exact.",
        },
        "per_dim_rows": per_dim_rows,
        "per_statement": per_statement,
        "changed_rows": changed,
    }


def _print_report(rep: dict[str, Any]) -> None:
    print("\n" + "=" * 72)
    print("SCORER DIFF  —  legacy per-dimension  vs  combined single-call")
    print("=" * 72)
    print(f"statements processed : {rep['statements_processed']}")
    print(f"dimensions compared  : {rep['dimensions_compared']}")
    print(f"dimensions changed   : {rep['dimensions_changed']}")
    print(f"fallback flag changed: {rep['fallback_changed']}")
    print(f"parse failures       : old={rep['parse_failures']['old']}  new={rep['parse_failures']['new']}")
    if rep["snapshot_divergences"]:
        print(f"!! legacy-vs-snapshot divergences: {len(rep['snapshot_divergences'])} "
              "(cache did not reproduce snapshot — investigate)")
    else:
        print("legacy reproduces committed snapshot: YES")
    c = rep["calls"]
    print(f"scoring calls        : old={c['old_total']}  new={c['new_total']}  "
          f"reduction={c['reduction_x']}x")
    t = rep["tokens_new_measured"]
    print(f"new tokens (measured): input={t['input']}  output={t['output']}  "
          f"thinking={t['thinking']} (disabled)  total={t['total']}")
    cost = rep["cost_usd"]
    print(f"est. cost (USD)      : new={cost['new_measured']}  "
          f"old≈{cost['old_estimated']} (rough lower bound)")
    ld = rep["largest_delta"]
    if ld:
        print(f"largest score delta  : {ld['delta']:+d}  {ld['statement']} "
              f"dim{ld['dimension']} ({ld['name']}) {ld['old_score']}->{ld['new_score']}")

    if rep["changed_rows"]:
        print("\nchanged dimensions (old -> new):")
        print(f"  {'statement':<22} {'dim':<3} {'old':>3} {'new':>3} {'Δ':>3} "
              f"{'oldEv':>5} {'newEv':>5}  fallback(old->new)")
        for r in rep["changed_rows"]:
            fb = f"{r['old_fallback']}->{r['new_fallback']}"
            print(f"  {r['statement']:<22} {r['dimension']:<3} {str(r['old_score']):>3} "
                  f"{str(r['new_score']):>3} {r['delta']:>+3} {str(r['old_evidence']):>5} "
                  f"{str(r['new_evidence']):>5}  {fb}")
    else:
        print("\nNo dimension score changed.")


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.diff_scorers",
        description="Compare legacy vs combined scorer against the committed snapshot.")
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--limit", type=int, default=None, help="Process at most N statements.")
    ap.add_argument("--snapshot", default=None,
                    help="Snapshot JSON (default: dashboard/data.json).")
    ap.add_argument("--out", default=None,
                    help="Report JSON path (default: data/scorer_diff.json).")
    ap.add_argument("--force-new", action="store_true",
                    help="Bypass cache for the combined scorer (re-issue live calls).")
    args = ap.parse_args()

    cfg = load_config()
    require_api_key()
    snap_path = Path(args.snapshot) if args.snapshot else (cfg.root / "dashboard" / "data.json")
    snapshot = _load_snapshot(snap_path)

    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]
    rows = [r for r in rows if (r.company_slug, r.year) in snapshot and text_path(cfg, r).exists()]
    if args.limit is not None:
        rows = rows[: args.limit]

    rep = run_diff(cfg, rows, snapshot, force_new=args.force_new)
    _print_report(rep)

    out = Path(args.out) if args.out else (cfg.path("db_path").parent / "scorer_diff.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfull report: {out}")


if __name__ == "__main__":
    main()
