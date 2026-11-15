"""The app layer: one JSON-ready surface used by the website, the mobile app and the tests.

Design rules that matter more than the code:
* no web framework is imported at module load, so the core stays zero-dependency and the
  test suite runs on a machine without FastAPI (the owner's own machine has no Python at all,
  which is exactly why the layer must degrade instead of exploding);
* every function returns plain dicts, so a Flask/FastAPI/Next.js front end can reuse them;
* nothing here invents prices: a missing price is reported as missing, never filled with zero.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from aurora.advice import holdings as hd
from aurora.advice import onboarding as ob
from aurora.core import asset_universe as au
from aurora.core import market_clock


def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "instruments": len(au.INSTRUMENTS),
        "classes": sorted({i.asset_class for i in au.INSTRUMENTS}),
        "venues": len(au.VENUES),
        "coverage": au.coverage_line(),
    }


def questionnaire() -> Dict[str, Any]:
    """The form the client fills in: ids, labels, options and what each answer is worth."""
    items = []
    for q in ob.QUESTIONS:
        items.append({
            "id": q["id"],
            "text": q["text"],
            "kind": q["kind"],
            "options": [{"label": label, "value": value}
                        for label, value in (o[0], o[1]) for o in [o]] if False else [
                {"label": o[0], "value": o[1]} for o in q["options"]],
        })
    return {"questions": items, "count": len(items)}


def onboard(payload: Dict[str, Any]) -> Dict[str, Any]:
    """answers + capital -> risk profile, allocation, instrument-level holdings, warnings."""
    answers = {str(k): int(v) for k, v in (payload.get("answers") or {}).items()}
    capital = float(payload.get("capital") or 0.0)
    if capital <= 0:
        raise ValueError("سرمایه باید بزرگ‌تر از صفر باشد")

    profile = ob.score_answers(answers)
    capacity = payload.get("capacity") or {}
    flags = ob.contradictions(answers, capacity, profile)
    allocation = ob.design_portfolio(profile)
    prices = payload.get("prices") or {}
    plan = hd.expand(allocation, capital, prices=prices)
    gate = ob.subscription_gate(payload.get("paid_until"), payload.get("today"))

    return {
        "profile": {"score": profile.score, "band": profile.band,
                    "risk_asset_cap": profile.risk_asset_cap,
                    "max_drawdown_pct": profile.max_drawdown_pct,
                    "reasons": profile.reasons},
        "contradictions": flags,
        "allocation": allocation,
        "holdings": [{"symbol": h.symbol, "name": h.name, "class": h.asset_class,
                      "venue": h.venue, "country": h.country, "currency": h.currency,
                      "weight": h.weight, "notional": h.notional,
                      "price": getattr(h, "price", None),
                      "units": getattr(h, "units", None)}
                     for h in plan.holdings],
        "other_components": [{"name": n, "weight": w, "notional": m, "share_of_other": sh}
                             for n, w, m, sh in plan.other_components],
        "gaps": plan.gaps,
        "subscription": {"allowed": gate.allowed, "reason": gate.reason},
        "disclaimer": "این خروجی پیشنهاد است نه تضمین بازده.",
    }


def rebalance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """current weights vs target weights -> the explicit trades, with amounts."""
    capital = float(payload.get("capital") or 0.0)
    current = {k: float(v) for k, v in (payload.get("current") or {}).items()}
    answers = {str(k): int(v) for k, v in (payload.get("answers") or {}).items()}
    profile = ob.score_answers(answers)
    target = ob.design_portfolio(profile)
    trades = ob.rebalance(current, target, capital,
                          band=float(payload.get("band", 0.02)),
                          cost_bps=float(payload.get("cost_bps", 10.0)))
    return {"target": target,
            "trades": [{"bucket": t.asset_class, "side": t.side, "weight": t.delta_pct,
                        "amount": t.amount, "note": t.reason} for t in trades]}


def venue_status(symbol: str, when_iso: Optional[str] = None) -> Dict[str, Any]:
    """Is this instrument's home exchange open right now? Never guess an unknown venue."""
    from datetime import datetime, timezone
    when = datetime.fromisoformat(when_iso) if when_iso else datetime.now(timezone.utc)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    result = market_clock.gate(symbol, when)
    return {"symbol": symbol, "open": result[0], "reason": result[1]}


def create_app() -> Any:
    """Optional FastAPI wrapper. Absent FastAPI is a clear error, not a silent fallback."""
    try:
        from fastapi import FastAPI
    except Exception as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(
            "FastAPI نصب نیست؛ لایه JSON همین‌جا کار می‌کند، برای سرور وب "
            "`pip install fastapi uvicorn` را اجرا کن") from exc

    app = FastAPI(title="AURORA API", version="4.30")

    @app.get("/health")
    def _health() -> Dict[str, Any]:
        return health()

    @app.get("/questionnaire")
    def _questionnaire() -> Dict[str, Any]:
        return questionnaire()

    @app.post("/onboard")
    def _onboard(payload: Dict[str, Any]) -> Dict[str, Any]:
        return onboard(payload)

    @app.post("/rebalance")
    def _rebalance(payload: Dict[str, Any]) -> Dict[str, Any]:
        return rebalance(payload)

    return app
