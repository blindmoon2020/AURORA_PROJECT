"""Venue-aware execution routing: say honestly HOW an order would reach each market.

The platform must trade all markets, but "trade" means something different on each one. A US
equity can go through a broker API; a Tehran bourse order cannot, because Mofid publishes no
API, so the real route is a manual ticket plus reconciliation. A crypto order needs exchange
keys that the owner must supply. Writing one generic "execute()" would hide all of that and
produce the worst possible failure: a system that believes it sent an order.

So routing is explicit, per venue, and each route names what it needs and what blocks it.
Three rules:

  1. NO SILENT FALLBACK. If a venue has no working route, the plan says BLOCKED with the
     reason. It never quietly degrades to "paper" and reports success.
  2. A ROUTE IS NOT A PERMISSION. Reconciliation decides whether new risk may be opened at
     all; routing only says which pipe the order would use once permission exists.
  3. CAPABILITIES ARE DECLARED, NOT ASSUMED. An API route exists only when the caller says
     the credential is present; the router never probes, guesses or fabricates one.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from aurora.core import asset_universe as au

PAPER = "paper"                 # internal simulator, the only route that always works
MANUAL = "manual_ticket"        # human places the order, AURORA tracks and reconciles
API = "broker_api"              # direct electronic submission
BLOCKED = "blocked"

# venues where a manual ticket is the practical, documented route today
MANUAL_VENUES = {"XTSE_IR", "IFB_IR", "IME_IR"}


@dataclass(frozen=True)
class RoutePlan:
    symbol: str
    venue: str
    kind: str
    reason: str
    needs: List[str]
    blocked: bool = False

    def line(self) -> str:
        tag = "مسدود" if self.blocked else ("دستی" if self.kind == MANUAL else
                                            ("API" if self.kind == API else "شبیه‌ساز"))
        extra = f" · نیاز: {', '.join(self.needs)}" if self.needs else ""
        return f"{self.symbol} ({self.venue}): {tag} — {self.reason}{extra}"


@dataclass
class RouteBook:
    plans: List[RoutePlan]

    @property
    def blocked(self) -> List[RoutePlan]:
        return [p for p in self.plans if p.blocked]

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for p in self.plans:
            key = "blocked" if p.blocked else p.kind
            out[key] = out.get(key, 0) + 1
        return out

    def summary(self) -> str:
        c = self.counts()
        parts = [f"{k}: {v}" for k, v in sorted(c.items())]
        return "مسیرهای اجرا — " + "، ".join(parts)


def route_symbol(symbol: str, has_broker_api: bool = False,
                 has_exchange_keys: bool = False) -> RoutePlan:
    """Decide the pipe for one symbol. Never pretends a blocked venue is tradable."""
    inst = au.get(symbol)
    venue = inst.venue

    if venue in MANUAL_VENUES:
        return RoutePlan(symbol, venue, MANUAL,
                         "بورس ایران API معاملاتی ندارد؛ سفارش با تیکت دستی و تطبیق بعدی",
                         ["تأیید کارگزار", "ثبت پر شدن"], blocked=False)

    if venue == "XCRYPTO":
        if has_exchange_keys:
            return RoutePlan(symbol, venue, API,
                             "کلید صرافی موجود است؛ ارسال الکترونیکی مجاز",
                             ["کلید صرافی"], blocked=False)
        return RoutePlan(symbol, venue, BLOCKED,
                         "بدون کلید صرافی ارسال سفارش ممکن نیست",
                         ["کلید API صرافی"], blocked=True)

    if venue in ("XFX",):
        return RoutePlan(symbol, venue, BLOCKED,
                         "بازار خارج از بورس؛ کارگزار قابل استفاده برای مقیم ایران تضمین‌شدنی نیست",
                         ["کارگزار با دسترسی قانونی"], blocked=True)

    if has_broker_api:
        return RoutePlan(symbol, venue, API, "کارگزار API دارد", ["دسترسی کارگزار"],
                         blocked=False)

    return RoutePlan(symbol, venue, PAPER,
                     "بدون دسترسی کارگزار، مسیر شبیه‌ساز با قیمت واقعی", [], blocked=False)


def route_book(targets: Dict[str, float], has_broker_api: bool = False,
               has_exchange_keys: bool = False) -> RouteBook:
    return RouteBook([route_symbol(s, has_broker_api, has_exchange_keys)
                      for s in sorted(targets)])


def unroutable(plans: Sequence[RoutePlan]) -> List[str]:
    return [p.symbol for p in plans if p.blocked]


def route_report(book: RouteBook) -> str:
    lines = ["# مسیر اجرای سفارش‌ها", "", book.summary(), ""]
    for plan in book.plans:
        lines.append("- " + plan.line())
    if book.blocked:
        lines += ["", "## بازارهایی که امروز مسیر ندارند"]
        for plan in book.blocked:
            lines.append(f"- {plan.symbol}: {plan.reason}")
        lines += ["", "این بازارها تا فراهم شدن مسیر، در سبد اجرا نمی‌شوند. "
                      "شبیه‌ساز به‌جای آن‌ها گزارش نمی‌سازد."]
    return "\n".join(lines) + "\n"
