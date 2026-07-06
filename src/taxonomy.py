"""The accountability taxonomy and scoring rubric.

Dimensions 1-6 map directly to the six recommended content areas in section
54(5) of the UK Modern Slavery Act 2015. Dimension 7 (boilerplate) is computed,
not LLM-scored, so it is not listed here.

Section 54(5): https://www.legislation.gov.uk/ukpga/2015/30/section/54
"""
from __future__ import annotations

SECTION_54_URL = "https://www.legislation.gov.uk/ukpga/2015/30/section/54"

# dimension number -> metadata used to build both LLM prompts and the dashboard.
DIMENSIONS: dict[int, dict[str, str]] = {
    1: {
        "key": "structure_and_supply_chains",
        "name": "Structure and supply chains",
        "s54": "54(5)(a)",
        "description": (
            "Does the statement describe the organisation's structure, business, "
            "and supply chains with specificity — named tiers, geographies, and "
            "product/service categories — rather than generic descriptions?"
        ),
    },
    2: {
        "key": "policies",
        "name": "Policies",
        "s54": "54(5)(b)",
        "description": (
            "Are policies named, dated, and tied to modern slavery specifically, "
            "or is there only generic CSR / code-of-conduct language?"
        ),
    },
    3: {
        "key": "due_diligence",
        "name": "Due diligence processes",
        "s54": "54(5)(c)",
        "description": (
            "Are there concrete due-diligence mechanisms — supplier audits, "
            "contract clauses, on-site inspections, worker-voice channels — versus "
            "expectation language such as 'we expect suppliers to comply'?"
        ),
    },
    4: {
        "key": "risk_assessment",
        "name": "Risk assessment",
        "s54": "54(5)(d)",
        "description": (
            "Does the statement name specific high-risk geographies, sectors, or "
            "supply-chain stages, versus a generic acknowledgement that risk exists?"
        ),
    },
    5: {
        "key": "effectiveness_and_kpis",
        "name": "Effectiveness and KPIs",
        "s54": "54(5)(e)",
        "description": (
            "Are there measurable indicators with numbers or targets, versus "
            "aspirational statements with no way to measure progress?"
        ),
    },
    6: {
        "key": "training",
        "name": "Training",
        "s54": "54(5)(f)",
        "description": (
            "Does it say who is trained, how often, and whether completion is "
            "tracked — versus a bare mention that training exists?"
        ),
    },
}

# The 0-4 rubric applied to every LLM-scored dimension (1-6).
RUBRIC: dict[int, str] = {
    0: "Not addressed.",
    1: "Mentioned, no substance.",
    2: "General commitments, no mechanisms.",
    3: "Concrete mechanisms described, weak or no measurement.",
    4: "Concrete mechanisms plus measurable evidence or outcomes.",
}

# Guidance for the extraction pass on how to classify each claim.
CLAIM_TYPE_GUIDANCE: dict[str, str] = {
    "mechanism": "A concrete mechanism or action actually taken (e.g. 'we audited 120 tier-1 suppliers').",
    "commitment": "A promise or intention without evidence it has happened (e.g. 'we are committed to eliminating forced labour').",
    "metric": "A number, target, or measured outcome (e.g. '94% of staff completed training').",
    "policy_reference": "A reference to a named or dated policy document (e.g. 'our Supplier Code of Conduct (2022)').",
    "generic": "Boilerplate or a vague acknowledgement with no specificity.",
}

# The computed dimension, documented here for completeness (not LLM-scored).
COMPUTED_DIMENSION = {
    7: {
        "key": "boilerplate",
        "name": "Boilerplate score",
        "description": (
            "Similarity of this year's statement to the prior year (share of "
            "paragraphs above the similarity threshold), plus hedge-word density "
            "per 1000 words. Computed, not LLM-scored."
        ),
    }
}

LLM_SCORED_DIMENSIONS = tuple(DIMENSIONS.keys())  # (1, 2, 3, 4, 5, 6)
