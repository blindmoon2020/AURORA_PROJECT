from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

AUDIT_FILE = (
    ROOT
    / "snapshots"
    / "broker_resolution_audit.json"
)

REGISTRY_FILE = (
    ROOT
    / "config"
    / "broker_resolution_registry.json"
)


TRACKED_FIELDS = [
    "broker_symbol",
    "confidence",
    "decision",
    "final_status",
    "data_status",
    "execution_status",
    "digits",
    "point",
    "tick_size",
    "tick_value",
    "contract_size",
    "volume_min",
    "volume_step",
    "volume_max",
    "base_currency",
    "quote_currency",
    "margin_currency",
    "volume_kind",
    "trade_mode",
    "execution_capable",
]


def stable_payload(row):
    return {
        field: row.get(field)
        for field in TRACKED_FIELDS
    }


def fingerprint(row):
    payload = stable_payload(row)

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def load_registry():
    if not REGISTRY_FILE.exists():
        return {
            "schema_version": 1,
            "instruments": {},
        }

    return json.loads(
        REGISTRY_FILE.read_text(
            encoding="utf-8"
        )
    )


audit = json.loads(
    AUDIT_FILE.read_text(
        encoding="utf-8"
    )
)

previous = load_registry()

previous_items = previous.get(
    "instruments",
    {}
)

current_items = {}

changes = []


for canonical, row in audit[
    "instruments"
].items():

    current_hash = fingerprint(row)

    old = previous_items.get(canonical)

    if old is None:
        state = "NEW"

    elif old.get("fingerprint") == current_hash:
        state = "UNCHANGED"

    else:
        state = "CHANGED"

    if row.get("final_status") != "PASS":
        state = "BLOCKED"

    current_items[canonical] = {
        "canonical_symbol": canonical,
        "broker_id": (
            audit
            .get("broker", {})
            .get("server", "")
        ),
        "broker_symbol": row.get(
            "broker_symbol"
        ),
        "confidence": row.get(
            "confidence", 0.0
        ),
        "decision": row.get(
            "decision"
        ),
        "final_status": row.get(
            "final_status"
        ),
        "data_status": row.get(
            "data_status"
        ),
        "execution_status": row.get(
            "execution_status"
        ),
        "volume_kind": row.get(
            "volume_kind"
        ),
        "digits": row.get(
            "digits"
        ),
        "point": row.get(
            "point"
        ),
        "tick_size": row.get(
            "tick_size"
        ),
        "tick_value": row.get(
            "tick_value"
        ),
        "contract_size": row.get(
            "contract_size"
        ),
        "volume_min": row.get(
            "volume_min"
        ),
        "volume_step": row.get(
            "volume_step"
        ),
        "volume_max": row.get(
            "volume_max"
        ),
        "base_currency": row.get(
            "base_currency"
        ),
        "quote_currency": row.get(
            "quote_currency"
        ),
        "margin_currency": row.get(
            "margin_currency"
        ),
        "trade_mode": row.get(
            "trade_mode"
        ),
        "execution_capable": row.get(
            "execution_capable"
        ),
        "description": row.get(
            "description"
        ),
        "path": row.get(
            "path"
        ),
        "fingerprint": current_hash,
        "state": state,
        "last_seen": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    if state in {
        "NEW",
        "CHANGED",
        "BLOCKED",
    }:
        changes.append(
            {
                "canonical_symbol": canonical,
                "state": state,
                "broker_symbol": row.get(
                    "broker_symbol"
                ),
                "old_fingerprint": (
                    None
                    if old is None
                    else old.get("fingerprint")
                ),
                "new_fingerprint": current_hash,
            }
        )


registry = {
    "schema_version": 1,
    "generated_at": datetime.now(
        timezone.utc
    ).isoformat(),

    "broker": audit.get(
        "broker",
        {}
    ),

    "execution_policy": "DISABLED",

    "change_policy": {
        "NEW": "REVALIDATE",
        "CHANGED": "BLOCK_UNTIL_REVALIDATED",
        "BLOCKED": "BLOCK",
        "UNCHANGED": "VALID",
    },

    "instruments": current_items,

    "change_summary": {
        "new": sum(
            1
            for x in changes
            if x["state"] == "NEW"
        ),
        "changed": sum(
            1
            for x in changes
            if x["state"] == "CHANGED"
        ),
        "blocked": sum(
            1
            for x in changes
            if x["state"] == "BLOCKED"
        ),
    },

    "changes": changes,
}


REGISTRY_FILE.write_text(
    json.dumps(
        registry,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


print()
print("================================================")
print("AURORA BROKER RESOLUTION REGISTRY")
print("================================================")

for canonical, row in current_items.items():

    print(
        f"{canonical:14} -> "
        f"{str(row['broker_symbol']):12} | "
        f"{row['state']:9} | "
        f"{row['final_status']:5} | "
        f"{row['volume_kind']}"
    )

print()
print(
    "NEW     =",
    registry["change_summary"]["new"]
)

print(
    "CHANGED =",
    registry["change_summary"]["changed"]
)

print(
    "BLOCKED =",
    registry["change_summary"]["blocked"]
)

print()
print("REGISTRY =", REGISTRY_FILE)
