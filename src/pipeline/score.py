"""Pass 2 — rubric scoring with evidence citation (sonnet).

Scores each of the six s.54(5) dimensions 0-4 against the rubric. The canonical
submission path uses the legacy one-call-per-dimension scorer; the combined
scorer can score all dimensions in one structured call per sample for audit and
cost comparison. Both paths pre-filter extracted claims to source-verified spans
before prompting, so any cited evidence is already source-matched.

After scoring, a post-hoc verifier re-checks each cited quote against the full
source text and keeps the exact source span (see src/verify.py). If a dimension
with a non-zero score loses all its evidence, it is re-scored once; if it still
has none, the score is forced to 0 and marked "no verifiable evidence" — an
uncited non-zero score is never displayed. Every call is cached (model, prompt
hash).

CLI:
    python -m src.pipeline.score [--company SLUG] [--force]
"""
from __future__ import annotations

import argparse
from statistics import mean
from typing import Any

from pydantic import BaseModel, Field

from ..config import Config, load_config, require_api_key
from ..llm import LLMError, cached_structured
from ..schemas import Claim, DimensionScore
from ..sources import load_sources, text_path
from ..taxonomy import DIMENSIONS, RUBRIC
from ..verify import NormIndex, build_norm_index, find_source_span, verify_quotes
from .claims import extract_for_row


class RawDimensionScore(BaseModel):
    """Internal LLM output shape; `dimension` is set by us, not the model."""

    score: int = Field(ge=0, le=4)
    justification: str
    evidence_quotes: list[str] = Field(default_factory=list)


class RawCombinedDimensionScore(BaseModel):
    """One dimension inside the combined-scoring output; `dimension` is the
    integer 1-6 the model is scoring (it labels its own entries here)."""

    dimension: int = Field(ge=1, le=6)
    score: int = Field(ge=0, le=4)
    justification: str
    evidence_quotes: list[str] = Field(default_factory=list)


class RawCombinedScore(BaseModel):
    """Internal LLM output shape for combined scoring: all six dimensions in a
    single structured call. Its own schema namespace keeps its cache keys
    disjoint from the legacy per-dimension `RawDimensionScore` cache."""

    scores: list[RawCombinedDimensionScore] = Field(default_factory=list)


def _rubric_block() -> str:
    return "\n".join(f"  {k}: {v}" for k, v in RUBRIC.items())


SCORING_SYSTEM = f"""You score ONE dimension of a corporate modern slavery statement for \
DISCLOSURE QUALITY — how specific and substantiated the disclosure is. You never \
assert that a company does or does not use forced labour; you assess only what the \
statement discloses.

Apply this 0-4 rubric:
{_rubric_block()}

Guidance:
- Judge ONLY from the claims provided below. If none are provided, score 0.
- Weigh claim types: `mechanism` and `metric` claims can support scores of 3-4; \
`commitment`, `policy_reference`, and `generic` claims on their own support at most 2.
- A 4 requires concrete mechanisms AND measurable evidence or outcomes (numbers, \
targets, results). A 3 requires concrete mechanisms but weak or no measurement.
- In `evidence_quotes`, copy 1-4 of the provided claim texts VERBATIM (exactly as \
written) — the ones that most justify your score. Never invent or paraphrase a quote.
- `justification`: 1-3 sentences tying the score to the cited evidence."""


COMBINED_SCORING_SYSTEM = f"""You score ALL SIX dimensions of a corporate modern slavery \
statement for DISCLOSURE QUALITY — how specific and substantiated each disclosure is. You \
never assert that a company does or does not use forced labour; you assess only what the \
statement discloses.

Apply this 0-4 rubric to EACH dimension independently:
{_rubric_block()}

Guidance:
- You are given the extracted claims grouped under each of the six dimensions below. Score \
every dimension and return one entry per dimension (1-6) in `scores`.
- Judge each dimension primarily from the claims listed under it. A claim listed under one \
dimension may also be relevant to another — if so, you may credit the other dimension from \
it, but only up to a score of 2 (a general/"mentioned" level) unless that dimension has its \
own mechanism/metric claims.
- If a dimension has NO relevant claims anywhere, score it 0 with empty evidence_quotes.
- Weigh claim types: `mechanism` and `metric` claims can support scores of 3-4; \
`commitment`, `policy_reference`, and `generic` claims on their own support at most 2.
- A 4 requires concrete mechanisms AND measurable evidence or outcomes (numbers, targets, \
results). A 3 requires concrete mechanisms but weak or no measurement.
- In each dimension's `evidence_quotes`, copy 1-4 of the provided claim texts VERBATIM \
(exactly as written) — the ones that most justify that dimension's score. Never invent or \
paraphrase a quote.
- Each `justification`: 1-3 sentences tying that dimension's score to its cited evidence."""


def _verified_claims(dim: int, claims: list[Claim], source: str, idx: NormIndex) -> list[tuple[str, str, str]]:
    """(source_span, claim_type, page) for this dimension's claims that verify."""
    out: list[tuple[str, str, str]] = []
    for c in claims:
        if c.dimension != dim:
            continue
        span = find_source_span(c.quote, idx, source)
        if span is not None:
            out.append((span, c.claim_type.value, c.page_or_position))
    return out


FALLBACK_SYSTEM = f"""You are re-checking whether a corporate modern slavery statement addresses \
ONE specific disclosure dimension. The claim extractor found NO claims for this dimension, so you \
are given the FULL statement text to double-check for relevant content that may have been filed \
under a different dimension. Assess DISCLOSURE QUALITY only — never assert whether forced labour \
occurs.

Apply this 0-4 rubric:
{_rubric_block()}

Guidance:
- Scan the full text for content relevant to THIS dimension only.
- If the statement genuinely does not address it, score 0 with empty evidence_quotes.
- A passing or generic mention with no substance is a 1; general commitments without mechanisms a 2.
- In evidence_quotes, copy VERBATIM (exactly) the sentence(s) relevant to this dimension. Never \
invent or paraphrase.
- justification: 1-2 sentences."""

_FALLBACK_NOTE = (
    "[Full-text fallback: no dimension-specific claims were extracted, so the full statement "
    "was re-scanned.] "
)


def _fallback_full_text(
    cfg: Config, dim: int, source: str, *, use_cache: bool,
    usage_sink: list[dict[str, Any]] | None = None,
) -> DimensionScore:
    """Re-score one dimension against the full statement text.

    Fires only when a dimension had zero extracted claims — it recovers content
    the single-dimension classifier filed elsewhere (e.g. a passing training
    mention inside a policy paragraph), converting a false 0 into a defensible,
    evidence-backed score. One call; a genuine omission still scores 0.
    """
    d = DIMENSIONS[dim]
    user = (
        f"Dimension {dim}: {d['name']} (UK MSA s.{d['s54']})\n{d['description']}\n\n"
        "No dimension-specific claims were extracted. Scan the FULL statement text below for any "
        "relevant content and score accordingly (0 if genuinely unaddressed).\n\n"
        "=== FULL STATEMENT TEXT ===\n" + source
    )
    try:
        raw = cached_structured(
            cfg, model=cfg.models["scoring"], system=FALLBACK_SYSTEM, user=user,
            response_model=RawDimensionScore, max_tokens=int(cfg.llm.get("scoring_max_tokens", 16000)),
            use_cache=use_cache, retries=int(cfg.llm.get("parse_retries", 1)), cache_salt="fallback",
            usage_sink=usage_sink,
        )
    except LLMError as exc:
        return DimensionScore(
            dimension=dim, score=0, fallback=True,
            justification=f"{_FALLBACK_NOTE}Full-text fallback failed ({exc}); scored 0.",
            evidence_quotes=[],
        )

    spans = verify_quotes(raw.evidence_quotes, source)
    # Cap at 2: the fallback reads full text WITHOUT extracted claims, so it may
    # only recover "mentioned" (1) or "general commitment" (2) — never a
    # mechanism-level score (3-4), which requires claim-grounded evidence.
    score = min(raw.score, 2)
    if not spans and score > 0:  # can't cite -> treat as genuine omission
        return DimensionScore(
            dimension=dim, score=0, fallback=True,
            justification=f"{_FALLBACK_NOTE}No verifiable evidence on re-scan; scored 0. ({raw.justification})",
            evidence_quotes=[],
        )
    cap_note = (
        " (capped at 2: full-text fallback cannot award mechanism-level scores)"
        if raw.score > 2 else ""
    )
    return DimensionScore(
        dimension=dim, score=score, fallback=True,
        justification=_FALLBACK_NOTE + raw.justification + cap_note, evidence_quotes=spans,
    )


def build_user_prompt(dim: int, verified: list[tuple[str, str, str]]) -> str:
    d = DIMENSIONS[dim]
    lines = [
        f"Dimension {dim}: {d['name']} (UK MSA s.{d['s54']})",
        d["description"],
        "",
        "Extracted claims for this dimension:",
    ]
    if not verified:
        lines.append("  (none)")
    for i, (span, ctype, page) in enumerate(verified, start=1):
        one_line = " ".join(span.split())
        lines.append(f'  [{i}] ({ctype}, {page}) "{one_line}"')
    lines += ["", "Score this dimension 0-4 using the rubric, and copy the most relevant "
              "claim texts verbatim into evidence_quotes."]
    return "\n".join(lines)


def _median(values: list[int]) -> int:
    """Lower-median: for scores like [2,3,2] -> 2. Deterministic and conservative."""
    s = sorted(values)
    return s[(len(s) - 1) // 2]


def score_dimension(
    cfg: Config, dim: int, claims: list[Claim], source: str, idx: NormIndex, *,
    use_cache: bool = True, usage_sink: list[dict[str, Any]] | None = None,
) -> DimensionScore:
    verified = _verified_claims(dim, claims, source, idx)
    if not verified:
        # No dimension-specific claims: re-score against the full text (catches
        # cross-cutting mentions the single-dimension classifier filed elsewhere).
        return _fallback_full_text(cfg, dim, source, use_cache=use_cache, usage_sink=usage_sink)

    model = cfg.models["scoring"]
    max_tokens = int(cfg.llm.get("scoring_max_tokens", 16000))
    retries = int(cfg.llm.get("parse_retries", 1))
    n_samples = max(1, int(cfg.llm.get("scoring_samples", 3)))
    user = build_user_prompt(dim, verified)

    def run(salt: str, extra: str = "") -> RawDimensionScore:
        return cached_structured(
            cfg, model=model, system=SCORING_SYSTEM, user=user + extra,
            response_model=RawDimensionScore, max_tokens=max_tokens,
            use_cache=use_cache, retries=retries, cache_salt=salt, usage_sink=usage_sink,
        )

    # Sample N times and take the median score (tames borderline-dimension flips).
    samples: list[RawDimensionScore] = []
    for k in range(n_samples):
        try:
            samples.append(run(salt=f"s{k}"))
        except LLMError:
            continue
    if not samples:
        return DimensionScore(
            dimension=dim, score=0,
            justification="Scoring failed for all samples; scored 0.", evidence_quotes=[],
        )

    median_score = _median([s.score for s in samples])
    consensus = [s for s in samples if s.score == median_score]
    # evidence pooled from the median-scoring samples, verified to source spans
    spans = verify_quotes([q for s in consensus for q in s.evidence_quotes], source)
    justification = consensus[0].justification

    if not spans and median_score > 0:  # lost all evidence — one verbatim-nudged re-run
        try:
            extra = run(
                salt="fix",
                extra="\n\nYour previous evidence_quotes could not be found in the source. "
                "Copy the claim texts above EXACTLY, character for character.",
            )
            spans2 = verify_quotes(extra.evidence_quotes, source)
            if spans2:
                spans, justification = spans2, extra.justification
        except LLMError:
            pass

    score = median_score
    if not spans and score > 0:  # uncited non-zero scores are worthless — force 0
        justification = f"No verifiable evidence could be cited; scored 0. (Model rationale: {justification})"
        score = 0
    return DimensionScore(dimension=dim, score=score, justification=justification, evidence_quotes=spans)


_CROSSCUT_NOTE = (
    "[Combined scoring: no dimension-specific claims were extracted; credited from "
    "cross-cutting claims filed under another dimension and capped at 2.] "
)


def build_combined_user_prompt(verified_by_dim: dict[int, list[tuple[str, str, str]]]) -> str:
    """User prompt for the combined call: every dimension's verified claims,
    presented as their SOURCE spans and grouped by dimension."""
    lines = [
        "Score ALL SIX dimensions of this modern slavery statement. Judge each dimension "
        "from the claims listed under it; a claim may also inform a different dimension "
        "(see guidance). Return one entry per dimension (1-6).",
        "",
    ]
    for d in DIMENSIONS:
        meta = DIMENSIONS[d]
        lines.append(f"=== Dimension {d}: {meta['name']} (UK MSA s.{meta['s54']}) ===")
        lines.append(meta["description"])
        verified = verified_by_dim[d]
        if not verified:
            lines.append("  Extracted claims: (none)")
        else:
            lines.append("  Extracted claims:")
            for i, (span, ctype, page) in enumerate(verified, start=1):
                one_line = " ".join(span.split())
                lines.append(f'    [{i}] ({ctype}, {page}) "{one_line}"')
        lines.append("")
    lines.append(
        "Score each dimension 0-4 using the rubric and copy the most relevant claim "
        "texts verbatim into that dimension's evidence_quotes."
    )
    return "\n".join(lines)


def _dim_entry(sample: RawCombinedScore, dim: int) -> RawCombinedDimensionScore | None:
    """The sample's entry for `dim` (first if the model duplicated it), or None."""
    for e in sample.scores:
        if e.dimension == dim:
            return e
    return None


def score_all_dimensions_combined(
    cfg: Config, claims: list[Claim], source: str, idx: NormIndex, *,
    use_cache: bool = True, usage_sink: list[dict[str, Any]] | None = None,
) -> list[DimensionScore]:
    """Score all six dimensions in ONE structured call per sample.

    Runs `scoring_samples` combined calls (thinking disabled) and takes the
    per-dimension median across them — identical median-of-3 semantics to the
    legacy scorer, but ~6x fewer Sonnet calls. Preserves the two safety nets:
    (1) evidence is verified to the source and an uncited non-zero score is
    forced to 0; (2) a dimension with no own claims that the combined call also
    fails to credit falls back to the full-text re-read. Cross-cutting credit
    (a claim filed under another dimension) is allowed but capped at 2 and
    marked `fallback=True` so it is visible in the snapshot diff.
    """
    model = cfg.models["scoring"]
    max_tokens = int(cfg.llm.get("scoring_max_tokens", 16000))
    retries = int(cfg.llm.get("parse_retries", 1))
    n_samples = max(1, int(cfg.llm.get("scoring_samples", 3)))

    verified_by_dim = {d: _verified_claims(d, claims, source, idx) for d in DIMENSIONS}
    user = build_combined_user_prompt(verified_by_dim)

    # Thinking is a per-CALL flag, and this call scores all six dimensions at once —
    # so thinking cannot be toggled per dimension, only per combined call. Disabled
    # is the default; "adaptive" is the recover-the-downgrades lever. Each mode uses
    # its own salt namespace so cached results never cross modes.
    think_mode = str(cfg.llm.get("combined_scoring_thinking", "disabled")).lower()
    thinking = {"type": "adaptive"} if think_mode == "adaptive" else {"type": "disabled"}
    salt_prefix = "ca" if think_mode == "adaptive" else "c"

    samples: list[RawCombinedScore] = []
    for k in range(n_samples):
        try:
            samples.append(cached_structured(
                cfg, model=model, system=COMBINED_SCORING_SYSTEM, user=user,
                response_model=RawCombinedScore, max_tokens=max_tokens,
                use_cache=use_cache, retries=retries, cache_salt=f"{salt_prefix}{k}",
                thinking=thinking, usage_sink=usage_sink,
            ))
        except LLMError:
            continue  # parse failure is recorded in usage_sink; median uses remaining samples

    results: list[DimensionScore] = []
    for d in DIMENSIONS:
        had_own_claims = bool(verified_by_dim[d])
        per = [e for e in (_dim_entry(s, d) for s in samples) if e is not None]

        if not per:
            # No usable combined output for this dimension across every sample.
            if had_own_claims:
                results.append(DimensionScore(
                    dimension=d, score=0,
                    justification="Combined scoring produced no entry for this dimension; scored 0.",
                    evidence_quotes=[]))
            else:
                results.append(_fallback_full_text(cfg, d, source, use_cache=use_cache, usage_sink=usage_sink))
            continue

        median_score = _median([p.score for p in per])
        consensus = [p for p in per if p.score == median_score]
        # evidence pooled from the median-scoring samples, verified to source spans
        spans = verify_quotes([q for p in consensus for q in p.evidence_quotes], source)
        justification = consensus[0].justification

        fallback = not had_own_claims
        # Cross-cutting cap = the rubric's own 2->3 boundary. The rubric ties 3-4 to
        # "concrete mechanisms" (3) and "mechanisms + measurable evidence" (4) FOR this
        # dimension; a 2 is "general commitments, no mechanisms". A claim filed under a
        # different dimension can establish that this topic is present/committed (<=2) but
        # cannot, on its own, substantiate a mechanism *here* — so 2 is the ceiling. This
        # is the same principle as the legacy zero-claim full-text fallback cap. It is
        # deliberately conservative: a genuinely-misfiled mechanism claim is held to 2
        # because "about this dimension" can't be told from "mentions it in passing"
        # without the claim being filed here.
        score = min(median_score, 2) if fallback else median_score
        if not spans and score > 0:  # uncited non-zero scores are worthless — force 0
            justification = (
                f"No verifiable evidence could be cited; scored 0. (Model rationale: {justification})"
            )
            score = 0
        if fallback and score == 0:
            # Genuine-omission candidate: full-text safety net, exactly as the legacy
            # zero-claim path. Recovers a real "mentioned"/"general commitment" or confirms 0.
            results.append(_fallback_full_text(cfg, d, source, use_cache=use_cache, usage_sink=usage_sink))
            continue
        if fallback:
            justification = _CROSSCUT_NOTE + justification
        results.append(DimensionScore(
            dimension=d, score=score, justification=justification,
            evidence_quotes=spans, fallback=fallback))
    return results


def score_for_row(
    cfg: Config, row, *, use_cache: bool = True, combined: bool | None = None,
    usage_sink: list[dict[str, Any]] | None = None,
) -> list[DimensionScore] | None:
    """Score one statement's six dimensions.

    `combined` selects the scorer: True = combined single-call scorer, False =
    legacy per-dimension scorer, None = the `llm.combined_scoring` config flag.
    """
    path = text_path(cfg, row)
    if not path.exists():
        return None
    extraction = extract_for_row(cfg, row, use_cache=use_cache)
    if extraction is None:
        return None
    source = path.read_text(encoding="utf-8")
    idx = build_norm_index(source)
    claims = extraction.claims
    if combined is None:
        combined = bool(cfg.llm.get("combined_scoring", True))

    if combined:
        scores = score_all_dimensions_combined(
            cfg, claims, source, idx, use_cache=use_cache, usage_sink=usage_sink)
    else:
        scores = [
            score_dimension(cfg, d, claims, source, idx, use_cache=use_cache, usage_sink=usage_sink)
            for d in DIMENSIONS
        ]
    for s in scores:
        tag = " (fallback)" if s.fallback else ""
        print(f"        dim {s.dimension} {DIMENSIONS[s.dimension]['name']}: {s.score}{tag}", flush=True)
    return scores


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="python -m src.pipeline.score",
        description="Score statement dimensions against the s.54(5) rubric (LLM pass 2).",
    )
    ap.add_argument("--company", metavar="SLUG", help="Only this company.")
    ap.add_argument("--force", action="store_true", help="Bypass the response cache.")
    ap.add_argument("--scorer", choices=("combined", "legacy"), default=None,
                    help="Scorer to use (default: llm.combined_scoring in config.yaml).")
    args = ap.parse_args()

    cfg = load_config()
    require_api_key()
    rows = load_sources(cfg)
    if args.company:
        rows = [r for r in rows if r.company_slug == args.company]

    combined = None if args.scorer is None else (args.scorer == "combined")
    for row in rows:
        if not text_path(cfg, row).exists():
            print(f"{row.company_slug}_{row.year}: no extracted text — skipped")
            continue
        print(f"\n{row.company_slug}_{row.year} ({cfg.models['scoring']}):")
        scores = score_for_row(row=row, cfg=cfg, use_cache=not args.force, combined=combined) or []
        for s in scores:
            name = DIMENSIONS[s.dimension]["name"]
            print(f"  {s.dimension}. {name:<28} score={s.score}  evidence={len(s.evidence_quotes)}")
            if s.evidence_quotes:
                print(f"       e.g. {' '.join(s.evidence_quotes[0].split())[:150]!r}")
            else:
                print(f"       {s.justification[:150]}")
        if scores:
            provisional = mean(s.score for s in scores)
            print(f"  --> provisional overall (mean of 6, pre-boilerplate): {provisional:.2f}")


if __name__ == "__main__":
    main()
