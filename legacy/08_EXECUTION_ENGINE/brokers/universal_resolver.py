from pathlib import Path
import json
import re
import MetaTrader5 as mt5

def txt(v):
    return "" if v is None else str(v).strip().lower()

def compact(v):
    return re.sub(r"[\s_\-./]+", "", txt(v))

def fx_desc(d):
    m = re.search(
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)\s+vs\s+"
        r"(usd|eur|gbp|jpy|chf|aud|cad|nzd)",
        txt(d),
    )
    return None if not m else m.group(1).upper() + m.group(2).upper()

def match(c, spec, item):
    name = str(getattr(item, "name", ""))
    desc = str(getattr(item, "description", ""))
    path = str(getattr(item, "path", ""))
    s = compact(name)
    d = txt(desc)
    p = txt(path)
    asset = spec["asset_class"]

    if asset == "FX":
        expected = spec["base"] + spec["quote"]
        if s.startswith(expected.lower()):
            return 0.99, name, "fx_symbol_prefix"
        if fx_desc(desc) == expected:
            return 0.98, name, "fx_description"
        return None

    if c == "XAUUSD":
        if s.startswith("xauusd"):
            return 0.99, name, "xauusd_symbol"
        if "gold vs us dollar" in d and "commodities" in p:
            return 0.98, name, "gold_usd_commodity"
        return None

    rules = {
        "NASDAQ_100": ("nasdaq100 index", None),
        "US30": ("djia index", None),
        "SP500": ("s&p500 index", None),
        "DAX40": ("dax40 index", None),
        "NIKKEI225": ("japan 225 index", None),
        "WTI_OIL": ("west texas intermediate", "wti oil"),
        "BRENT_OIL": ("brent crude", "brent oil"),
    }

    # Oil identity: prefer standard ECN Oil symbols over
    # perpetual/crypto-provider variants.
    if c == "WTI_OIL":
        strong = (
            "west texas intermediate" in d
            and ("\\oil\\" in p or " oil " in (" " + p + " "))
        )
        weak = (
            "west texas intermediate" in d
            or "wti oil" in d
        )

        if strong:
            return 0.99, name, "wti_standard_oil_path"

        if weak and "crypto_com" in p:
            return 0.90, name, "wti_perpetual_variant"

        if weak:
            return 0.95, name, "wti_description"

        return None

    if c == "BRENT_OIL":
        strong = (
            "brent crude" in d
            and ("\\oil\\" in p or " oil " in (" " + p + " "))
        )
        weak = (
            "brent crude" in d
            or "brent oil" in d
        )

        if strong:
            return 0.99, name, "brent_standard_oil_path"

        if weak and "crypto_com" in p:
            return 0.90, name, "brent_perpetual_variant"

        if weak:
            return 0.95, name, "brent_description"

        return None

    if c not in rules:
        return None

    key1, key2 = rules[c]

    if key1 in d and ("major indices" in p or asset != "INDEX"):
        return 0.98, name, "identity_description"

    if key2 and key2 in d:
        return 0.98, name, "identity_description"

    return None


root = Path(__file__).resolve().parents[1]
universe = json.loads(
    (root / "config" / "canonical_universe.json").read_text(
        encoding="utf-8"
    )
)["instruments"]

if not mt5.initialize():
    raise SystemExit(f"MT5 initialize failed: {mt5.last_error()}")

symbols = mt5.symbols_get()

if symbols is None:
    err = mt5.last_error()
    mt5.shutdown()
    raise SystemExit(f"symbols_get failed: {err}")

print()
print("==========================================")
print("AURORA UNIVERSAL MT5 AUTO DISCOVERY")
print("==========================================")

for canonical, spec in universe.items():

    candidates = []

    for item in symbols:
        result = match(canonical, spec, item)

        if result is not None:
            confidence, name, reason = result
            candidates.append((confidence, name, reason))

    candidates.sort(
        key=lambda x: (x[0], x[1]),
        reverse=True,
    )

    if not candidates:
        print(f"{canonical:14} -> {'None':12} | 0.00 | REJECT")
        continue

    best = candidates[0]

    if (
        len(candidates) == 1
        or best[0] - candidates[1][0] >= 0.05
    ):
        decision = "AUTO"
        selected = best[1]
    else:
        decision = "REVIEW"
        selected = None

    print(
        f"{canonical:14} -> "
        f"{str(selected):12} | "
        f"{best[0]:.2f} | {decision} | {best[2]}"
    )

mt5.shutdown()
