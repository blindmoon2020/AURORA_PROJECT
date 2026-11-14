"""The country and index registry: how far AURORA's reach actually goes, and how it grows.

The question this module answers honestly: "all stocks of all countries and all stock
indices" is not a list you type by hand. There are roughly sixty thousand listed companies
worldwide and more than a hundred national indices. Hand-adding tickers produces a catalogue
that looks broad and is arbitrary, and it rots the moment a symbol changes.

So the unit of coverage here is not a symbol but a REGISTRY ENTRY:
  venue  -> country, currency, timezone, session, settlement, and the provider suffix that
            turns a local ticker into a fetchable symbol ("RELIANCE" + XNSE -> RELIANCE.NS)
  index  -> the benchmark of a country, its venue and its provider symbol (^N225, ^GDAXI)

Coverage then becomes a MEASUREMENT (how many countries, continents and indices resolve)
instead of a boast, and growth becomes a data problem - enumerate tickers from a listing
feed - instead of an editing problem.

Honesty rules, same as the asset catalogue:
  - every venue and index carries `verified`; a suffix quoted from memory is an assumption
  - an unknown venue raises; guessing a suffix is how a fetch silently returns the wrong
    company
  - nothing here claims data availability. A venue can be registered and still have no free
    feed; `source_gap` says so per region instead of hiding it.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------- venues by region
EUROPE = "Europe"
AMERICAS = "Americas"
ASIA = "Asia"
AFRICA = "Africa"
MIDDLE_EAST = "Middle East"
OCEANIA = "Oceania"

CONTINENTS: Tuple[str, ...] = (EUROPE, AMERICAS, ASIA, AFRICA, MIDDLE_EAST, OCEANIA)


@dataclass(frozen=True)
class Exchange:
    code: str
    name: str
    country: str
    continent: str
    currency: str
    timezone: str
    suffix: str            # provider suffix for local tickers, "" for bare US tickers
    verified: bool = False
    source_gap: str = ""   # why a free feed may not cover this venue


EXCHANGES: Dict[str, Exchange] = {e.code: e for e in (
    # Americas
    Exchange("XNYS", "بورس نیویورک", "US", AMERICAS, "USD", "America/New_York", "", True),
    Exchange("XNAS", "نزدک", "US", AMERICAS, "USD", "America/New_York", "", True),
    Exchange("XTSX", "بورس تورنتو", "CA", AMERICAS, "CAD", "America/Toronto", ".TO"),
    Exchange("XMEX", "بورس مکزیک", "MX", AMERICAS, "MXN", "America/Mexico_City", ".MX"),
    Exchange("XBSP", "بورس برزیل (B3)", "BR", AMERICAS, "BRL", "America/Sao_Paulo", ".SA"),
    Exchange("XBA", "بورس بوئنوس آیرس", "AR", AMERICAS, "ARS", "America/Argentina/Buenos_Aires", ".BA"),
    Exchange("XSGO", "بورس سانتیاگو", "CL", AMERICAS, "CLP", "America/Santiago", ".SN"),
    Exchange("XLIM", "بورس لیما", "PE", AMERICAS, "PEN", "America/Lima", ".LM"),
    Exchange("XBOG", "بورس کلمبیا", "CO", AMERICAS, "COP", "America/Bogota", ".CL"),
    # Europe
    Exchange("XLON", "بورس لندن", "GB", EUROPE, "GBP", "Europe/London", ".L"),
    Exchange("XPAR", "بورس پاریس", "FR", EUROPE, "EUR", "Europe/Paris", ".PA"),
    Exchange("XETR", "بورس آلمان (Xetra)", "DE", EUROPE, "EUR", "Europe/Berlin", ".DE"),
    Exchange("XMIL", "بورس ایتالیا", "IT", EUROPE, "EUR", "Europe/Rome", ".MI"),
    Exchange("XMAD", "بورس مادرید", "ES", EUROPE, "EUR", "Europe/Madrid", ".MC"),
    Exchange("XAMS", "بورس آمستردام", "NL", EUROPE, "EUR", "Europe/Amsterdam", ".AS"),
    Exchange("XBRU", "بورس بروکسل", "BE", EUROPE, "EUR", "Europe/Brussels", ".BR"),
    Exchange("XSWX", "بورس سوئیس (SIX)", "CH", EUROPE, "CHF", "Europe/Zurich", ".SW"),
    Exchange("XWBO", "بورس وین", "AT", EUROPE, "EUR", "Europe/Vienna", ".VI"),
    Exchange("XLIS", "بورس لیسبون", "PT", EUROPE, "EUR", "Europe/Lisbon", ".LS"),
    Exchange("XSTO", "بورس استکهلم", "SE", EUROPE, "SEK", "Europe/Stockholm", ".ST"),
    Exchange("XOSL", "بورس اسلو", "NO", EUROPE, "NOK", "Europe/Oslo", ".OL"),
    Exchange("XCSE", "بورس کپنهاگ", "DK", EUROPE, "DKK", "Europe/Copenhagen", ".CO"),
    Exchange("XHEL", "بورس هلسینکی", "FI", EUROPE, "EUR", "Europe/Helsinki", ".HE"),
    Exchange("XWAR", "بورس ورشو", "PL", EUROPE, "PLN", "Europe/Warsaw", ".WA"),
    Exchange("XPRA", "بورس پراگ", "CZ", EUROPE, "CZK", "Europe/Prague", ".PR"),
    Exchange("XBUD", "بورس بوداپست", "HU", EUROPE, "HUF", "Europe/Budapest", ".BD"),
    Exchange("XBSE", "بورس بخارست", "RO", EUROPE, "RON", "Europe/Bucharest", ".RO"),
    Exchange("XATH", "بورس آتن", "GR", EUROPE, "EUR", "Europe/Athens", ".AT"),
    Exchange("XDUB", "بورس ایرلند", "IE", EUROPE, "EUR", "Europe/Dublin", ".IR"),
    # Asia
    Exchange("XTKS", "بورس توکیو", "JP", ASIA, "JPY", "Asia/Tokyo", ".T"),
    Exchange("XHKG", "بورس هنگ‌کنگ", "HK", ASIA, "HKD", "Asia/Hong_Kong", ".HK"),
    Exchange("XSHG", "بورس شانگهای", "CN", ASIA, "CNY", "Asia/Shanghai", ".SS",
             False, "دسترسی خارجی محدود؛ فید رایگان ناقص است"),
    Exchange("XSHE", "بورس شنژن", "CN", ASIA, "CNY", "Asia/Shanghai", ".SZ",
             False, "دسترسی خارجی محدود؛ فید رایگان ناقص است"),
    Exchange("XTAI", "بورس تایوان", "TW", ASIA, "TWD", "Asia/Taipei", ".TW"),
    Exchange("XKRX", "بورس کره", "KR", ASIA, "KRW", "Asia/Seoul", ".KS"),
    Exchange("XKOS", "کوسداک", "KR", ASIA, "KRW", "Asia/Seoul", ".KQ"),
    Exchange("XNSE", "بورس ملی هند", "IN", ASIA, "INR", "Asia/Kolkata", ".NS"),
    Exchange("XBOM", "بورس بمبئی", "IN", ASIA, "INR", "Asia/Kolkata", ".BO"),
    Exchange("XIDX", "بورس اندونزی", "ID", ASIA, "IDR", "Asia/Jakarta", ".JK"),
    Exchange("XKLS", "بورس مالزی", "MY", ASIA, "MYR", "Asia/Kuala_Lumpur", ".KL"),
    Exchange("XBKK", "بورس تایلند", "TH", ASIA, "THB", "Asia/Bangkok", ".BK"),
    Exchange("XPHS", "بورس فیلیپین", "PH", ASIA, "PHP", "Asia/Manila", ".PS"),
    Exchange("XHCM", "بورس ویتنام", "VN", ASIA, "VND", "Asia/Ho_Chi_Minh", ".VN"),
    Exchange("XPSX", "بورس پاکستان", "PK", ASIA, "PKR", "Asia/Karachi", ".KA"),
    Exchange("XDHA", "بورس داکا", "BD", ASIA, "BDT", "Asia/Dhaka", ".DH"),
    Exchange("XCOL", "بورس کلمبو", "LK", ASIA, "LKR", "Asia/Colombo", ".CM"),
    # Middle East
    Exchange("XTSE_IR", "بورس اوراق بهادار تهران", "IR", MIDDLE_EAST, "IRR", "Asia/Tehran", ""),
    Exchange("IFB_IR", "فرابورس ایران", "IR", MIDDLE_EAST, "IRR", "Asia/Tehran", ""),
    Exchange("XSAU", "بورس عربستان (تداول)", "SA", MIDDLE_EAST, "SAR", "Asia/Riyadh", ".SR"),
    Exchange("XDFM", "بورس دبی", "AE", MIDDLE_EAST, "AED", "Asia/Dubai", ".AE"),
    Exchange("XQSE", "بورس قطر", "QA", MIDDLE_EAST, "QAR", "Asia/Qatar", ".QA"),
    Exchange("XBIL", "بورس استانبول", "TR", MIDDLE_EAST, "TRY", "Europe/Istanbul", ".IS"),
    Exchange("XTAE", "بورس تل‌آویو", "IL", MIDDLE_EAST, "ILS", "Asia/Jerusalem", ".TA"),
    Exchange("XKUW", "بورس کویت", "KW", MIDDLE_EAST, "KWD", "Asia/Kuwait", ".KW"),
    # Africa
    Exchange("XJSE", "بورس ژوهانسبورگ", "ZA", AFRICA, "ZAR", "Africa/Johannesburg", ".JO"),
    Exchange("XCAI", "بورس مصر", "EG", AFRICA, "EGP", "Africa/Cairo", ".CA"),
    Exchange("XLAG", "بورس نیجریه", "NG", AFRICA, "NGN", "Africa/Lagos", ".LG"),
    Exchange("XNAI", "بورس نایروبی", "KE", AFRICA, "KES", "Africa/Nairobi", ".NR"),
    Exchange("XCAS", "بورس کازابلانکا", "MA", AFRICA, "MAD", "Africa/Casablanca", ".CS"),
    Exchange("XTUN", "بورس تونس", "TN", AFRICA, "TND", "Africa/Tunis", ".TN",
             False, "فید رایگان معمولاً موجود نیست"),
    Exchange("XGHA", "بورس غنا", "GH", AFRICA, "GHS", "Africa/Accra", ".GH",
             False, "فید رایگان معمولاً موجود نیست"),
    # Oceania
    Exchange("XASX", "بورس استرالیا", "AU", OCEANIA, "AUD", "Australia/Sydney", ".AX"),
    Exchange("XNZE", "بورس نیوزیلند", "NZ", OCEANIA, "NZD", "Pacific/Auckland", ".NZ"),
)}


@dataclass(frozen=True)
class IndexDef:
    symbol: str          # provider symbol
    name: str
    country: str
    venue: str
    verified: bool = False


INDICES: List[IndexDef] = [
    IndexDef("^GSPC", "S&P 500", "US", "XNYS", True),
    IndexDef("^DJI", "داو جونز", "US", "XNYS", True),
    IndexDef("^IXIC", "نزدک کامپوزیت", "US", "XNAS", True),
    IndexDef("^NDX", "نزدک ۱۰۰", "US", "XNAS", True),
    IndexDef("^RUT", "راسل ۲۰۰۰", "US", "XNYS", True),
    IndexDef("^GSPTSE", "TSX کانادا", "CA", "XTSX", True),
    IndexDef("^BVSP", "بویسپا برزیل", "BR", "XBSP", True),
    IndexDef("^MXX", "IPC مکزیک", "MX", "XMEX", True),
    IndexDef("^MERV", "مرول آرژانتین", "AR", "XBA", False),
    IndexDef("^FTSE", "فوتسی ۱۰۰", "GB", "XLON", True),
    IndexDef("^FCHI", "کک ۴۰ فرانسه", "FR", "XPAR", True),
    IndexDef("^GDAXI", "دکس آلمان", "DE", "XETR", True),
    IndexDef("^STOXX50E", "یورو استاکس ۵۰", "EU", "XETR", True),
    IndexDef("FTSEMIB.MI", "فوتسی ام آی بی ایتالیا", "IT", "XMIL", False),
    IndexDef("^IBEX", "ایبکس اسپانیا", "ES", "XMAD", True),
    IndexDef("^SSMI", "SMI سوئیس", "CH", "XSWX", True),
    IndexDef("^AEX", "AEX هلند", "NL", "XAMS", True),
    IndexDef("^OMX", "اومکس استکهلم", "SE", "XSTO", False),
    IndexDef("^OSEAX", "بورس اسلو", "NO", "XOSL", False),
    IndexDef("^N225", "نیکه‌ای ۲۲۵ ژاپن", "JP", "XTKS", True),
    IndexDef("^HSI", "هنگ‌سنگ", "HK", "XHKG", True),
    IndexDef("000001.SS", "کامپوزیت شانگهای", "CN", "XSHG", True),
    IndexDef("^TWII", "تایوان وایت", "TW", "XTAI", True),
    IndexDef("^KS11", "کوسپی کره", "KR", "XKRX", True),
    IndexDef("^BSESN", "سنسکس هند", "IN", "XBOM", True),
    IndexDef("^NSEI", "نیفتی ۵۰ هند", "IN", "XNSE", True),
    IndexDef("^JKSE", "جاکارتا کامپوزیت", "ID", "XIDX", True),
    IndexDef("^KLSE", "کوالالامپور", "MY", "XKLS", True),
    IndexDef("^SET.BK", "ست تایلند", "TH", "XBKK", False),
    IndexDef("^AXJO", "ASX 200 استرالیا", "AU", "XASX", True),
    IndexDef("^NZ50", "NZX 50 نیوزیلند", "NZ", "XNZE", True),
    IndexDef("^TASI.SR", "تداول عربستان", "SA", "XSAU", False),
    IndexDef("^TA125.TA", "تل‌آویو ۱۲۵", "IL", "XTAE", False),
    IndexDef("XU100.IS", "بورس استانبول ۱۰۰", "TR", "XBIL", False),
    IndexDef("^JN0U.JO", "JSE Top 40 آفریقای جنوبی", "ZA", "XJSE", False),
    IndexDef("^CASE30", "EGX 30 مصر", "EG", "XCAI", False),
    IndexDef("^TEDPIX", "تدپیکس بورس تهران", "IR", "XTSE_IR", False),
    IndexDef("^TEPIX", "tepix بورس تهران", "IR", "XTSE_IR", False),
]


class UnknownVenue(KeyError):
    """Raised instead of guessing a suffix, which would silently fetch the wrong company."""


def exchange(code: str) -> Exchange:
    try:
        return EXCHANGES[code]
    except KeyError:
        raise UnknownVenue(f"بورس ناشناخته: {code}") from None


def provider_symbol(ticker: str, venue_code: str) -> str:
    """Turn a local ticker into the fetchable symbol for that exchange."""
    ex = exchange(venue_code)
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("نماد خالی است")
    if not ex.suffix:
        return ticker
    return ticker + ex.suffix


def venues_in(continent: str) -> List[Exchange]:
    return sorted((e for e in EXCHANGES.values() if e.continent == continent),
                  key=lambda e: (e.country, e.code))


def country_venues() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for ex in EXCHANGES.values():
        out.setdefault(ex.country, []).append(ex.code)
    return dict(sorted(out.items()))


def indices_for(country: str) -> List[IndexDef]:
    return [i for i in INDICES if i.country == country]


def index_symbol(symbol: str) -> IndexDef:
    for idx in INDICES:
        if idx.symbol == symbol:
            return idx
    raise KeyError(f"شاخص ناشناخته: {symbol}")


def coverage() -> Dict[str, object]:
    """The measured picture, not a claim: countries, continents, venues, indices, gaps."""
    per_continent: Dict[str, int] = {}
    for ex in EXCHANGES.values():
        per_continent[ex.continent] = per_continent.get(ex.continent, 0) + 1
    countries = sorted({ex.country for ex in EXCHANGES.values()})
    gaps = [ex.code for ex in EXCHANGES.values() if ex.source_gap]
    unverified = [ex.code for ex in EXCHANGES.values() if not ex.verified]
    return {
        "venues": len(EXCHANGES),
        "countries": len(countries),
        "country_codes": countries,
        "continents": per_continent,
        "indices": len(INDICES),
        "indices_unverified": [i.symbol for i in INDICES if not i.verified],
        "venues_verified": len(EXCHANGES) - len(unverified),
        "venues_with_free_feed_gap": gaps,
        "countries_without_index": [c for c in countries
                                    if not any(i.country == c for i in INDICES)],
    }


def coverage_line() -> str:
    c = coverage()
    return (f"{c['venues']} بورس در {c['countries']} کشور و {len(c['continents'])} قاره · "
            f"{c['indices']} شاخص ملی · تأییدشده {c['venues_verified']} بورس")


def audit() -> List[str]:
    """Structural problems in the registry itself. Empty list means it is sound."""
    problems: List[str] = []
    seen: Dict[str, int] = {}
    for ex in EXCHANGES.values():
        seen[ex.code] = seen.get(ex.code, 0) + 1
        if ex.continent not in CONTINENTS:
            problems.append(f"{ex.code}: قاره ناشناخته {ex.continent}")
        if not ex.currency or not ex.timezone:
            problems.append(f"{ex.code}: ارز یا منطقه زمانی خالی")
        if ex.source_gap and ex.verified:
            problems.append(f"{ex.code}: هم شکاف داده دارد هم تأییدشده است")
    for idx in INDICES:
        if idx.venue not in EXCHANGES:
            problems.append(f"{idx.symbol}: بورس {idx.venue} تعریف نشده")
    for sym, n in seen.items():
        if n > 1:
            problems.append(f"{sym}: کد تکراری")
    return problems
