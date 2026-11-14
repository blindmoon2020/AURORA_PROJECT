"""Customer data protection: what may never leave, and what may never be logged.

Scope is deliberately honest. This module gives three controls that stdlib can
actually deliver, rather than a fourth that only sounds like one:

1. Redaction - email, phone, national code, card number and long account numbers
   are masked before any text reaches a log, a report, an error message or a commit.
   A card number is only masked when it passes the Luhn check, so a price series and
   a random 16-digit id do not become casualties of the filter.
2. Pseudonymisation - personal identifiers are stored as HMAC-SHA256 tokens under a
   key that lives outside the data. The mapping cannot be reversed from the data
   alone, and the same input always yields the same token, so joins still work.
3. Tamper-evident audit trail - every decision and data access appends a record
   whose hash chains to the previous one. Editing history breaks the chain and
   verify_chain() says exactly where.

What is NOT here, and must not be claimed: encryption at rest. Python's standard
library has no authenticated cipher, and writing one is how security bugs are born.
Until a vetted dependency is approved, disk-level encryption is the honest answer.
"""
import hashlib
import hmac
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

CLASSES = ("public", "internal", "confidential", "personal")

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)(?:\+98|0)?9\d{9}(?!\d)|(?<!\d)\+\d{10,14}(?!\d)")
_NATIONAL_ID = re.compile(r"(?<!\d)\d{10}(?!\d)")
# cards are written in groups as often as not: 4111 1111 1111 1111
_LONG_NUMBER = re.compile(r"(?<!\d)(?:\d[ -]?){12,19}(?!\d)")
_MASK = "***"


def luhn(number: str) -> bool:
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 12:
        return False
    checksum, parity = 0, len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def redact(text: str) -> str:
    """Mask personal identifiers in free text. Order matters: mask emails first."""
    if not text:
        return text
    out = _EMAIL.sub(_MASK, str(text))
    out = _PHONE.sub(_MASK, out)
    out = _NATIONAL_ID.sub(_MASK, out)

    def _maybe_card(m: re.Match) -> str:
        digits = "".join(ch for ch in m.group(0) if ch.isdigit())
        return _MASK if luhn(digits) else m.group(0)

    return _LONG_NUMBER.sub(_maybe_card, out)


def _key() -> bytes:
    secret = os.environ.get("AURORA_PSEUDONYM_KEY")
    if not secret:
        raise RuntimeError("AURORA_PSEUDONYM_KEY is not set: refusing to store "
                           "identifiers without a key outside the data")
    return secret.encode()


def pseudonym(value: str, namespace: str = "default") -> str:
    """Stable, irreversible token. Same input -> same token, so joins survive."""
    mac = hmac.new(_key(), f"{namespace}:{value}".encode(), hashlib.sha256).hexdigest()
    return f"{namespace}_{mac[:24]}"


@dataclass(frozen=True)
class Field:
    name: str
    classification: str

    def __post_init__(self):
        if self.classification not in CLASSES:
            raise ValueError(f"{self.name}: unknown classification {self.classification!r}")


def safe_export(rows: Sequence[Dict[str, str]], schema: Sequence[Field],
                allow: Sequence[str] = ("public", "internal")) -> List[Dict[str, str]]:
    """Project rows to the fields a given audience may see. Personal data is dropped."""
    allowed = {f.name for f in schema if f.classification in allow}
    return [{k: v for k, v in row.items() if k in allowed} for row in rows]


@dataclass
class AuditLog:
    """Append-only, hash-chained. Tampering with any entry breaks every later link."""
    salt: str = "aurora"
    entries: List[dict] = field(default_factory=list)

    def append(self, event: str, payload: str) -> dict:
        prev = self.entries[-1]["hash"] if self.entries else "genesis"
        body = f"{prev}|{event}|{redact(payload)}"
        entry = {"n": len(self.entries), "event": event, "payload": redact(payload),
                 "prev": prev, "hash": hashlib.sha256(body.encode()).hexdigest()}
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> Optional[int]:
        """None when intact, otherwise the index of the first broken link."""
        prev = "genesis"
        for i, e in enumerate(self.entries):
            body = f"{prev}|{e['event']}|{e['payload']}"
            if hashlib.sha256(body.encode()).hexdigest() != e["hash"] or e["prev"] != prev:
                return i
            prev = e["hash"]
        return None
