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
    "XMATIF": Venue("XMATIF", "یورونکست پاریس (MATIF)", "FR", "Europe/Paris", "EUR",
                     "10:45", "18:30", "Mon-Fri", "T+2", "AMF",
                     "گندم، ذرت و کلزا اروپا", False),
    "XBMD": Venue("XBMD", "بورس مالزی (BMD)", "MY", "Asia/Kuala_Lumpur", "MYR",
                  "10:30", "18:00", "Mon-Fri", "T+1", "SC",
                  "روغن نخل؛ ساعات و قرارداد نیازمند تأیید", False),
    "XSHFE": Venue("XSHFE", "بورس آتی شانگهای", "CN", "Asia/Shanghai", "CNY",
                   "09:00", "15:00", "Mon-Fri", "T+1", "CSRC",
                   "دسترسی خارجی محدود؛ فولاد و فلزات صنعتی", False),
    "XTOCOM": Venue("XTOCOM", "بورس کالای توکیو", "JP", "Asia/Tokyo", "JPY",
                    "09:00", "15:15", "Mon-Fri", "T+1", "FSA Japan",
                    "لاستیک و پلاتین؛ نقدینگی محدود", False),
    "XEUREX": Venue("XEUREX", "یورکس (Eurex)", "DE", "Europe/Berlin", "EUR",
                    "09:00", "17:30", "Mon-Fri", "T+2", "BaFin",
                    "باند آلمان و مشتقات نرخ بهره اروپا", False),
    "XLME": Venue("XLME", "بورس فلزات لندن (LME)", "GB", "Europe/London", "USD",
                  "01:00", "19:00", "Mon-Fri", "T+2", "FCA",
                  "بازار خارج از بورس با تسویه روزانه؛ فید رایگان ناقص است", False),
    "XOSE": Venue("XOSE", "بورس اوراق و مشتقات اوساکا", "JP", "Asia/Tokyo", "JPY",
                  "09:00", "15:15", "Mon-Fri", "T+1", "FSA Japan",
                  "قرارداد آتی اوراق ژاپن (JGB)", False),
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
    ("JNJ", "جانسون اند جانسون", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("AMZN", "آمازون", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("GOOGL", "آلفابت", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("META", "متا", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("NVDA", "انویدیا", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("CSCO", "سیسکو", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("INTC", "اینتل", EQUITY, "XNAS", "سهم", 1, "share", "USD", True),
    ("ORCL", "اوراکل", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("IBM", "آی‌بی‌ام", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("CAT", "کاترپیلار", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("GE", "جنرال الکتریک", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("WMT", "والمارت", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("PG", "پروکتر اند گمبل", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("WFC", "ولز فارگو", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("BAC", "بنک آو امریکا", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("F", "فورد", EQUITY, "XNYS", "سهم", 1, "share", "USD", True),
    ("EFA", "ETF سهام توسعه‌یافته", ETF, "XNYS", "واحد", 1, "share", "USD", True),
    ("EEM", "ETF سهام بازارهای نوظهور", ETF, "XNYS", "واحد", 1, "share", "USD", True),
    ("DBC", "ETF سبد کالا", ETF, "XNYS", "واحد", 1, "share", "USD", True),
    ("CL=F", "نفت خام WTI (قرارداد پیوسته)", ENERGY, "XNYM", "بشکه", 1000, "bbl", "USD", True),
    ("ZC=F", "ذرت (قرارداد پیوسته)", AGRI, "XCBT", "بوشل", 5000, "bushel", "USD", True),
    ("GC=F", "طلا (قرارداد پیوسته)", METALS, "XCOM", "اونس", 100, "oz", "USD", True),
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
    ('EURJPY', 'EUR/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURCHF', 'EUR/CHF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURAUD', 'EUR/AUD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURCAD', 'EUR/CAD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURNZD', 'EUR/NZD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('GBPJPY', 'GBP/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('GBPCHF', 'GBP/CHF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('GBPAUD', 'GBP/AUD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('GBPCAD', 'GBP/CAD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('GBPNZD', 'GBP/NZD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('AUDJPY', 'AUD/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('AUDCAD', 'AUD/CAD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('AUDCHF', 'AUD/CHF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('AUDNZD', 'AUD/NZD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('CADJPY', 'CAD/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('CADCHF', 'CAD/CHF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('CHFJPY', 'CHF/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('NZDJPY', 'NZD/JPY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('NZDCAD', 'NZD/CAD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('NZDCHF', 'NZD/CHF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURSEK', 'EUR/SEK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURNOK', 'EUR/NOK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURPLN', 'EUR/PLN', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURTRY', 'EUR/TRY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURHUF', 'EUR/HUF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('EURCZK', 'EUR/CZK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', True, ''),
    ('USDCNH', 'USD/CNH', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDMXN', 'USD/MXN', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDBRL', 'USD/BRL', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDZAR', 'USD/ZAR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDTRY', 'USD/TRY', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDINR', 'USD/INR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDKRW', 'USD/KRW', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDSGD', 'USD/SGD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDHKD', 'USD/HKD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDSEK', 'USD/SEK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDNOK', 'USD/NOK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDDKK', 'USD/DKK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDPLN', 'USD/PLN', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDHUF', 'USD/HUF', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDCZK', 'USD/CZK', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDILS', 'USD/ILS', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDTHB', 'USD/THB', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDIDR', 'USD/IDR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDPHP', 'USD/PHP', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDTWD', 'USD/TWD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDCLP', 'USD/CLP', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDCOP', 'USD/COP', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDPEN', 'USD/PEN', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDARS', 'USD/ARS', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDSAR', 'USD/SAR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDAED', 'USD/AED', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDPKR', 'USD/PKR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDBDT', 'USD/BDT', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDLKR', 'USD/LKR', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDNGN', 'USD/NGN', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDKES', 'USD/KES', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDMAD', 'USD/MAD', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDEGP', 'USD/EGP', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('USDVND', 'USD/VND', 'fx', 'XFX', 'واحد ارز پایه', 1, 'unit', 'USD', False, 'جفت\u200cارز بازار نوظهور؛ نقدینگی و اسپرد باید جدا سنجیده شود'),
    ('XPDUSD', 'پالادیوم (اسپات)', 'metals', 'XFX', 'oz', 1, 'oz', 'USD', False, ''),
    ('SI=F', 'نقره (آتی COMEX)', 'metals', 'XCOM', 'oz', 5000, 'oz', 'USD', True, ''),
    ('PL=F', 'پلاتین (آتی)', 'metals', 'XNYM', 'oz', 50, 'oz', 'USD', False, ''),
    ('PA=F', 'پالادیوم (آتی)', 'metals', 'XNYM', 'oz', 100, 'oz', 'USD', False, ''),
    ('HG=F', 'مس (آتی COMEX)', 'metals', 'XCOM', 'lb', 25000, 'lb', 'USD', True, ''),
    ('ALI=F', 'آلومینیوم (آتی)', 'metals', 'XCOM', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_AL', 'آلومینیوم LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_CU', 'مس LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_NI', 'نیکل LME', 'metals', 'XLME', 'tonne', 6, 'tonne', 'USD', False, ''),
    ('LME_ZN', 'روی LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_PB', 'سرب LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_SN', 'قلع LME', 'metals', 'XLME', 'tonne', 5, 'tonne', 'USD', False, ''),
    ('IRON_ORE', 'سنگ آهن (SGX)', 'metals', 'XFX', 'tonne', 100, 'tonne', 'USD', False, 'قرارداد SGX؛ دسترسی داده محدود'),
    ('URANIUM', 'اورانیوم U3O8', 'metals', 'XFX', 'lb', 250, 'lb', 'USD', False, 'بازار غیربورسی؛ شاخص قیمت است نه قرارداد'),
    ('LITHIUM', 'لیتیوم (کربنات)', 'metals', 'XFX', 'tonne', 1, 'tonne', 'USD', False, 'بازار غیربورسی؛ شاخص قیمت'),
    ('ZW=F', 'گندم شیکاگو', 'agri', 'XCBT', 'bushel', 5000, 'bushel', 'USD', True, ''),
    ('KE=F', 'گندم کانزاس', 'agri', 'XCBT', 'bushel', 5000, 'bushel', 'USD', True, ''),
    ('ZS=F', 'سویا', 'agri', 'XCBT', 'bushel', 5000, 'bushel', 'USD', True, ''),
    ('ZM=F', 'کنجاله سویا', 'agri', 'XCBT', 'short ton', 100, 'short ton', 'USD', True, ''),
    ('ZL=F', 'روغن سویا', 'agri', 'XCBT', 'lb', 60000, 'lb', 'USD', True, ''),
    ('ZO=F', 'جو دوسر', 'agri', 'XCBT', 'bushel', 5000, 'bushel', 'USD', False, ''),
    ('ZR=F', 'برنج', 'agri', 'XCBT', 'cwt', 2000, 'cwt', 'USD', False, ''),
    ('KC=F', 'قهوه عربیکا', 'agri', 'XICE', 'lb', 37500, 'lb', 'USD', True, ''),
    ('RC=F', 'قهوه روبوستا', 'agri', 'XICE', 'tonne', 10, 'tonne', 'USD', False, ''),
    ('SB=F', 'شکر', 'agri', 'XICE', 'lb', 112000, 'lb', 'USD', True, ''),
    ('CC=F', 'کاکائو', 'agri', 'XICE', 'tonne', 10, 'tonne', 'USD', True, ''),
    ('CT=F', 'پنبه', 'agri', 'XICE', 'lb', 50000, 'lb', 'USD', True, ''),
    ('OJ=F', 'آب پرتقال', 'agri', 'XICE', 'lb', 15000, 'lb', 'USD', False, ''),
    ('LE=F', 'گاو زنده', 'agri', 'XCME', 'lb', 40000, 'lb', 'USD', False, ''),
    ('HE=F', 'خوک', 'agri', 'XCME', 'lb', 40000, 'lb', 'USD', False, ''),
    ('GF=F', 'گاو پرواری', 'agri', 'XCME', 'lb', 50000, 'lb', 'USD', False, ''),
    ('RS=F', 'کانولا', 'agri', 'XICE', 'tonne', 20, 'tonne', 'USD', False, ''),
    ('LBS=F', 'چوب', 'agri', 'XCME', 'board foot', 27500, 'board foot', 'USD', False, ''),
    ('زیره', 'زیره سبز (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('IVV', 'آی\u200cشیرز اس\u200cاند\u200cپی ۵۰۰', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('VOO', 'ونگارد اس\u200cاند\u200cپی ۵۰۰', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('VTI', 'ونگارد کل بازار', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('QQQ', 'اینوِسکو نزدک ۱۰۰', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('QQQM', 'نزدک ۱۰۰ کم\u200cهزینه', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IWM', 'راسل ۲۰۰۰', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('DIA', 'دیاموندز داو جونز', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('MDY', 'اس\u200cاند\u200cپی میدکپ', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('IJR', 'اس\u200cاند\u200cپی اسمال\u200cکپ', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('VGK', 'اروپا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWJ', 'ژاپن', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWG', 'آلمان', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWQ', 'فرانسه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWU', 'بریتانیا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWC', 'کانادا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWA', 'استرالیا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWZ', 'برزیل', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWW', 'مکزیک', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('INDA', 'هند', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('FXI', 'چین بزرگ', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWT', 'تایوان', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EWY', 'کره', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('TUR', 'ترکیه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('EZA', 'آفریقای جنوبی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('KSA', 'عربستان', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('EGPT', 'مصر', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IEF', 'خزانه ۷-۱۰ ساله', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('SHY', 'خزانه ۱-۳ ساله', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('TIP', 'اوراق تورمی', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('LQD', 'اوراق شرکتی درجه سرمایه\u200cگذاری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('HYG', 'اوراق پرریسک', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('JNK', 'اوراق پرریسک SPDR', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('AGG', 'سبد اوراق کل بازار', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('BNDX', 'اوراق بین\u200cالمللی', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('EMB', 'اوراق بازار نوظهور', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('GOVT', 'خزانه آمریکا کل سررسید', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('MUB', 'اوراق شهرداری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IAU', 'طلا آی\u200cشیرز', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('SLV', 'نقره', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('GDX', 'معادن طلا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('GDXJ', 'معادن طلای کوچک', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('PPLT', 'پلاتین', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('PALL', 'پالادیوم', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('DBA', 'سبد کشاورزی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('USO', 'نفت خام', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('UNG', 'گاز طبیعی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLE', 'انرژی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XOP', 'نفت و گاز اکتشاف', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLU', 'آب و برق', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLF', 'مالی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLK', 'فناوری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLV', 'سلامت', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLI', 'صنعت', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLY', 'مصرف اختیاری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLP', 'مصرف ضروری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLB', 'مواد اولیه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XLRE', 'املاک', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SMH', 'نیمه\u200cهادی', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', True, ''),
    ('XBI', 'زیست\u200cفناوری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('IBB', 'زیست\u200cفناوری آی\u200cشیرز', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ARKK', 'نوآوری آرک', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VNQ', 'املاک آمریکا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('IBIT', 'بیت\u200cکوین بلک\u200cراک', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IGLT', 'اوراق دولتی بریتانیا', 'etf', 'XLON', 'واحد', 1, 'share', 'GBP', False, ''),
    ('VFIAX', 'صندوق ۵۰۰ ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', True, 'صندوق مشاع؛ قیمت پایان روز'),
    ('VTIAX', 'صندوق بین\u200cالمللی ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', True, 'صندوق مشاع؛ قیمت پایان روز'),
    ('VBTLX', 'صندوق اوراق ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', True, 'صندوق مشاع؛ قیمت پایان روز'),
    ('VWELX', 'صندوق متوازن وینزور', 'fund', 'XNYS', 'واحد', 1, 'share', 'USD', False, 'صندوق مشاع؛ قیمت پایان روز'),
    ('FFFEX', 'صندوق آزادی فیدلیتی', 'fund', 'XNYS', 'واحد', 1, 'share', 'USD', False, 'صندوق مشاع؛ قیمت پایان روز'),
    ('صندوق_درآمد_ثابت', 'صندوق درآمد ثابت (فرابورس)', 'fund', 'IFB_IR', 'واحد', 1, 'share', 'IRR', False, 'بازده اسمی اعلامی؛ نقدشوندگی و قیمت\u200cگذاری باید بررسی شود'),
    ('ZT=F', 'آتی خزانه ۲ ساله', 'fixed_income', 'XCBT', 'واحد', 1000, 'unit', 'USD', True, ''),
    ('ZF=F', 'آتی خزانه ۵ ساله', 'fixed_income', 'XCBT', 'واحد', 1000, 'unit', 'USD', True, ''),
    ('ZN=F', 'آتی خزانه ۱۰ ساله', 'fixed_income', 'XCBT', 'واحد', 1000, 'unit', 'USD', True, ''),
    ('ZB=F', 'آتی خزانه ۳۰ ساله', 'fixed_income', 'XCBT', 'واحد', 1000, 'unit', 'USD', True, ''),
    ('UB=F', 'آتی اولترا خزانه', 'fixed_income', 'XCBT', 'واحد', 1000, 'unit', 'USD', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('FBTP', 'آتی باند آلمان Euro-Bund', 'fixed_income', 'XEUREX', 'واحد', 100000, 'unit', 'EUR', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('FBTP_5Y', 'آتی باند ۵ ساله آلمان', 'fixed_income', 'XEUREX', 'واحد', 100000, 'unit', 'EUR', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('JBTP', 'آتی اوراق ۱۰ ساله ژاپن', 'fixed_income', 'XOSE', 'واحد', 100000000, 'unit', 'JPY', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('اخزا', 'اسناد خزانه اسلامی (فرابورس)', 'fixed_income', 'IFB_IR', 'واحد', 1, 'unit', 'IRR', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('صکوک_اجاره', 'صکوک اجاره (فرابورس)', 'fixed_income', 'IFB_IR', 'واحد', 1, 'unit', 'IRR', False, 'مشخصات قرارداد یا سررسید نیازمند تأیید'),
    ('MWE=F', 'گندم بهاره (مینیاپولیس)', 'agri', 'XCME', 'bushel', 5000, 'bushel', 'USD', False, ''),
    ('EBM', 'گندم آسیابانی اروپا (MATIF)', 'agri', 'XMATIF', 'tonne', 50, 'tonne', 'EUR', False, ''),
    ('EMA', 'ذرت اروپا (MATIF)', 'agri', 'XMATIF', 'tonne', 50, 'tonne', 'EUR', False, ''),
    ('ECO', 'کلزای اروپا (MATIF)', 'agri', 'XMATIF', 'tonne', 50, 'tonne', 'EUR', False, ''),
    ('FCPO', 'روغن نخل (BMD)', 'agri', 'XBMD', 'tonne', 25, 'tonne', 'MYR', False, 'قرارداد به رینگیت؛ نیازمند تأیید'),
    ('TFCOM_RSS3', 'لاستیک RSS3 (توکیو)', 'agri', 'XTOCOM', 'kg', 5000, 'kg', 'JPY', False, ''),
    ('SF=F', 'شکر ۱۶ (ICE)', 'agri', 'XICE', 'lb', 112000, 'lb', 'USD', False, ''),
    ('DC=F', 'شیر کلاس ۳ (CME)', 'agri', 'XCME', 'cwt', 200000, 'cwt', 'USD', False, ''),
    ('GDK', 'شیر کلاس ۴ (CME)', 'agri', 'XCME', 'cwt', 200000, 'cwt', 'USD', False, ''),
    ('CB=F', 'کره (CME)', 'agri', 'XCME', 'lb', 20000, 'lb', 'USD', False, ''),
    ('CSC=F', 'پنیر چدار (CME)', 'agri', 'XCME', 'lb', 40000, 'lb', 'USD', False, ''),
    ('GNF=F', 'شیر خشک بدون چربی (CME)', 'agri', 'XCME', 'lb', 44000, 'lb', 'USD', False, ''),
    ('PRK=F', 'پولک خوک منجمد (CME)', 'agri', 'XCME', 'lb', 40000, 'lb', 'USD', False, ''),
    ('BJ=F', 'سوخت زیستی دیزل (CME)', 'agri', 'XCME', 'gallon', 42000, 'gallon', 'USD', False, ''),
    ('PLT', 'سیب\u200cزمینی (ICE)', 'agri', 'XICE', 'lb', 50000, 'lb', 'USD', False, 'نقدینگی بسیار کم'),
    ('پنبه_ایران', 'پنبه (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('جو_ایران', 'جو (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('ذرت_ایران', 'ذرت دامی (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('کنجاله_سویا_ایران', 'کنجاله سویا (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('روغن_خام_نخل', 'روغن خام نخل (بورس کالا)', 'agri', 'IME_IR', 'کیلوگرم', 1, 'کیلوگرم', 'IRR', False, ''),
    ('LME_CO', 'کبالت LME', 'metals', 'XLME', 'tonne', 1, 'tonne', 'USD', False, ''),
    ('LME_MO', 'مولیبدن LME', 'metals', 'XLME', 'tonne', 2, 'tonne', 'USD', False, ''),
    ('LME_AA', 'آلیاژ آلومینیوم LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('LME_NASAAC', 'آلیاژ آلومینیوم ثانویه LME', 'metals', 'XLME', 'tonne', 25, 'tonne', 'USD', False, ''),
    ('SHFE_REBAR', 'میلگرد (SHFE)', 'metals', 'XSHFE', 'tonne', 10, 'tonne', 'CNY', False, ''),
    ('SHFE_HRC', 'ورق گرم (SHFE)', 'metals', 'XSHFE', 'tonne', 10, 'tonne', 'CNY', False, ''),
    ('SHFE_CU', 'مس (SHFE)', 'metals', 'XSHFE', 'tonne', 5, 'tonne', 'CNY', False, ''),
    ('SHFE_AL', 'آلومینیوم (SHFE)', 'metals', 'XSHFE', 'tonne', 5, 'tonne', 'CNY', False, ''),
    ('ALUMINA', 'آلومینا (SHFE)', 'metals', 'XSHFE', 'tonne', 20, 'tonne', 'CNY', False, ''),
    ('ANTIMONY', 'آنتی\u200cموني (SHFE)', 'metals', 'XSHFE', 'tonne', 5, 'tonne', 'CNY', False, ''),
    ('MAGNESIUM', 'منیزیم (غیربورسی)', 'metals', 'XFX', 'tonne', 1, 'tonne', 'USD', False, 'شاخص قیمت، نه قرارداد'),
    ('TITANIUM', 'تیتانیوم (غیربورسی)', 'metals', 'XFX', 'tonne', 1, 'tonne', 'USD', False, 'شاخص قیمت'),
    ('PLATINUM_JPY', 'پلاتین (توکیو)', 'metals', 'XTOCOM', 'gram', 500, 'gram', 'JPY', False, ''),
    ('VEA', 'توسعه\u200cیافته خارج آمریکا (ونگارد)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('VWO', 'بازار نوظهور (ونگارد)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('SCHD', 'سود سهامی آمریکا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', True, ''),
    ('VIG', 'رشد سود سهامی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VYM', 'سود بالا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SOXX', 'نیمه\u200cهادی (آی\u200cشیرز)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('XLC', 'ارتباطات', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ITOT', 'کل بازار آمریکا (آی\u200cشیرز)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ACWI', 'کل جهان (آی\u200cشیرز)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('URTH', 'کل جهان (MSCI)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IEFA', 'توسعه\u200cیافته (آی\u200cشیرز)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IEMG', 'بازار نوظهور (آی\u200cشیرز)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('TLH', 'خزانه ۱۰-۲۰ ساله', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('BIL', 'اسناد خزانه یک\u200cماهه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SHV', 'اسناد خزانه کوتاه\u200cمدت', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IGSB', 'اوراق شرکتی کوتاه\u200cمدت', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VCIT', 'اوراق شرکتی میان\u200cمدت (ونگارد)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VCSH', 'اوراق شرکتی کوتاه (ونگارد)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('HYLB', 'اوراق پرریسک کم\u200cهزینه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IBND', 'اوراق بین\u200cالمللی (SPDR)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IAU_GLD', 'طلا (آی\u200cشیرز)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SGOL', 'طلا (ابردین)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SIVR', 'نقره (ابردین)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('CPER', 'مس', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('PICK', 'فلزات و معدن', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('REMX', 'فلزات نادر خاکی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('LIT', 'لیتیوم و باتری', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('URA', 'اورانیوم', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('MOO', 'کشاورزی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('WEAT', 'گندم', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('CORN', 'ذرت', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('SOYB', 'سویا', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('CANE', 'شکر', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('JO', 'قهوه', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('NIB', 'کاکائو', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('COW', 'دام', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('WOOD', 'چوب و جنگل', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VNQI', 'املاک بین\u200cالمللی', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IYR', 'املاک آمریکا (آی\u200cشیرز)', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('IBB_Q', 'زیست\u200cفناوری (آی\u200cشیرز)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ICLN', 'انرژی پاک', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('TAN', 'انرژی خورشیدی', 'etf', 'XNYS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ESGU', 'سرمایه\u200cگذاری مسئولانه', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('ESGV', 'مسئولانه (ونگارد)', 'etf', 'XNAS', 'واحد', 1, 'share', 'USD', False, ''),
    ('VIMAX', 'صندوق میدکپ ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('VSMAX', 'صندوق اسمال\u200cکپ ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('VFWAX', 'صندوق کل جهان به\u200cجز آمریکا', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('VFSUX', 'صندوق اوراق کوتاه\u200cمدت ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('VBILX', 'صندوق اوراق میان\u200cمدت ونگارد', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('VFIAX_2', 'صندوق شاخص ۵۰۰ (کلاس ادمیرال)', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('SWTSX', 'صندوق کل بازار چارلز شواب', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('SWISX', 'صندوق بین\u200cالمللی شواب', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('FXAIX', 'صندوق ۵۰۰ فیدلیتی', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('FSPSX', 'صندوق بین\u200cالمللی فیدلیتی', 'fund', 'XNAS', 'واحد', 1, 'share', 'USD', False, 'مشخصات صندوق نیازمند بررسی'),
    ('صندوق_شاخصی_تهران', 'صندوق شاخصی بورس تهران', 'fund', 'IFB_IR', 'واحد', 1, 'share', 'IRR', False, 'مشخصات صندوق نیازمند بررسی'),
    ('صندوق_کالایی_طلا', 'صندوق کالایی مبتنی بر طلا', 'fund', 'IFB_IR', 'واحد', 1, 'share', 'IRR', False, 'مشخصات صندوق نیازمند بررسی'),
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
