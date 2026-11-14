"""Customer data vault: the four categories the owner named, each with a rule.

Bank accounts, portfolio holdings, private identifiers and executed trades are not
one kind of data. Treating them as one is how a system ends up either leaking a
national ID or unable to compute a return. So each field carries a classification
and the classification decides what happens to it:

  personal      -> pseudonymised on write; never stored in the clear
  confidential  -> stored, never leaves the vault except as an aggregate
  internal      -> stored and usable inside the platform
  public        -> free to move

Rules that matter more than the storage itself:
- a personal field with no pseudonymisation key RAISES; it does not degrade to
  writing the value, because that is the failure nobody notices.
- the vault file is created 0600 and every write appends to the tamper-evident log,
  so reading a customer's portfolio leaves a mark.
- money is stored as integer minor units, never as a float: a rounding error in a
  portfolio balance is a customer complaint, not a bug report.
"""
import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from aurora.privacy import AuditLog, CLASSES, pseudonym, redact

# Field names as they arrive from brokers, banks and the platform itself.
FIELD_POLICY: Dict[str, str] = {
    # bank
    "iban": "personal", "sheba": "personal", "account_number": "personal",
    "card_number": "personal", "bank_name": "confidential",
    # identity
    "national_id": "personal", "national_code": "personal", "passport": "personal",
    "email": "personal", "phone": "personal", "mobile": "personal",
    "address": "personal", "birth_date": "personal", "full_name": "personal",
    # portfolio and trades
    "customer_id": "personal", "holdings": "confidential", "positions": "confidential",
    "cost_basis": "confidential", "pnl": "confidential", "cash_balance": "confidential",
    "symbol": "internal", "quantity": "confidential", "price": "internal",
    "side": "internal", "ts": "internal", "ticket_id": "internal",
    # project data
    "source": "public", "dataset": "public", "revision": "public", "note": "internal",
}

PERSONAL = tuple(k for k, v in FIELD_POLICY.items() if v == "personal")
CONFIDENTIAL = tuple(k for k, v in FIELD_POLICY.items() if v == "confidential")


class VaultError(RuntimeError):
    """A write that would have stored personal data in the clear."""


def classify(field_name: str) -> str:
    """Unknown fields are confidential, not public: the safe default is 'do not leak'."""
    return FIELD_POLICY.get(field_name, "confidential")


def protect(record: Dict[str, Any], namespace: str = "customer") -> Dict[str, Any]:
    """Return a copy safe to persist: identifiers replaced by stable tokens."""
    out: Dict[str, Any] = {}
    for k, v in record.items():
        cls = classify(k)
        if cls == "personal" and v not in (None, ""):
            try:
                out[k] = pseudonym(str(v), namespace=namespace)
            except RuntimeError as exc:      # no key: refuse, never write the value
                raise VaultError(str(exc)) from exc
            out[f"{k}__redacted"] = True
        elif cls == "personal":
            out[k] = None
        else:
            out[k] = v
    return out


def aggregate_holdings(records: Sequence[Dict[str, Any]], by: str = "symbol") -> Dict[str, float]:
    """What may leave the vault: exposure per instrument, with no customer attached."""
    out: Dict[str, float] = {}
    for r in records:
        key = str(r.get(by, "?"))
        out[key] = out.get(key, 0.0) + float(r.get("quantity", 0) or 0)
    return out


@dataclass
class CustomerVault:
    """Append-only JSONL store for protected customer records."""
    path: Path
    log: AuditLog = field(default_factory=lambda: AuditLog(salt="customer-vault"))

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
            os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)   # 0600

    def write(self, event: str, record: Dict[str, Any]) -> Dict[str, Any]:
        safe = protect(record)
        # a second pass: belt and braces, in case a value hid inside a nested string
        line = redact(json.dumps(safe, ensure_ascii=False, sort_keys=True))
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        self.log.append(event, line)
        return safe

    def read_rows(self) -> List[Dict[str, Any]]:
        self.log.append("read", f"{self.path.name}")
        return [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def public_view(self, allow: Sequence[str] = ("public", "internal")) -> List[Dict[str, Any]]:
        allowed = set(allow)
        return [{k: v for k, v in row.items() if classify(k) in allowed}
                for row in self.read_rows()]


# ---------------------------------------------------------- account-level money
# Cash, fees and lot cost basis are what a customer actually loses sleep over, and
# floats are the wrong type for them: 0.1 + 0.2 != 0.3 is a support ticket.
MONEY_FIELDS = ("cash_balance", "cash", "fee", "fees", "commission", "cost_basis",
                "proceeds", "dividend", "deposit", "withdrawal")


def money(value: float, decimals: int = 2) -> int:
    """Store money as integer minor units. Never persist a float balance."""
    return int(round(float(value) * (10 ** decimals)))


def from_minor(units: int, decimals: int = 2) -> float:
    return units / (10 ** decimals)


def protect_account(snapshot: Dict[str, Any], namespace: str = "account") -> Dict[str, Any]:
    """An account snapshot: identity removed, money in minor units, fees kept separately.

    Fees are kept as their own field rather than folded into cash, because a
    platform that cannot separate cost from performance cannot prove either.
    """
    out: Dict[str, Any] = {}
    for k, v in snapshot.items():
        if k in MONEY_FIELDS and v is not None:
            out[f"{k}_minor"] = money(v)
            continue
        cls = classify(k)
        if cls == "personal" and v not in (None, ""):
            try:
                out[k] = pseudonym(str(v), namespace=namespace)
            except RuntimeError as exc:
                raise VaultError(str(exc)) from exc
            out[f"{k}__redacted"] = True
        else:
            out[k] = v
    gross = sum(from_minor(out.get(f, 0)) for f in ("proceeds_minor",))
    fees = from_minor(out.get("fee_minor", 0)) + from_minor(out.get("commission_minor", 0))
    if gross or fees:
        out["net_minor"] = money(gross - fees)
        out["cost_share_pct"] = round(fees / gross * 100, 4) if gross else 0.0
    return out


def account_total(rows: Sequence[Dict[str, Any]], field_name: str = "cash_balance_minor") -> int:
    """Sum a money column across accounts without ever touching a float."""
    return sum(int(r.get(field_name, 0) or 0) for r in rows)
