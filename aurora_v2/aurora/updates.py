"""Self-updating data: detect that a source changed before it corrupts a decision.

A provider that silently renames a column, changes a unit, or starts returning a
different row count does not raise an error. It returns plausible numbers and the
strategy quietly trades on a different world. The defence is a digest: remember the
shape of each dataset (columns, row count band, hash of the last rows), and compare
on every refresh.

Diffs are classified, because "the price moved" and "the schema moved" need
different responses: prices change every day and must not alarm; a schema change
must stop use of that dataset until a human looks.
"""
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

SCHEMA, VOLUME, CONTENT = "schema", "volume", "content"


@dataclass
class Digest:
    source: str
    columns: List[str]
    rows: int
    tail_hash: str
    updated_ts: int = 0


@dataclass
class Change:
    source: str
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.source}: {self.kind} - {self.detail}"


def digest(source: str, columns: Sequence[str], rows: Sequence[Sequence], tail: int = 20,
           updated_ts: int = 0) -> Digest:
    rows = list(rows)
    tail_rows = rows[-tail:]
    payload = "\n".join(",".join(str(c) for c in r) for r in tail_rows).encode("utf-8")
    return Digest(source=source, columns=list(columns), rows=len(rows),
                  tail_hash=hashlib.sha256(payload).hexdigest()[:16], updated_ts=updated_ts)


def compare(previous: Optional[Digest], current: Digest, volume_tolerance: float = 0.25) -> List[Change]:
    """Empty list means usable. SCHEMA changes block the dataset; others inform."""
    if previous is None:
        return []
    out: List[Change] = []
    if previous.columns != current.columns:
        added = [c for c in current.columns if c not in previous.columns]
        removed = [c for c in previous.columns if c not in current.columns]
        out.append(Change(current.source, SCHEMA,
                          f"columns changed (added {added or '-'}, removed {removed or '-'})"))
    if previous.rows and abs(current.rows - previous.rows) > previous.rows * volume_tolerance:
        out.append(Change(current.source, VOLUME,
                          f"row count {previous.rows} -> {current.rows}"))
    elif previous.tail_hash and previous.tail_hash == current.tail_hash:
        out.append(Change(current.source, CONTENT, "identical tail: source may be frozen"))
    return out


def blocked(changes: Iterable[Change]) -> List[str]:
    """Datasets that must not be used until a human reviews them."""
    return sorted({c.source for c in changes if c.kind == SCHEMA})
