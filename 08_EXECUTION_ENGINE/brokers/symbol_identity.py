from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


FX_CODES = {
    "USD", "EUR", "GBP", "JPY", "CHF",
    "AUD", "CAD", "NZD", "CNH", "NOK",
    "SEK", "SGD", "HKD", "ZAR", "TRY",
    "MXN", "PLN", "HUF", "CZK",
}


@dataclass(frozen=True)
class IdentityDecision:
    canonical_symbol: str
    broker_symbol: str | None
    confidence: float
    decision: str
    reason: str


def norm(value: object) -> str:
    if value is None:
        return ""

    value = str(value).strip().lower()
    value = re.sub(r"[\s_\-./]+", "", value)
    return value


def norm_text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip().lower()


def is_major_index_path(path: str) -> bool:
    return "major indices" in norm_text(path)


def fx_pair_from_description(description: str) -> str | None:
    text = norm_text(description)

    match = re.search(
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)\s+vs\s+"
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)",
        text,
    )

    if not match:
        return None

    base = match.group(1).upper()
    quote = match.group(2).upper()

    if base not in FX_CODES or quote not in FX_CODES:
        return None

    return base + quote


def target_identity(
    canonical: str,
    symbol: str,
    description: str,
    path: str,
) -> tuple[float, str] | None:

    s = norm(symbol)
    d = norm_text(description)
    p = norm_text(path)

    # -----------------------------------------------------
    # FX
    # -----------------------------------------------------

    if canonical in FX_CODES:
        return None

    if len(canonical) == 6:
        base = canonical[:3]
        quote = canonical[3:]

        if base in FX_CODES and quote in FX_CODES:

            if s.startswith(canonical.lower()):
                return (
                    0.99,
                    "broker_symbol_prefix_matches_fx_identity",
                )

            detected = fx_pair_from_description(description)

            if detected == canonical:
                return (
                    0.98,
                    "description_matches_fx_identity",
                )

            return None

    # -----------------------------------------------------
    # Gold
    # -----------------------------------------------------

    if canonical == "XAUUSD":

        if s.startswith("xauusd"):
            return (
                0.99,
                "symbol_matches_xauusd",
            )

        if (
            "gold vs us dollar" in d
            and "commodities" in p
        ):
            return (
                0.98,
                "gold_usd_description_and_commodity_path",
            )

        return None

    # -----------------------------------------------------
    # NASDAQ 100
    # -----------------------------------------------------

    if canonical == "NASDAQ_100":

        if (
            "nasdaq100 index" in d
            and is_major_index_path(path)
        ):
            return (
                0.98,
                "nasdaq100_description_and_major_index_path",
            )

        return None

    # -----------------------------------------------------
    # US30 / DJIA
    # -----------------------------------------------------

    if canonical == "US30":

        if (
            "djia index" in d
            and is_major_index_path(path)
        ):
            return (
                0.98,
                "djia_description_and_major_index_path",
            )

        return None

    # -----------------------------------------------------
    # S&P 500
    # -----------------------------------------------------

    if canonical == "SP500":

        if (
            "s&p500 index" in d
            and is_major_index_path(path)
        ):
            return (
                0.98,
                "sp500_description_and_major_index_path",
            )

        return None

    # -----------------------------------------------------
    # DAX 40
    # -----------------------------------------------------

    if canonical == "DAX40":

        if (
            "dax40 index" in d
            and is_major_index_path(path)
        ):
            return (
                0.98,
                "dax40_description_and_major_index_path",
            )

        return None

    # -----------------------------------------------------
    # Nikkei 225
    # -----------------------------------------------------

    if canonical == "NIKKEI225":

        if (
            "japan 225 index" in d
            and is_major_index_path(path)
        ):
            return (
                0.98,
                "nikkei225_description_and_major_index_path",
            )

        return None

    return None


TARGETS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "USDCHF",
    "AUDUSD",
    "USDCAD",
    "XAUUSD",
    "NASDAQ_100",
    "US30",
    "SP500",
    "DAX40",
    "NIKKEI225",
]


def main() -> int:

    root = Path(__file__).resolve().parents[1]

    discovery_path = (
        root
        / "snapshots"
        / "symbol_discovery_litefinance.json"
    )

    with discovery_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        discovery = json.load(handle)

    decisions: dict[str, list[IdentityDecision]] = {}

    for canonical in TARGETS:

        raw_candidates = (
            discovery
            .get("targets", {})
            .get(canonical, {})
            .get("top_candidates", [])
        )

        matches = []

        for candidate in raw_candidates:

            result = target_identity(
                canonical,
                candidate.get("symbol", ""),
                candidate.get("description", ""),
                candidate.get("path", ""),
            )

            if result is None:
                continue

            confidence, reason = result

            matches.append(
                IdentityDecision(
                    canonical_symbol=canonical,
                    broker_symbol=candidate["symbol"],
                    confidence=confidence,
                    decision="AUTO_CANDIDATE",
                    reason=reason,
                )
            )

        matches.sort(
            key=lambda x: x.confidence,
            reverse=True,
        )

        if not matches:

            decisions[canonical] = [
                IdentityDecision(
                    canonical_symbol=canonical,
                    broker_symbol=None,
                    confidence=0.0,
                    decision="REJECT",
                    reason="no_strong_identity_match",
                )
            ]

        elif len(matches) == 1:

            decisions[canonical] = [
                IdentityDecision(
                    canonical_symbol=matches[0].canonical_symbol,
                    broker_symbol=matches[0].broker_symbol,
                    confidence=matches[0].confidence,
                    decision="AUTO",
                    reason=matches[0].reason,
                )
            ]

        else:

            top = matches[0]
            second = matches[1]

            gap = top.confidence - second.confidence

            if top.confidence >= 0.98 and gap >= 0.05:

                decisions[canonical] = [
                    IdentityDecision(
                        canonical_symbol=top.canonical_symbol,
                        broker_symbol=top.broker_symbol,
                        confidence=top.confidence,
                        decision="AUTO",
                        reason=top.reason,
                    )
                ]

            else:

                decisions[canonical] = [
                    IdentityDecision(
                        canonical_symbol=canonical,
                        broker_symbol=None,
                        confidence=top.confidence,
                        decision="REVIEW",
                        reason=(
                            "multiple plausible candidates "
                            "with insufficient confidence gap"
                        ),
                    )
                ]

    output = {
        "broker": discovery.get("broker", {}),
        "generated_at": discovery.get("generated_at"),
        "decisions": {
            key: [
                {
                    "canonical_symbol": item.canonical_symbol,
                    "broker_symbol": item.broker_symbol,
                    "confidence": item.confidence,
                    "decision": item.decision,
                    "reason": item.reason,
                }
                for item in value
            ]
            for key, value in decisions.items()
        },
    }

    output_path = (
        root
        / "snapshots"
        / "symbol_identity_decisions.json"
    )

    output_path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("")
    print("==========================================")
    print("AURORA UNIVERSAL SYMBOL IDENTITY")
    print("==========================================")

    for canonical, items in decisions.items():

        item = items[0]

        print(
            f"{canonical:12} -> "
            f"{str(item.broker_symbol):12} "
            f"| {item.confidence:.2f} "
            f"| {item.decision}"
        )

    print("")
    print("REPORT =", output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
