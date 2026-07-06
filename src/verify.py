"""Evidence verification: confirm a quote occurs in the source, and return the
exact SOURCE-TEXT span for display.

Matching is tolerant of cosmetic PDF-vs-model differences (case, punctuation,
bullets, hyphenation, whitespace) but requires the exact contiguous word
sequence — a paraphrase does not match. Crucially, the returned span is sliced
from the original source text via a normalized->original offset map, so the
dashboard shows what the document actually says (not the model's reconstruction)
and a reviewer can locate it in the source.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_NON_ALNUM = re.compile(r"[^0-9a-z]+")


def normalize_for_match(s: str) -> str:
    """Lowercase, alphanumeric tokens joined by single spaces."""
    return _NON_ALNUM.sub(" ", s.lower()).strip()


def quote_in_text(quote: str, normalized_source: str) -> bool:
    """True if `quote` occurs in an already-normalized source string."""
    q = normalize_for_match(quote)
    return bool(q) and q in normalized_source


@dataclass
class NormIndex:
    """A normalized source string plus, per normalized char, the original span."""

    norm: str
    starts: list[int]  # original start offset of each normalized char
    ends: list[int]    # original end offset (exclusive) of each normalized char


def build_norm_index(source: str) -> NormIndex:
    """Normalize `source` char-by-char, keeping a map back to original offsets.

    Produces the same string as `normalize_for_match(source)` while recording,
    for every normalized character, which original character(s) it came from.
    """
    chars: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    prev_space = True  # collapse separator runs; drop leading separators
    for i, ch in enumerate(source):
        lc = ch.lower()
        if lc.isascii() and (lc.isdigit() or ("a" <= lc <= "z")):
            chars.append(lc)
            starts.append(i)
            ends.append(i + 1)
            prev_space = False
        elif not prev_space:
            chars.append(" ")
            starts.append(i)
            ends.append(i + 1)
            prev_space = True
    while chars and chars[-1] == " ":  # strip trailing separator
        chars.pop()
        starts.pop()
        ends.pop()
    return NormIndex("".join(chars), starts, ends)


def find_source_span(quote: str, idx: NormIndex, source: str) -> str | None:
    """Return the exact `source` substring matching `quote`, or None."""
    q = normalize_for_match(quote)
    if not q:
        return None
    pos = idx.norm.find(q)
    if pos < 0:
        return None
    start = idx.starts[pos]
    end = idx.ends[pos + len(q) - 1]
    return source[start:end].strip()


def verify_quotes(quotes: list[str], source: str) -> list[str]:
    """Return deduped source spans for the quotes that verify against `source`."""
    idx = build_norm_index(source)
    seen: set[str] = set()
    spans: list[str] = []
    for q in quotes:
        span = find_source_span(q, idx, source)
        if span is None:
            continue
        key = normalize_for_match(span)
        if key not in seen:
            seen.add(key)
            spans.append(span)
    return spans
