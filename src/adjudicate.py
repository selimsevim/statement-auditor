"""Adjudication worksheet: the human-decision instrument for the scorer change.

For every dimension whose score (or fallback flag) moved between the committed
snapshot (legacy scorer) and the combined scorer, this emits one worksheet entry
containing the rubric text, both scores, and BOTH sides' cited evidence and
justification — everything a human needs to mark a winner, and nothing that
pre-judges the outcome.

The acceptance CRITERION is a process, not a threshold this tool computes: a
human reads the rubric + evidence + both scores and marks legacy / combined /
neither for each row. The maintainer owns the accept-or-reject decision and any
decision rule over those marks; this document does not assert one.

Reads the committed snapshot (old side) and re-runs the combined scorer
cache-served (new side) — no API calls, deterministic. Writes Markdown.

CLI:
    python -m src.adjudicate [--company SLUG] [--snapshot PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import Config, load_config
from .pipeline.score import score_for_row
from .sources import load_sources, text_path
from .taxonomy import DIMENSIONS, RUBRIC


def _load_snapshot(path: Path) -> dict[tuple[str, int], dict[int, dict[str, Any]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[str, int], dict[int, dict[str, Any]]] = {}
    for s in data["statements"]:
        out[(s["slug"], s["year"])] = {
            d["dimension"]: {
                "score": d["score"],
                "justification": d.get("justification", ""),
                "evidence": [e["quote"] for e in d.get("evidence", [])],
                "fallback": bool(d.get("fallback", False)),
            }
            for d in s["dimensions"]
        }
    return out


def _rubric_block() -> str:
    return "\n".join(f"| {k} | {v} |" for k, v in RUBRIC.items())


def _evidence_md(quotes: list[str]) -> str:
    if not quotes:
        return "    _(none)_"
    return "\n".join(f"    - {' '.join(q.split())!r}" for q in quotes)


def _load_attribution(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """(statement, dim) -> {bucket, snapshot, disabled, adaptive} from attribution.json."""
    if not path.exists():
        return {}
    aj = json.loads(path.read_text(encoding="utf-8"))
    out: dict[tuple[str, int], dict[str, Any]] = {}
    for bucket, obj in aj["buckets"].items():
        for r in obj["rows"]:
            out[(r["statement"], r["dimension"])] = {"bucket": bucket, **r}
    return out


_ATTR_TAIL = {
    "artifact": "reverts to the snapshot score under adaptive thinking — re-enabling thinking recovers it",
    "structural": "adaptive keeps the combined score — thinking does NOT recover it; adjudicate",
    "unstable": "adaptive lands on a third value — genuinely borderline; adjudicate / widen sampling",
}


def _attribution_line(attr: dict[str, Any] | None) -> str:
    if attr is None:  # run not done yet: blank tick-boxes
        return ("**Attribution (fill after combined+adaptive run):** ☐ thinking-off artifact "
                "(reverts) ☐ structural to combining ☐ borderline-unstable (third value)\n")
    b = attr["bucket"]
    mark = {k: ("☑" if k == b else "☐") for k in ("artifact", "structural", "unstable")}
    return (f"**Attribution:** {mark['artifact']} thinking-off artifact  "
            f"{mark['structural']} structural to combining  {mark['unstable']} borderline-unstable  "
            f"(snapshot={attr['snapshot']}, disabled={attr['disabled']}, adaptive={attr['adaptive']}) — "
            f"{_ATTR_TAIL[b]}\n")


def build_worksheet(cfg: Config, snap_path: Path, company: str | None) -> tuple[str, int]:
    snapshot = _load_snapshot(snap_path)
    attr_map = _load_attribution(cfg.path("db_path").parent / "attribution.json")
    rows = [r for r in load_sources(cfg)
            if (r.company_slug, r.year) in snapshot and text_path(cfg, r).exists()
            and (company is None or r.company_slug == company)]

    entries: list[str] = []
    summary: list[str] = []
    n_changed = 0
    for row in rows:
        key = (row.company_slug, row.year)
        sid = f"{row.company_slug}_{row.year}"
        # cache-served (combined samples + fallbacks are all cached) -> free, deterministic
        new_scores = score_for_row(cfg, row, use_cache=True, combined=True) or []
        new_by_dim = {s.dimension: s for s in new_scores}
        snap = snapshot[key]

        for d in DIMENSIONS:
            old = snap.get(d)
            new = new_by_dim.get(d)
            if old is None or new is None:
                continue
            if old["score"] == new.score and old["fallback"] == new.fallback:
                continue
            n_changed += 1
            meta = DIMENSIONS[d]
            delta = new.score - old["score"]
            # Attribution only matters for downgrades — the down-skew is what we're
            # explaining. Upgrades still get a winner line, but no attribution row.
            attribution = _attribution_line(attr_map.get((sid, d))) if delta < 0 else ""
            summary.append(
                f"| {sid} | {d} {meta['name']} | {old['score']} | {new.score} | "
                f"{delta:+d} | {old['fallback']}→{new.fallback} | |")
            entries.append(
                f"### {sid} — Dimension {d}: {meta['name']} (UK MSA s.{meta['s54']})\n\n"
                f"**Rubric (0–4):**\n\n| score | meaning |\n|---|---|\n{_rubric_block()}\n\n"
                f"Dimension question: {meta['description']}\n\n"
                f"**LEGACY (committed snapshot): score = {old['score']}"
                f"{' · fallback' if old['fallback'] else ''}**\n"
                f"- justification: {old['justification']}\n"
                f"- evidence:\n{_evidence_md(old['evidence'])}\n\n"
                f"**COMBINED (new): score = {new.score}"
                f"{' · fallback' if new.fallback else ''}**\n"
                f"- justification: {new.justification}\n"
                f"- evidence:\n{_evidence_md(new.evidence_quotes)}\n\n"
                f"**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score\n"
                f"{attribution}"
                f"**Notes:** \n\n---\n")

    header = (
        "# Scorer change — adjudication worksheet\n\n"
        "One entry per dimension whose score or fallback flag moved between the committed "
        "snapshot (legacy per-dimension scorer) and the combined single-call scorer.\n\n"
        "**How to use this (the criterion is this process, not a number):** for each entry, "
        "read the rubric, read the cited evidence on both sides, and tick a winner — the "
        "score the rubric + evidence better support. The maintainer owns the accept/reject "
        "decision and any rule over these marks (e.g. how many combined-wins-or-ties are "
        "required, and how to treat statements whose overall moved > 0.2). This tool does "
        "not assert that rule.\n\n"
        f"Changed dimensions: **{n_changed}**\n\n"
        "| statement | dimension | old | new | Δ | fallback | winner |\n"
        "|---|---|---|---|---|---|---|\n" + "\n".join(summary) + "\n\n---\n\n")
    return header + "\n".join(entries), n_changed


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.adjudicate",
        description="Emit the human adjudication worksheet for changed dimensions.")
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--snapshot", default=None, help="Snapshot JSON (default: dashboard/data.json).")
    ap.add_argument("--out", default=None, help="Worksheet path (default: data/adjudication_worksheet.md).")
    args = ap.parse_args()

    cfg = load_config()
    snap_path = Path(args.snapshot) if args.snapshot else (cfg.root / "dashboard" / "data.json")
    md, n = build_worksheet(cfg, snap_path, args.company)

    out = Path(args.out) if args.out else (cfg.path("db_path").parent / "adjudication_worksheet.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"{n} changed dimensions -> {out}")


if __name__ == "__main__":
    main()
