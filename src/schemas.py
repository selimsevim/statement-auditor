"""Pydantic models for every structured output in the pipeline.

These are the single source of truth for the JSON that flows between the two
LLM passes, the computed boilerplate step, and SQLite storage. Pass 1 (claims)
and Pass 2 (scoring) drive `client.messages.parse()` directly against these
models, so the model is forced to return schema-valid JSON.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    """How substantive a claim is — set by the extraction pass."""

    mechanism = "mechanism"                # a concrete action actually taken
    commitment = "commitment"              # a promise or intention
    metric = "metric"                      # a number, target, or measured outcome
    policy_reference = "policy_reference"  # a named/dated policy document
    generic = "generic"                    # boilerplate or vague acknowledgement


class Claim(BaseModel):
    """One extracted claim tied to a taxonomy dimension (1-6).

    `quote` MUST be copied verbatim from the source text; it is string-matched
    against the extracted text downstream, and any claim whose quote cannot be
    located is discarded.
    """

    dimension: int = Field(ge=1, le=6, description="Taxonomy dimension, 1-6.")
    quote: str = Field(description="Verbatim quote from the statement text.")
    page_or_position: str = Field(
        description="Page number or character offset where the quote appears."
    )
    claim_type: ClaimType


class ClaimsExtraction(BaseModel):
    """Full output of Pass 1 for a single statement."""

    claims: list[Claim] = Field(default_factory=list)


class DimensionScore(BaseModel):
    """Output of Pass 2 for a single dimension (1-6).

    `evidence_quotes` holds only quotes verified to exist verbatim in the
    source text — the post-hoc verifier drops the rest. An empty list with a
    score of 0 is rendered in the dashboard as "no evidence found, scored 0".
    """

    dimension: int = Field(ge=1, le=6)
    score: int = Field(ge=0, le=4)
    justification: str
    evidence_quotes: list[str] = Field(default_factory=list)
    fallback: bool = Field(
        default=False,
        description="True if scored via the zero-claim full-text fallback (capped at 2) "
        "rather than from extracted claims.",
    )


class BoilerplateResult(BaseModel):
    """Computed dimension 7 — no LLM involved.

    `boilerplate_share` is the fraction of this year's paragraphs whose maximum
    cosine similarity to any prior-year paragraph exceeds the configured
    threshold. It is None when the company has no prior-year statement.
    """

    prior_year: int | None = None
    n_paragraphs: int | None = None
    n_unchanged_paragraphs: int | None = None
    boilerplate_share: float | None = None
    similarity_method: str | None = Field(
        default=None,
        description="Paragraph similarity method used for YoY pairs: embedding or lexical.",
    )
    similarity_threshold: float | None = Field(
        default=None,
        description="Threshold used to mark paragraph pairs as unchanged.",
    )
    hedge_density: float = Field(
        description="Hedge-lexicon occurrences per 1000 words across the document."
    )


class ParagraphPair(BaseModel):
    """One current-year paragraph aligned to its most-similar prior-year paragraph.

    Persisted for the year-over-year diff view — the concrete "N of M paragraphs
    carried over" evidence, and the data the side-by-side view renders.
    """

    cur_index: int
    cur_text: str
    prior_index: int
    prior_text: str
    similarity: float
    unchanged: bool  # similarity >= the configured boilerplate threshold


class StatementScore(BaseModel):
    """Aggregate, persisted result for one company-year.

    `overall_score` is the mean of dimensions 1-6, penalized by boilerplate:
    when `boilerplate_share` exceeds the cap threshold the overall is capped and
    "substantially unchanged from prior year" is added to `flags`.
    """

    company_slug: str
    company_name: str
    sector: str
    year: int = Field(ge=2000, le=2100, description="Fiscal-year END; see SourceRow.year.")
    dimension_scores: list[DimensionScore]
    boilerplate: BoilerplateResult
    overall_score: float
    boilerplate_flag: bool = False
    flags: list[str] = Field(default_factory=list)


class SourceRow(BaseModel):
    """One row of sources.csv."""

    company_slug: str
    company_name: str
    sector: str
    year: int = Field(
        ge=2000,
        le=2100,
        description=(
            "Reporting year defined as the fiscal-year END — the calendar year in "
            "which the reporting period closes (Tesco FY2023/24 -> 2024). This "
            "convention makes consecutive-year diff pairing (year vs year-1) "
            "well-defined."
        ),
    )
    pdf_url: str
