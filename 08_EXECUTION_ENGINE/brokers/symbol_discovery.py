from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5


TARGETS = {
    "EURUSD": [
        "eurusd",
        "euro vs us dollar",
        "euro/us dollar",
    ],
    "GBPUSD": [
        "gbpusd",
        "gbp usd",
        "pound",
        "sterling",
    ],
    "USDJPY": [
        "usdjpy",
        "usd jpy",
        "dollar yen",
    ],
    "USDCHF": [
        "usdchf",
        "usd chf",
        "dollar swiss",
    ],
    "AUDUSD": [
        "audusd",
        "aud usd",
        "australian dollar",
    ],
    "USDCAD": [
        "usdcad",
        "usd cad",
        "canadian dollar",
    ],
    "XAUUSD": [
        "xauusd",
        "gold",
        "gold vs us dollar",
    ],
    "NASDAQ_100": [
        "nasdaq100",
        "nasdaq 100",
        "nasdaq",
        "ndx",
        "nq",
    ],
    "US30": [
        "us30",
        "dow jones",
        "dow",
        "wall street 30",
        "djia",
    ],
    "SP500": [
        "sp500",
        "s&p 500",
        "s&p500",
        "us500",
        "spx",
        "es",
    ],
    "DAX40": [
        "dax40",
        "dax 40",
        "germany 40",
        "ger40",
        "dax",
    ],
    "NIKKEI225": [
        "nikkei225",
        "nikkei 225",
        "japan 225",
        "jp225",
        "nikkei",
    ],
    "OIL": [
        "usoil",
        "wti",
        "crude oil",
        "brent",
        "ukoil",
        "oil",
    ],
}


def normalize(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def score_symbol(
    name: str,
    description: str,
    path: str,
    keywords: list[str],
) -> tuple[int, list[str]]:

    name_n = normalize(name)
    description_n = normalize(description)
    path_n = normalize(path)

    score = 0
    reasons: list[str] = []

    for keyword in keywords:
        key = normalize(keyword)

        if not key:
            continue

        if key == name_n:
            score += 100
            reasons.append(f"name_exact:{keyword}")
            continue

        if key in name_n:
            score += 60
            reasons.append(f"name_contains:{keyword}")

        if key in description_n:
            score += 30
            reasons.append(f"description_contains:{keyword}")

        if key in path_n:
            score += 20
            reasons.append(f"path_contains:{keyword}")

    return score, reasons


def main() -> int:
    if not mt5.initialize():
        print("MT5 INITIALIZE FAILED:", mt5.last_error())
        return 1

    terminal = mt5.terminal_info()

    if terminal is None:
        print("MT5 TERMINAL INFO FAILED:", mt5.last_error())
        mt5.shutdown()
        return 1

    symbols = mt5.symbols_get()

    if symbols is None:
        print("MT5 SYMBOL DISCOVERY FAILED:", mt5.last_error())
        mt5.shutdown()
        return 1

    results = {}

    for canonical, keywords in TARGETS.items():
        candidates = []

        for item in symbols:
            name = getattr(item, "name", "")
            description = getattr(item, "description", "")
            path = getattr(item, "path", "")

            score, reasons = score_symbol(
                name,
                description,
                path,
                keywords,
            )

            if score <= 0:
                continue

            info = mt5.symbol_info(name)

            candidate = {
                "symbol": name,
                "description": description,
                "path": path,
                "score": score,
                "reasons": reasons,
            }

            if info is not None:
                candidate.update(
                    {
                        "digits": int(info.digits),
                        "point": float(info.point),
                        "tick_size": float(info.trade_tick_size),
                        "tick_value": float(info.trade_tick_value),
                        "contract_size": float(info.trade_contract_size),
                        "volume_min": float(info.volume_min),
                        "volume_step": float(info.volume_step),
                        "volume_max": float(info.volume_max),
                        "currency_base": getattr(
                            info,
                            "currency_base",
                            None,
                        ),
                        "currency_profit": getattr(
                            info,
                            "currency_profit",
                            None,
                        ),
                        "trade_mode": int(
                            getattr(info, "trade_mode", -1)
                        ),
                    }
                )

            candidates.append(candidate)

        candidates.sort(
            key=lambda x: (
                x["score"],
                x["symbol"],
            ),
            reverse=True,
        )

        results[canonical] = {
            "candidate_count": len(candidates),
            "top_candidates": candidates[:10],
        }

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "broker": {
            "company": getattr(
                terminal,
                "company",
                None,
            ),
            "server": None,
            "terminal": getattr(
                terminal,
                "name",
                None,
            ),
            "build": getattr(
                terminal,
                "build",
                None,
            ),
        },
        "symbol_count": len(symbols),
        "targets": results,
    }

    account = mt5.account_info()

    if account is not None:
        report["broker"]["server"] = getattr(
            account,
            "server",
            None,
        )

    output_path = (
        Path(__file__).resolve().parents[1]
        / "snapshots"
        / "symbol_discovery_litefinance.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("")
    print("========================================")
    print("AURORA SYMBOL DISCOVERY AUDIT")
    print("========================================")
    print("MT5 SYMBOL COUNT =", len(symbols))
    print(
        "SERVER =",
        report["broker"]["server"],
    )
    print("")

    for canonical, data in results.items():
        print(f"[{canonical}]")
        print(
            "  candidates =",
            data["candidate_count"],
        )

        for candidate in data["top_candidates"][:5]:
            print(
                "  ",
                candidate["symbol"],
                "| score=",
                candidate["score"],
                "|",
                candidate["description"],
            )

        print("")

    print(
        "REPORT =",
        output_path,
    )

    mt5.shutdown()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
