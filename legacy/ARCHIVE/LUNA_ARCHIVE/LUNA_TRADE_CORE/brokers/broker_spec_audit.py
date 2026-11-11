from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import MetaTrader5 as mt5

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "config" / "canonical_universe.json"
REPORT = ROOT / "snapshots" / "broker_resolution_audit.json"


def txt(v):
    return "" if v is None else str(v).strip()


def fx_desc(desc):
    m = re.search(
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)\s+vs\s+"
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)",
        txt(desc).lower(),
    )
    return "" if not m else m.group(1).upper() + m.group(2).upper()


def identity(canonical, spec, info):
    name = txt(getattr(info, "name", ""))
    desc = txt(getattr(info, "description", "")).lower()
    path = txt(getattr(info, "path", "")).lower()

    if spec["asset_class"] == "FX":
        expected = spec["base"] + spec["quote"]
        if name.lower().startswith(expected.lower()):
            return 0.99, "fx_symbol_prefix"
        if fx_desc(desc) == expected:
            return 0.98, "fx_description"
        return 0.0, "mismatch"

    if canonical == "XAUUSD":
        if name.lower().startswith("xauusd"):
            return 0.99, "xauusd_symbol"
        if "gold vs us dollar" in desc and "commodit" in path:
            return 0.98, "gold_description_path"
        return 0.0, "mismatch"

    rules = {
        "NASDAQ_100": "nasdaq100 index",
        "US30": "djia index",
        "SP500": "s&p500 index",
        "DAX40": "dax40 index",
        "NIKKEI225": "japan 225 index",
    }

    if canonical in rules:
        if rules[canonical] in desc and "major indices" in path:
            return 0.98, "index_description_major_path"
        return 0.0, "mismatch"

    if canonical == "WTI_OIL":
        if "west texas intermediate" in desc and "\\oil\\" in path:
            return 0.99, "wti_standard_oil_path"
        if "west texas intermediate" in desc or "wti oil" in desc:
            return 0.95, "wti_description"
        return 0.0, "mismatch"

    if canonical == "BRENT_OIL":
        if "brent crude" in desc and "\\oil\\" in path:
            return 0.99, "brent_standard_oil_path"
        if "brent crude" in desc or "brent oil" in desc:
            return 0.95, "brent_description"
        return 0.0, "mismatch"

    return 0.0, "unsupported"


def volume_kind(symbol):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=3)
    rates = mt5.copy_rates_range(
        symbol,
        mt5.TIMEFRAME_M1,
        start,
        end,
    )

    if rates is None or len(rates) == 0:
        return "UNKNOWN", 0, 0

    total = len(rates)
    real = sum(1 for x in rates if int(x["real_volume"]) > 0)

    if real > 0:
        return "REAL", real, total

    return "TICK", 0, total


def validate(info):
    checks = []

    def add(name, ok):
        checks.append({
            "check": name,
            "status": "PASS" if ok else "FAIL",
        })

    tick_size = float(getattr(info, "trade_tick_size", 0) or 0)
    tick_value = float(getattr(info, "trade_tick_value", 0) or 0)
    point = float(getattr(info, "point", 0) or 0)
    vmin = float(getattr(info, "volume_min", 0) or 0)
    vstep = float(getattr(info, "volume_step", 0) or 0)
    vmax = float(getattr(info, "volume_max", 0) or 0)

    add("tick_size_positive", tick_size > 0)
    add("tick_value_positive", tick_value > 0)
    add("point_positive", point > 0)
    add("volume_min_positive", vmin > 0)
    add("volume_step_positive", vstep > 0)
    add("volume_bounds", vmax >= vmin)
    add("digits_valid", int(getattr(info, "digits", -1)) >= 0)
    add(
        "symbol_visible_or_selectable",
        bool(
            getattr(info, "visible", False)
            or getattr(info, "select", False)
        ),
    )

    failed = [
        x["check"]
        for x in checks
        if x["status"] == "FAIL"
    ]

    return checks, ("PASS" if not failed else "BLOCK"), failed


universe = json.loads(
    UNIVERSE.read_text(encoding="utf-8")
)["instruments"]

if not mt5.initialize():
    raise SystemExit(
        f"MT5 initialize failed: {mt5.last_error()}"
    )

try:
    symbols = mt5.symbols_get()

    if symbols is None:
        raise SystemExit(
            f"symbols_get failed: {mt5.last_error()}"
        )

    results = {}

    for canonical, spec in universe.items():

        candidates = []

        for info in symbols:
            score, reason = identity(
                canonical,
                spec,
                info,
            )

            if score > 0:
                candidates.append(
                    (score, reason, info)
                )

        candidates.sort(
            key=lambda x: (
                x[0],
                txt(getattr(x[2], "name", "")),
            ),
            reverse=True,
        )

        if not candidates:
            results[canonical] = {
                "decision": "REJECT",
                "final_status": "BLOCK",
                "broker_symbol": None,
                "confidence": 0.0,
                "reason": "no_identity_candidate",
            }
            continue

        best_score, reason, info = candidates[0]
        second_score = (
            candidates[1][0]
            if len(candidates) > 1
            else 0.0
        )

        gap = best_score - second_score

        strong_identity = (
            best_score >= 0.99
            and reason in {
                "wti_standard_oil_path",
                "brent_standard_oil_path",
            }
        )

        decision = (
            "AUTO"
            if (
                len(candidates) == 1
                or strong_identity
                or (
                    best_score >= 0.98
                    and gap >= 0.05
                )
            )
            else "REVIEW"
        )

        checks, spec_status, failed = validate(info)

        volume, real_count, sample_count = volume_kind(
            txt(getattr(info, "name", ""))
        )

        trade_mode = int(
            getattr(info, "trade_mode", -1)
        )

        execution_capable = (
            trade_mode not in (0, -1)
        )

        data_ready = (
            decision == "AUTO"
            and spec_status == "PASS"
        )

        if decision == "REVIEW":
            data_status = "REVIEW"
        elif spec_status != "PASS":
            data_status = "BLOCK"
        else:
            data_status = "PASS"

        if not data_ready:
            execution_status = "NOT_READY"
        elif not execution_capable:
            execution_status = "BROKER_NOT_EXECUTABLE"
        else:
            execution_status = "READY"

        final_status = data_status

        results[canonical] = {
            "decision": decision,
            "final_status": final_status,
            "broker_symbol": (
                txt(getattr(info, "name", ""))
                if decision == "AUTO"
                else None
            ),
            "confidence": best_score,
            "candidate_count": len(candidates),
            "confidence_gap": gap,
            "identity_reason": reason,

            "description": txt(
                getattr(info, "description", "")
            ),
            "path": txt(
                getattr(info, "path", "")
            ),

            "trade_mode": trade_mode,
            "execution_capable": execution_capable,
            "visible": bool(
                getattr(info, "visible", False)
            ),
            "select": bool(
                getattr(info, "select", False)
            ),

            "digits": int(
                getattr(info, "digits", 0)
            ),
            "point": float(
                getattr(info, "point", 0) or 0
            ),
            "tick_size": float(
                getattr(info, "trade_tick_size", 0) or 0
            ),
            "tick_value": float(
                getattr(info, "trade_tick_value", 0) or 0
            ),
            "contract_size": float(
                getattr(info, "trade_contract_size", 0) or 0
            ),

            "volume_min": float(
                getattr(info, "volume_min", 0) or 0
            ),
            "volume_step": float(
                getattr(info, "volume_step", 0) or 0
            ),
            "volume_max": float(
                getattr(info, "volume_max", 0) or 0
            ),

            "base_currency": txt(
                getattr(info, "currency_base", "")
            ),
            "quote_currency": txt(
                getattr(info, "currency_profit", "")
            ),
            "margin_currency": txt(
                getattr(info, "currency_margin", "")
            ),

            "spread_points": int(
                getattr(info, "spread", 0)
            ),

            "volume_kind": volume,
            "real_volume_bars": real_count,
            "sample_volume_bars": sample_count,

            "spec_status": spec_status,
            "data_status": data_status,
            "execution_status": execution_status,
            "failed_checks": failed,
            "validation_checks": checks,

            "candidates": [
                {
                    "broker_symbol": txt(
                        getattr(candidate[2], "name", "")
                    ),
                    "confidence": candidate[0],
                    "reason": candidate[1],
                    "description": txt(
                        getattr(candidate[2], "description", "")
                    ),
                    "path": txt(
                        getattr(candidate[2], "path", "")
                    ),
                }
                for candidate in candidates
            ],
        }

    terminal = mt5.terminal_info()
    account = mt5.account_info()

    payload = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "broker": {
            "terminal": txt(
                getattr(terminal, "name", "")
            ),
            "server": txt(
                getattr(account, "server", "")
            ),
            "company": txt(
                getattr(terminal, "company", "")
            ),
        },

        "execution_policy": "DISABLED",

        "instruments": results,
    }

    REPORT.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("================================================")
    print("LUNA BROKER RESOLUTION & SPECIFICATION AUDIT")
    print("================================================")

    for canonical, row in results.items():
        print(
            f"{canonical:14} -> "
            f"{str(row['broker_symbol']):12} | "
            f"{row['confidence']:.2f} | "
            f"{row['decision']:6} | "
            f"{row['final_status']:6} | "
            f"{row.get('volume_kind', '-')}"
        )

    print()
    print("REPORT =", REPORT)

finally:
    mt5.shutdown()