"""SQLite persistence — single file, no server.

Stores one row per statement plus child rows for dimension scores, verified
evidence spans, and year-over-year paragraph pairs. Writes are idempotent
(replace-on-conflict by slug+year), so re-running the pipeline is safe. Also
exports a single dashboard-ready JSON.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .schemas import ParagraphPair, StatementScore
from .sources import load_sources
from .taxonomy import DIMENSIONS

_SCHEMA = """
CREATE TABLE IF NOT EXISTS statements (
  slug TEXT NOT NULL, year INTEGER NOT NULL,
  company_name TEXT, sector TEXT,
  overall_score REAL, boilerplate_flag INTEGER, flags TEXT,
  prior_year INTEGER, boilerplate_share REAL,
  n_paragraphs INTEGER, n_unchanged INTEGER, hedge_density REAL,
  updated_at TEXT,
  PRIMARY KEY (slug, year)
);
CREATE TABLE IF NOT EXISTS dimension_scores (
  slug TEXT NOT NULL, year INTEGER NOT NULL, dimension INTEGER NOT NULL,
  score INTEGER, justification TEXT, fallback INTEGER,
  PRIMARY KEY (slug, year, dimension)
);
CREATE TABLE IF NOT EXISTS evidence (
  slug TEXT NOT NULL, year INTEGER NOT NULL, dimension INTEGER NOT NULL,
  idx INTEGER NOT NULL, quote TEXT
);
CREATE TABLE IF NOT EXISTS paragraph_pairs (
  slug TEXT NOT NULL, year INTEGER NOT NULL, prior_year INTEGER,
  cur_index INTEGER, cur_text TEXT, prior_index INTEGER, prior_text TEXT,
  similarity REAL, unchanged INTEGER
);
CREATE INDEX IF NOT EXISTS ix_dim ON dimension_scores (slug, year);
CREATE INDEX IF NOT EXISTS ix_ev ON evidence (slug, year, dimension);
CREATE INDEX IF NOT EXISTS ix_pp ON paragraph_pairs (slug, year);
"""


def connect(cfg: Config) -> sqlite3.Connection:
    cfg.path("db_path").parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(cfg.path("db_path"))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def save_statement(conn: sqlite3.Connection, score: StatementScore, pairs: list[ParagraphPair]) -> None:
    slug, year = score.company_slug, score.year
    bp = score.boilerplate
    # idempotent: clear any prior rows for this statement
    for tbl in ("statements", "dimension_scores", "evidence", "paragraph_pairs"):
        conn.execute(f"DELETE FROM {tbl} WHERE slug=? AND year=?", (slug, year))

    conn.execute(
        """INSERT INTO statements VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            slug, year, score.company_name, score.sector,
            score.overall_score, int(score.boilerplate_flag), json.dumps(score.flags),
            bp.prior_year, bp.boilerplate_share, bp.n_paragraphs, bp.n_unchanged_paragraphs,
            bp.hedge_density, datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )
    for ds in score.dimension_scores:
        conn.execute(
            "INSERT INTO dimension_scores VALUES (?,?,?,?,?,?)",
            (slug, year, ds.dimension, ds.score, ds.justification, int(ds.fallback)),
        )
        for i, quote in enumerate(ds.evidence_quotes):
            conn.execute(
                "INSERT INTO evidence VALUES (?,?,?,?,?)", (slug, year, ds.dimension, i, quote)
            )
    for p in pairs:
        conn.execute(
            "INSERT INTO paragraph_pairs VALUES (?,?,?,?,?,?,?,?,?)",
            (slug, year, bp.prior_year, p.cur_index, p.cur_text, p.prior_index,
             p.prior_text, p.similarity, int(p.unchanged)),
        )
    conn.commit()


def export_json(cfg: Config, conn: sqlite3.Connection) -> Path:
    """Write a single dashboard-ready JSON from the DB. Returns its path.

    Evidence carries character offsets into the statement's full text, computed
    HERE (exact substring — the stored span is a verbatim slice of the source),
    so the evidence view highlights by offset and never re-matches in the browser.
    Statements are ordered by overall score (desc), then hedge density (asc) as a
    deterministic tie-break.
    """
    source_url = {(r.company_slug, r.year): r.pdf_url for r in load_sources(cfg)}
    statements = []
    for s in conn.execute(
        "SELECT * FROM statements ORDER BY overall_score DESC, hedge_density ASC, slug"
    ):
        text_file = cfg.path("text_dir") / f"{s['slug']}_{s['year']}.txt"
        full_text = text_file.read_text(encoding="utf-8") if text_file.exists() else ""

        dims = []
        for d in conn.execute(
            "SELECT * FROM dimension_scores WHERE slug=? AND year=? ORDER BY dimension",
            (s["slug"], s["year"]),
        ):
            ev = []
            for r in conn.execute(
                "SELECT quote FROM evidence WHERE slug=? AND year=? AND dimension=? ORDER BY idx",
                (s["slug"], s["year"], d["dimension"]),
            ):
                quote = r["quote"]
                start = full_text.find(quote)  # exact: quote is a verbatim source slice
                ev.append({"quote": quote, "start": start,
                           "end": (start + len(quote)) if start >= 0 else -1})
            meta = DIMENSIONS[d["dimension"]]
            dims.append({
                "dimension": d["dimension"], "name": meta["name"], "s54": meta["s54"],
                "score": d["score"], "justification": d["justification"],
                "fallback": bool(d["fallback"]), "evidence": ev,
            })
        pairs = [
            dict(r) for r in conn.execute(
                "SELECT cur_index, cur_text, prior_index, prior_text, similarity, unchanged "
                "FROM paragraph_pairs WHERE slug=? AND year=? ORDER BY cur_index",
                (s["slug"], s["year"]),
            )
        ]
        statements.append({
            "slug": s["slug"], "year": s["year"], "company_name": s["company_name"],
            "sector": s["sector"], "overall_score": s["overall_score"],
            "source_url": source_url.get((s["slug"], s["year"]), ""),
            "boilerplate_flag": bool(s["boilerplate_flag"]), "flags": json.loads(s["flags"]),
            "boilerplate": {
                "prior_year": s["prior_year"], "share": s["boilerplate_share"],
                "n_paragraphs": s["n_paragraphs"], "n_unchanged": s["n_unchanged"],
                "hedge_density": s["hedge_density"],
            },
            "dimensions": dims,
            "paragraph_pairs": pairs,
            "text": full_text,
        })

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "boilerplate_similarity_threshold": cfg.thresholds["boilerplate_similarity"],
        "boilerplate_cap_share": cfg.thresholds["boilerplate_cap_share"],
        "statements": statements,
    }
    out = cfg.root / "dashboard" / "data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out
