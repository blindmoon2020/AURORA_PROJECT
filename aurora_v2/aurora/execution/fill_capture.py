"""First real fills: capture them once, measure them honestly, calibrate from evidence.

The 17 November open is the first time AURORA will see a real fill. Three things must
be true or the measurement is worthless:

  1. ONE fill counts ONCE. A capture run that is re-run (a restart, a retry, a manual
     invocation an hour later) must not add the same fill to the sample again, because
     duplicated good fills shrink the standard error and manufacture false confidence.
  2. A fill that arrived outside its ticket's window is not evidence about execution
     quality, it is a stale price. It is rejected, not averaged in.
  3. A fill with no matching ticket is recorded as unmatched, never silently dropped:
     a fill the book does not know about is the most dangerous kind.

Slippage sign follows the trade: paying above the decision price on a buy is a loss,
and receiving less than it on a sell is a loss. Getting that sign wrong would flip the
calibration from "costs are higher than assumed" to "we are being paid to trade".
"""
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set

from aurora.calibration import slippage_bps
from aurora.execution.manual import FillRecord, OrderTicket, Side


@dataclass(frozen=True)
class MatchedFill:
    ticket_id: str
    symbol: str
    bps: float
    ts: int
    price: float
    units: float

    def line(self) -> str:
        return (f"{self.ticket_id} {self.symbol:10s} {self.units:>10,.2f} @ {self.price:.4f} "
                f"→ {self.bps:+.1f} bps")


@dataclass
class CaptureReport:
    matched: List[MatchedFill] = field(default_factory=list)
    duplicates: List[str] = field(default_factory=list)
    late: List[str] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)
    unknown_ticket: List[str] = field(default_factory=list)

    @property
    def observations(self) -> List[float]:
        return [m.bps for m in self.matched]

    @property
    def mean_bps(self) -> Optional[float]:
        return (sum(self.observations) / len(self.observations)) if self.matched else None

    def summary(self) -> str:
        return (f"matched {len(self.matched)} · duplicate {len(self.duplicates)} · "
                f"late {len(self.late)} · unmatched {len(self.unmatched)} · "
                f"unknown ticket {len(self.unknown_ticket)}")


def _decision_price(ticket: OrderTicket) -> Optional[float]:
    return ticket.limit_price


def capture(tickets: Sequence[OrderTicket], fills: Iterable[FillRecord],
            already_captured: Optional[Set[str]] = None,
            market_open_ts: Optional[Sequence[int]] = None) -> CaptureReport:
    """Turn raw fills into calibration observations, refusing anything ambiguous.

    `already_captured` carries the ticket ids consumed by earlier runs so a retry cannot
    double-count. `market_open_ts` (optional) restricts acceptable fill timestamps to
    the sessions that actually opened, which is what stops a weekend timestamp from
    entering the sample.
    """
    by_id: Dict[str, OrderTicket] = {t.ticket_id: t for t in tickets}
    captured = set(already_captured or ())
    report = CaptureReport()

    for fill in fills:
        ticket = by_id.get(fill.ticket_id)
        if ticket is None:
            report.unknown_ticket.append(fill.ticket_id)
            continue
        if fill.ticket_id in captured:
            report.duplicates.append(fill.ticket_id)
            continue
        decision = _decision_price(ticket)
        if decision is None or decision <= 0:
            report.unmatched.append(fill.ticket_id)     # no reference price, no measurement
            continue
        if fill.ts < ticket.created_ts:
            report.late.append(fill.ticket_id)          # fill predates its own ticket
            continue
        if fill.ts > ticket.expires_ts:
            report.late.append(fill.ticket_id)          # stale: window closed
            continue
        if market_open_ts is not None and fill.ts not in set(market_open_ts):
            report.late.append(fill.ticket_id)
            continue
        bps = slippage_bps(decision, fill.price, is_buy=(ticket.side == Side.LONG))
        report.matched.append(MatchedFill(fill.ticket_id, fill.symbol, bps, fill.ts,
                                          fill.price, fill.units))
        captured.add(fill.ticket_id)

    return report


def calibrate_from_capture(report: CaptureReport, prior_observations: Sequence[float],
                           assumption_bps: float = 10.0):
    """Blend this capture into the sample and return the calibration verdict.

    Prior observations are kept so an early run does not throw away history; the
    calibration rule itself stays the one pre-registered in aurora/calibration.py.
    """
    from aurora.calibration import calibrate
    return calibrate(list(prior_observations) + report.observations, assumption_bps)


def ready_for_first_fill(report: CaptureReport) -> tuple:
    """Is this capture clean enough to be the sample the cost model learns from?"""
    problems = []
    if report.unknown_ticket:
        problems.append(f"{len(report.unknown_ticket)} fills have no ticket: "
                        "reconcile the book before calibrating")
    if report.unmatched:
        problems.append(f"{len(report.unmatched)} fills lack a reference price")
    if report.duplicates:
        problems.append(f"{len(report.duplicates)} fills were already captured")
    return (not problems, problems)
