"""The global asset catalogue: classes, venues, contract units, hours and settlement.

"All markets" is a slogan until something knows what a market is. Before this module the
system had a US-equity pipeline, a Yahoo fetch and a Tehran CSV reader, and no single place
that answered three questions a real platform must answer for every instrument:

  1. What is this, and on which venue does it trade?   (class, venue, currency)
  2. What is one unit worth moving?                    (contract size, tick value)
  3. When is it open, and when does the money settle?  (session, settlement)

Design rules, deliberately institutional:
- UNKNOWN IS A BUILD ERROR. `get()` raises on an unknown symbol instead of inventing a
  default venue, because a default venue is how a strategy ends up pricing coffee with
  equity hours.
- EVERY ROW CARRIES `verified`. A contract size quoted from memory is an assumption, and
  an assumption that is not labelled becomes a fact nobody checks. The coverage report
  prints the split so the honest number is always visible.
- NO PRICES LIVE HERE. This is a catalogue, not a feed: it stays correct when the internet
  is cut, which is the offline requirement.
- VENUE HOURS ARE LOCAL, with settlement as a plain T+n. Exchange holidays are NOT
  modelled here beyond the US calendar in aurora.market_calendar, and the report says so.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------- asset classes
EQUITY = "equity"
ETF = "etf"
FUND = "fund"
FIXED_INCOME = "fixed_income"
FX = "fx"
CRYPTO = "crypto"
NFT = "nft"
ENERGY = "energy"
METALS = "metals"
AGRI = "agri"
INDEX = "index"
METAVERSE = "metaverse"

ASSET_CLASSES: Tuple[str, ...] = (
    EQUITY, ETF, FUND, FIXED_INCOME, FX, CRYPTO, NFT,
    ENERGY, METALS, AGRI, INDEX, METAVERSE,
)

CLASS_LABELS: Dict[str, str] = {
    EQUITY: "سهام", ETF: "ETF", FUND: "صندوق سرمایه‌گذاری",
    FIXED_INCOME: "اوراق بهادار و درآمد ثابت", FX: "جفت‌ارز",
    CRYPTO: "رمز ارز", NFT: "NFT", ENERGY: "انرژی",
    METALS: "فلزات", AGRI: "کالای کشاورزی", INDEX: "شاخص",
    METAVERSE: "متاورس",
}


@dataclass(frozen=True)
class Venue:
    code: str                 # short internal code, not a claim about the MIC
    name: str
    country: str
    timezone: str
    currency: str
    open_local: str           # "HH:MM" local
    close_local: str
    days: str                 # "Mon-Fri", "Sat-Wed", "24/7"
    settlement: str           # "T+2", "T+1", "instant", "T+0"
    regulator: str
    notes: str = ""
    verified: bool = False    # hours and settlement read from the exchange, or assumed


VENUES: Dict[str, Venue] = {
    "XNYS": Venue("XNYS", "بورس نیویورک", "US", "America/New_York", "USD",
                  "09:30", "16:00", "Mon-Fri", "T+1", "SEC",
                  "ساعات و تسویه از سند رسمی بورس؛ تقویم تعطیلات در market_calendar", True),
    "XNAS": Venue("XNAS", "نزدک", "US", "America/New_York", "USD",
                  "09:30", "16:00", "Mon-Fri", "T+1", "SEC", "", True),
    "XLON": Venue("XLON", "بورس لندن", "GB", "Europe/London", "GBP",
                  "08:00", "16:30", "Mon-Fri", "T+2", "FCA", "", False),
    "XETR": Venue("XETR", "بورس آلمان (Xetra)", "DE", "Europe/Berlin", "EUR",
                  "09:00", "17:30", "Mon-Fri", "T+2", "BaFin", "", False),
    "XTKS": Venue("XTKS", "بورس توکیو", "JP", "Asia/Tokyo", "JPY",
                  "09:00", "15:00", "Mon-Fri", "T+2", "FSA Japan",
                  "جلسه استراحت میان‌روز مدل نشده", False),
    "XHKG": Venue("XHKG", "بورس هنگ‌کنگ", "HK", "Asia/Hong_Kong", "HKD",
                  "09:30", "16:00", "Mon-Fri", "T+2", "SFC", "", False),
    "XSHG": Venue("XSHG", "بورس شانگهای", "CN", "Asia/Shanghai", "CNY",
                  "09:30", "15:00", "Mon-Fri", "T+1", "CSRC",
                  "دسترسی خارجی محدود است؛ داده رایگان قابل اتکا نیست", False),
    "XNSE": Venue("XNSE", "بورس ملی هند", "IN", "Asia/Kolkata", "INR",
                  "09:15", "15:30", "Mon-Fri", "T+1", "SEBI", "", False),
    "XTSE_IR": Venue("XTSE_IR", "بورس اوراق بهادار تهران", "IR", "Asia/Tehran", "IRR",
                     "09:00", "12:30", "Sat-Wed", "T+2", "سازمان بورس و اوراق بهادار",
                     "دامنه نوسان روزانه و حجم مبنا قواعد خاص خود را دارند", False),
    "IFB_IR": Venue("IFB_IR", "فرابورس ایران", "IR", "Asia/Tehran", "IRR",
                    "09:00", "12:30", "Sat-Wed", "T+2", "سازمان بورس و اوراق بهادار", "", False),
    "IME_IR": Venue("IME_IR", "بورس کالای ایران", "IR", "Asia/Tehran", "IRR",
                    "10:00", "17:00", "Sat-Thu", "T+2", "سازمان بورس و اوراق بهادار",
                    "زعفران، پسته، زیره و محصولات پتروشیمی؛ مشخصات قرارداد نیازمند تأیید", False),
    "XCME": Venue("XCME", "CME", "US", "America/Chicago", "USD",
                  "17:00", "16:00", "Sun-Fri", "T+1", "CFTC",
                  "جلسه تقریباً ۲۴ ساعته؛ ساعات باید از تقویم محصول تأیید شود", False),
    "XNYM": Venue("XNYM", "NYMEX", "US", "America/New_York", "USD",
                  "18:00", "17:00", "Sun-Fri", "T+1", "CFTC", "", False),
    "XCOM": Venue("XCOM", "COMEX", "US", "America/New_York", "USD",
                  "18:00", "17:00", "Sun-Fri", "T+1", "CFTC", "", False),
    "XCBT": Venue("XCBT", "CBOT", "US", "America/Chicago", "USD",
                  "19:00", "14:20", "Sun-Fri", "T+1", "CFTC", "", False),
    "XICE": Venue("XICE", "ICE Futures", "US", "America/New_York", "USD",
                  "03:00", "14:30", "Mon-Fri", "T+1", "CFTC", "ساعات محصول‌به‌محصول متفاوت است", False),
    "XCRYPTO": Venue("XCRYPTO", "صرافی‌های رمزارز (تجمیعی)", "XX", "UTC", "USDT",
                     "00:00", "24:00", "24/7", "instant", "خودتنظیم",
                     "۲۴ ساعته و بدون تسویه سنتی؛ ریسک نگهداری جداگانه بررسی می‌شود", False),
    "XFX": Venue("XFX", "بازار جهانی ارز (OTC)", "XX", "UTC", "USD",
                 "00:00", "24:00", "Mon-Fri", "T+2", "خودتنظیم",
                 "بازار خارج از بورس؛ بهترين قيمت از تجمیع چند منبع", False),
}


@dataclass(frozen=True)
class Instrument:
    symbol: str
    name: str
    asset_class: str
    venue: str
    unit: str                 # what one contract/lot moves
    size: float               # units per contract, 1 for spot equities
    size_unit: str            # "share", "oz", "bbl", "bushel", "lb", "kg", "MMBtu"
    currency: str
    verified: bool = False
    note: str = ""


def _i(*rows) -> List[Instrument]:
    return [Instrument(*r) for r in rows]


INSTRUMENTS: List[Instrument] = _i(
    # --- US equities: the pipeline that already exists
    ("AAPL", "اپل", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("MSFT", "مایکروسافت", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("JPM", "جی‌پی مورگان", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("KO", "کوکاکولا", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    # --- ETFs and funds
    ("SPY", "ETF اس‌اند‌پی ۵۰۰", ETF, "XNYS", "واحد", 1, "share", "USD", True),
    ("VTSAX", "صندوق شاخص کل بازار", FUND, "XNAS", "واحد", 1, "share", "USD", True),
    ("صندوق_طلا", "صندوق طلای بورس تهران", FUND, "XTSE_IR", "واحد", 1, "share", "IRR", False),
    ("صندوق_اهرم", "صندوق اهرمی بورس تهران", FUND, "XTSE_IR", "واحد", 1, "share", "IRR", False,
     "اهرم صندوق قاعده پذیره‌نویسی و ضامن دارد؛ پیش از معامله باید بررسی شود"),
    ("TLT", "ETF اوراق خزانه بلندمدت", ETF, "XNAS", "واحد", 1, "share", "USD", True),
    ("GLD", "ETF طلا", ETF, "XNYS", "واحد", 1, "share", "USD", True),
    ("XAUUSD", "انس طلا در برابر دلار", METALS, "XFX", "اونس", 1, "oz", "USD", True),
    ("XAGUSD", "نقره در برابر دلار", METALS, "XFX", "اونس", 1, "oz", "USD", True),
    ("XPTUSD", "پلاتین در برابر دلار", METALS, "XFX", "اونس", 1, "oz", "USD", False),
    # --- energy
    ("CL", "نفت خام وست تگزاس (آتی)", ENERGY, "XNYM", "بشکه", 1000, "bbl", "USD", True),
    ("BZ", "نفت برنت (آتی)", ENERGY, "XICE", "بشکه", 1000, "bbl", "USD", False),
    ("NG", "گاز طبیعی (آتی)", ENERGY, "XNYM", "MMBtu", 10000, "MMBtu", "USD", True),
    # --- metals futures
    ("GC", "طلا (آتی)", METALS, "XCOM", "اونس", 100, "oz", "USD", True),
    ("SI", "نقره (آتی)", METALS, "XCOM", "اونس", 5000, "oz", "USD", True),
    ("HG", "مس (آتی)", METALS, "XCOM", "پوند", 25000, "lb", "USD", False),
    # --- agriculture
    ("ZC", "ذرت (آتی)", AGRI, "XCBT", "بوشل", 5000, "bushel", "USD", True),
    ("ZW", "گندم شیکاگو (آتی)", AGRI, "XCBT", "بوشل", 5000, "bushel", "USD", True),
    ("ZS", "سویا (آتی)", AGRI, "XCBT", "بوشل", 5000, "bushel", "USD", True),
    ("KC", "قهوه عربیکا (آتی)", AGRI, "XICE", "پوند", 37500, "lb", "USD", True),
    ("SB", "شکر (آتی)", AGRI, "XICE", "پوند", 112000, "lb", "USD", False),
    ("CC", "کاکائو (آتی)", AGRI, "XICE", "تن متریک", 10, "kg", "USD", False),
    ("CT", "پنبه (آتی)", AGRI, "XICE", "پوند", 50000, "lb", "USD", False),
    # --- Iran: equities and the exchange's own agricultural complex
    ("فولاد", "فولاد مبارکه", EQUITY, "XTSE_IR", "سهم", 1, "share", "IRR", False),
    ("خودرو", "ایران خودرو", EQUITY, "XTSE_IR", "سهم", 1, "share", "IRR", False),
    ("شپنا", "پالایش نفت اصفهان", EQUITY, "XTSE_IR", "سهم", 1, "share", "IRR", False),
    ("زعفران_نگین", "زعفران نگین (آتی بورس کالا)", AGRI, "IME_IR", "کیلوگرم", 1, "kg", "IRR", False,
     "مشخصات قرارداد باید از سند بورس کالای ایران تأیید شود"),
    ("زعفران_پوشال", "زعفران پوشال (آتی بورس کالا)", AGRI, "IME_IR", "کیلوگرم", 1, "kg", "IRR", False,
     "مشخصات قرارداد باید از سند بورس کالای ایران تأیید شود"),
    ("پسته", "پسته (بورس کالا)", AGRI, "IME_IR", "کیلوگرم", 1, "kg", "IRR", False),
    # --- FX: the majors and the crosses a platform is expected to quote
    ("EURUSD", "یورو/دلار", FX, "XFX", "واحد", 100000, "unit", "USD", True),
    ("GBPUSD", "پوند/دلار", FX, "XFX", "واحد", 100000, "unit", "USD", True),
    ("USDJPY", "دلار/ین", FX, "XFX", "واحد", 100000, "unit", "JPY", True),
    ("USDCHF", "دلار/فرانک", FX, "XFX", "واحد", 100000, "unit", "CHF", False),
    ("AUDUSD", "دلار استرالیا/دلار", FX, "XFX", "واحد", 100000, "unit", "USD", False),
    ("USDCAD", "دلار/دلار کانادا", FX, "XFX", "واحد", 100000, "unit", "CAD", False),
    ("NZDUSD", "دلار نیوزيلند/دلار", FX, "XFX", "واحد", 100000, "unit", "USD", False),
    ("EURGBP", "یورو/پوند", FX, "XFX", "واحد", 100000, "unit", "GBP", False),
    ("USDIRR", "دلار/ریال", FX, "XFX", "واحد", 1, "unit", "IRR", False,
     "نرخ رسمی و بازار آزاد دو چیز متفاوت‌اند؛ منبع باید صریح باشد"),
    # --- crypto
    ("BTC-USD", "بیت‌کوین", CRYPTO, "XCRYPTO", "واحد", 1, "coin", "USD", True),
    ("ETH-USD", "اتریوم", CRYPTO, "XCRYPTO", "واحد", 1, "coin", "USD", True),
    ("SOL-USD", "سولانا", CRYPTO, "XCRYPTO", "واحد", 1, "coin", "USD", False),
    # --- indices
    ("ES", "S&P 500 (آتی)", INDEX, "XCME", "شاخص", 50, "index", "USD", True),
    ("NQ", "نزدک ۱۰۰ (آتی)", INDEX, "XCME", "شاخص", 20, "index", "USD", True),
    # --- fixed income
    ("ZN", "اوراق خزانه ۱۰ ساله (آتی)", FIXED_INCOME, "XCBT", "صورت", 100000, "face", "USD", False),
    ("BND", "ETF اوراق کل بازار", FIXED_INCOME, "XNAS", "واحد", 1, "share", "USD", False),
    # --- instruments that exist but are NOT yet investable here, declared on purpose
    ("NFT-BAYC", "مجموعه‌های NFT (نمونه)", NFT, "XCRYPTO", "توکن", 1, "token", "ETH", False,
     "داده قیمت نهادی رایگان ندارد؛ بدون API معتبر وارد تصمیم نمی‌شود"),
    ("SAND-USD", "سندباکس (متاورس)", METAVERSE, "XCRYPTO", "توکن", 1, "token", "USD", False),
)

_BY_SYMBOL: Dict[str, Instrument] = {i.symbol: i for i in INSTRUMENTS}


class UnknownInstrument(KeyError):
    """Raised instead of guessing a venue, a size or a settlement rule."""


def get(symbol: str) -> Instrument:
    try:
        return _BY_SYMBOL[symbol]
    except KeyError:
        raise UnknownInstrument(
            f"{symbol} در کاتالوگ نیست؛ حدس‌زدن کلاس و بورس مجاز نیست") from None


def exists(symbol: str) -> bool:
    return symbol in _BY_SYMBOL


def by_class(asset_class: str) -> List[Instrument]:
    return [i for i in INSTRUMENTS if i.asset_class == asset_class]


def by_venue(code: str) -> List[Instrument]:
    return [i for i in INSTRUMENTS if i.venue == code]


def venue(code: str) -> Venue:
    try:
        return VENUES[code]
    except KeyError:
        raise UnknownInstrument(f"بورس ناشناخته: {code}") from None


def search(text: str) -> List[Instrument]:
    needle = text.strip().lower()
    if not needle:
        return []
    return [i for i in INSTRUMENTS
            if needle in i.symbol.lower() or needle in i.name.lower()]


def contract_value(symbol: str, price: float) -> float:
    """Cash value of one contract at a price, in the instrument's own currency."""
    inst = get(symbol)
    if price <= 0:
        raise ValueError("قیمت باید مثبت باشد")
    return inst.size * float(price)


def coverage() -> Dict[str, object]:
    """The honest picture: what is covered, and how much of it is actually verified."""
    classes = {}
    for inst in INSTRUMENTS:
        classes[inst.asset_class] = classes.get(inst.asset_class, 0) + 1
    venues_used = sorted({i.venue for i in INSTRUMENTS})
    verified = sum(1 for i in INSTRUMENTS if i.verified)
    missing = [c for c in ASSET_CLASSES if c not in classes]
    return {
        "instruments": len(INSTRUMENTS),
        "verified": verified,
        "unverified": len(INSTRUMENTS) - verified,
        "classes_covered": len(classes),
        "classes_missing": missing,
        "venues_used": venues_used,
        "venues_declared": len(VENUES),
        "per_class": dict(sorted(classes.items())),
    }


def coverage_line() -> str:
    c = coverage()
    return (f"{c['instruments']} ابزار در {c['classes_covered']} کلاس و "
            f"{len(c['venues_used'])} بورس · تأییدشده {c['verified']} · "
            f"فرض {c['unverified']}")


# ---------------------------------------------------------------- self audit
def audit() -> List[str]:
    """Structural problems in the catalogue itself. Empty list means it is sound."""
    problems: List[str] = []
    seen: Dict[str, int] = {}
    for inst in INSTRUMENTS:
        seen[inst.symbol] = seen.get(inst.symbol, 0) + 1
        if inst.venue not in VENUES:
            problems.append(f"{inst.symbol}: بورس {inst.venue} تعریف نشده")
        if inst.asset_class not in ASSET_CLASSES:
            problems.append(f"{inst.symbol}: کلاس {inst.asset_class} تعریف نشده")
        if inst.size <= 0:
            problems.append(f"{inst.symbol}: اندازه قرارداد نامعتبر")
        if not inst.size_unit:
            problems.append(f"{inst.symbol}: واحد اندازه خالی است")
        # a venue may legitimately quote several currencies only where it is an OTC or
        # multi-venue aggregate; anywhere else a mismatch is a data error, not a choice
        multi_currency = {"XFX", "XCRYPTO"}
        if inst.venue in VENUES and inst.venue not in multi_currency \
                and inst.currency != VENUES[inst.venue].currency:
            problems.append(f"{inst.symbol}: ارز با ارز بورس نمی‌خواند")
    problems += [f"{s}: نماد تکراری ({n} بار)" for s, n in seen.items() if n > 1]
    return problems
