"""Decision log: one line per decision, taken or rejected, forever.

This is the AURORA idea worth keeping. If a trade cannot point at the record
that justified it, it was not a decision, it was an accident.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class DecisionRecord:
    ts: int
    symbol: str
    strategy: str
    side: str
    entry: float
    stop: float
    target: float
    units: float
    risk_money: float
    equity: float
    approved: bool
    reason: str
    stage: str = "risk"
    decision_id: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)


class DecisionLog:
    """Append-only JSONL. Also keeps records in memory for inspection."""

    def __init__(self, path: Optional[str | Path] = None) -> None:
        self.path = Path(path) if path else None
        self.records: List[DecisionRecord] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("", encoding="utf-8")

    def record(self, rec: DecisionRecord) -> DecisionRecord:
        if not rec.reason or not rec.reason.strip():
            raise ValueError("every decision needs a reason")
        if not rec.decision_id:
            rec = replace(rec, decision_id=f"D{len(self.records) + 1:06d}")
        self.records.append(rec)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(rec.to_json() + "\n")
        return rec

    def approved(self) -> List[DecisionRecord]:
        return [r for r in self.records if r.approved]

    def rejected(self) -> List[DecisionRecord]:
        return [r for r in self.records if not r.approved]

    def __len__(self) -> int:
        return len(self.records)


def read_log(path: str | Path) -> List[DecisionRecord]:
    p = Path(path)
    out: List[DecisionRecord] = []
    with p.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(DecisionRecord(**json.loads(line)))
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValueError(f"{p}: bad record at line {lineno}: {exc}") from exc
    return out
