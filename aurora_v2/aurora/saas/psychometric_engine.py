"""Psychometric profiling for the SaaS layer.

The original version of this file was truncated mid-string and could not even be imported,
and nothing in the test suite noticed. Rather than maintain a second, divergent questionnaire,
this module is a thin adapter over the single source of truth in
`aurora.advice.onboarding` - a two-part questionnaire (capacity and tolerance), scored
with the binding-constraint rule (the lower of the two, penalised for disagreement).

A questionnaire can be answered consistently overall and still be internally inconsistent
(for example: claims a 40% loss tolerance while holding two months of cash). Those cases are
returned as explicit flags so the caller can show them to the client instead of silently
averaging them away.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from aurora.advice.onboarding import (QUESTIONS, Profile, contradictions, fa_digits,
                                      score_answers)

# a stable, importable view of the questionnaire for API clients and the web form
PSYCHOMETRIC_QUESTIONS = tuple(
    {
        "id": q["id"],
        "kind": q["kind"],
        "text": q["text"],
        "options": [{"index": i, "label": label, "value": value}
                    for i, (label, value) in enumerate(q["options"])],
    }
    for q in QUESTIONS
)


def assess(answers: Dict[str, int],
           capacity: Optional[Dict[str, object]] = None) -> Dict[str, object]:
    """Score a completed questionnaire.

    `answers` maps question id to the chosen option index. `capacity` carries the client's
    stated situation (capital, horizon_years, emergency_fund_months, loss_tolerance_pct) and is
    only used to detect contradictions; the score itself comes from the answers.
    """
    profile: Profile = score_answers(answers)
    flags: List[str] = contradictions(answers, capacity or {}, profile=profile)
    return {
        "score": profile.score,
        "band": profile.band,
        "capacity_score": profile.capacity_score,
        "tolerance_score": profile.tolerance_score,
        "risk_asset_cap": profile.risk_asset_cap,
        "max_drawdown_pct": profile.max_drawdown_pct,
        "contradictions": flags,
        "reasons": list(profile.reasons),
        "summary": fa_digits(profile.line()),
    }


def questionnaire_for_api() -> List[dict]:
    """The questionnaire as JSON-ready data, for the web/app form."""
    return [dict(q) for q in PSYCHOMETRIC_QUESTIONS]
