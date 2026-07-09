"""Attribution: why did the combined scorer's scores move?

The combined+thinking-DISABLED delta bundles two changes vs the legacy snapshot
(combining six calls into one, and disabling thinking). This isolates them by
running the combined scorer with thinking ADAPTIVE and bucketing each dimension
that changed under thinking-disabled:

  * adaptive == snapshot          -> thinking-off artifact (re-enabling thinking recovers it)
  * adaptive == disabled (!=snap) -> structural to combining (adjudicate)
  * adaptive == a third value     -> borderline-unstable (adjudicate / widen sampling)

It also measures combined+adaptive cost, so the "re-enable thinking?" decision
has a number: C_on (adaptive) vs C_off (disabled, from data/scorer_diff.json).
Reads the committed snapshot read-only; writes data/attribution.json.

CLI:
    python -m src.attribution [--company SLUG] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_config, require_api_key
from .diff_scorers import _est_cost, _live_calls, _load_snapshot, _tok_totals
from .pipeline.score import score_for_row
from .sources import load_sources, text_path


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.attribution",
        description="Bucket combined-scorer changes into thinking-off artifact vs structural.")
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--diff", default=None, help="scorer_diff.json (default: data/scorer_diff.json).")
    ap.add_argument("--out", default=None, help="Output JSON (default: data/attribution.json).")
    args = ap.parse_args()

    cfg = load_config()
    require_api_key()
    # Toggle the combined scorer into adaptive-thinking mode for this run only
    # (in-process; config.yaml on disk stays "disabled"). Fresh "ca" cache namespace.
    cfg.llm["combined_scoring_thinking"] = "adaptive"

    snap_path = cfg.root / "dashboard" / "data.json"
    snapshot = _load_snapshot(snap_path)
    diff_path = Path(args.diff) if args.diff else (cfg.path("db_path").parent / "scorer_diff.json")
    diff = json.loads(diff_path.read_text(encoding="utf-8"))
    # off-mode (combined + thinking disabled) score per (statement, dim), and the changed set
    off_score = {(r["statement"], r["dimension"]): r["new_score"] for r in diff["per_dim_rows"]}
    changed = {(r["statement"], r["dimension"]) for r in diff["changed_rows"]}
    c_off = diff["cost_usd"]["new_measured"]

    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]
    rows = [r for r in rows if (r.company_slug, r.year) in snapshot and text_path(cfg, r).exists()]

    sink: list[dict[str, Any]] = []
    adaptive_score: dict[tuple[str, int], int] = {}
    per_statement_calls: dict[str, int] = {}
    for row in rows:
        sid = f"{row.company_slug}_{row.year}"
        print(f"== {sid} : combined + ADAPTIVE (live) ==", flush=True)
        st_sink: list[dict[str, Any]] = []
        scores = score_for_row(cfg, row, use_cache=True, combined=True, usage_sink=st_sink) or []
        for s in scores:
            adaptive_score[(sid, s.dimension)] = s.score
        sink += st_sink
        per_statement_calls[sid] = len(_live_calls(st_sink))

    # Bucket every dimension that changed under thinking-disabled.
    buckets: dict[str, list[dict[str, Any]]] = {"artifact": [], "structural": [], "unstable": []}
    for r in diff["changed_rows"]:
        key = (r["statement"], r["dimension"])
        snap_s, off_s = r["old_score"], r["new_score"]
        adp_s = adaptive_score.get(key)
        if adp_s == snap_s:
            bucket = "artifact"
        elif adp_s == off_s:
            bucket = "structural"
        else:
            bucket = "unstable"
        buckets[bucket].append({
            "statement": r["statement"], "dimension": r["dimension"], "name": r["name"],
            "snapshot": snap_s, "disabled": off_s, "adaptive": adp_s,
            "direction": "down" if r["delta"] < 0 else "up",
        })

    # Adaptive may ALSO move dimensions that were unchanged under disabled — surface those.
    new_divergences = []
    for (sid, dim), adp in adaptive_score.items():
        snap_s = snapshot.get((sid.rsplit("_", 1)[0], int(sid.rsplit("_", 1)[1])), {}).get(dim, {}).get("score")
        if snap_s is not None and adp != snap_s and (sid, dim) not in changed:
            new_divergences.append({"statement": sid, "dimension": dim,
                                    "snapshot": snap_s, "adaptive": adp})

    c_on = round(_est_cost(sink, cfg.pricing), 4)
    tok = _tok_totals(sink)

    def _dirs(items):
        return {"down": sum(1 for x in items if x["direction"] == "down"),
                "up": sum(1 for x in items if x["direction"] == "up")}

    report = {
        "changed_under_disabled": len(diff["changed_rows"]),
        "buckets": {k: {"count": len(v), **_dirs(v), "rows": v} for k, v in buckets.items()},
        "new_divergences_under_adaptive": new_divergences,
        "cost_usd": {"combined_disabled_C_off": c_off, "combined_adaptive_C_on": c_on,
                     "premium_x": round(c_on / c_off, 2) if c_off else None},
        "adaptive_tokens": tok,
        "adaptive_live_calls": len(_live_calls(sink)),
    }

    print("\n" + "=" * 64)
    print("ATTRIBUTION  —  combined+disabled  vs  combined+adaptive")
    print("=" * 64)
    for k in ("artifact", "structural", "unstable"):
        b = report["buckets"][k]
        print(f"  {k:<11}: {b['count']:>2}  (down {b['down']}, up {b['up']})")
    print(f"  new divergences under adaptive (were unchanged): {len(new_divergences)}")
    print(f"  cost: C_off=${c_off}  C_on=${c_on}  premium={report['cost_usd']['premium_x']}x")
    print("\n  downgrade rows (the ones the skew is about):")
    for k in ("artifact", "structural", "unstable"):
        for x in report["buckets"][k]["rows"]:
            if x["direction"] == "down":
                print(f"    [{k:<10}] {x['statement']:<20} dim{x['dimension']} "
                      f"snap={x['snapshot']} off={x['disabled']} adaptive={x['adaptive']}")

    out = Path(args.out) if args.out else (cfg.path("db_path").parent / "attribution.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nfull report: {out}")


if __name__ == "__main__":
    main()
