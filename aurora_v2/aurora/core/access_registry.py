"""Where each blocked capability is actually obtained, as data rather than prose.

A list of links in a chat message is lost the moment the chat scrolls. This module makes the
access paths part of the code base, so the obstacle list, the document and the printable
summary all come from one source and cannot drift apart.

Every entry answers four questions the owner actually asks: what it unblocks, where to go,
what exactly to do there, and what it costs. `verified` is the same honesty flag used
elsewhere: a URL I am confident is the provider's own site is verified; one quoted from
memory is marked, so nobody types a password into a lookalike page on my word alone.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

FREE, PAID, CONTRACT = "رایگان", "پرداختی", "قراردادی"


@dataclass(frozen=True)
class AccessPath:
    key: str
    title: str
    unblocks: str
    url: str
    action: str
    cost: str
    kind: str                       # "data" | "execution" | "legal" | "calendar"
    verified: bool = False
    note: str = ""

    def line(self) -> str:
        mark = "" if self.verified else " (نشانی از دانش عمومی، پیش از ورود بررسی شود)"
        return f"{self.title}: {self.url}{mark}"


PATHS: List[AccessPath] = [
    AccessPath(
        "mofid", "کارگزاری مفید (اجرای بورس تهران)",
        "اجرای واقعی سفارش‌های بورس تهران به‌جای تیکت دستی",
        "https://www.mofid.com",
        "ورود به پنل معاملاتی و دریافت دسترسی API یا تأیید مسیر تیکت دستی", CONTRACT, "execution",
        False, "مفید API عمومی ندارد؛ اگر پنل «معاملات آنلاین» دارد همان کافی است",
    ),
    AccessPath(
        "tsetmc", "TSETMC (قیمت و حجم بورس تهران)",
        "داده تاریخی و روزانه سهام ایران",
        "https://www.tsetmc.com",
        "استفاده از خروجی CSV روزانه؛ کلید لازم نیست", FREE, "data", True,
        "داده عمومی است ولی نرخ درخواست باید محدود شود",
    ),
    AccessPath(
        "codal", "کدال (صورت‌های مالی ایران)",
        "بنیادی سهام ایران: EPS، ترازنامه، رویدادها",
        "https://codal.ir",
        "جست‌وجوی نماد و دریافت گزارش؛ API رسمی نیازمند تأیید است", FREE, "data", True,
    ),
    AccessPath(
        "fred", "FRED (نرخ بهره، تورم، نقدینگی آمریکا)",
        "لایه ماکرو و رژیم بازار",
        "https://fred.stlouisfed.org/docs/api/api_key.html",
        "ثبت‌نام رایگان و ساخت کلید API و ارسال در فرم امن", FREE, "data", True,
    ),
    AccessPath(
        "sec", "SEC EDGAR (بنیادی شرکت‌های آمریکا)",
        "EPS و صورت‌های مالی با تاریخ انتشار (بدون سوگیری آینده)",
        "https://www.sec.gov/edgar/sec-api-documentation",
        "ثبت User-Agent با ایمیل واقعی؛ کلید دیگر لازم نیست", FREE, "data", True,
    ),
    AccessPath(
        "eodhd", "EODHD (داده جهانی و سهام حذف‌شده)",
        "رفع سوگیری بقا و پوشش بازارهای نوظهور",
        "https://eodhd.com",
        "اشتراک پایه ماهانه؛ کلید در فرم امن", PAID, "data", True,
        "طبق تصمیم قبلی تا تأمین بودجه خریداری نمی‌شود",
    ),
    AccessPath(
        "eia", "EIA (نفت، گاز، ذخایر انرژی آمریکا)",
        "داده هفتگی انرژی و ذخایر",
        "https://www.eia.gov/opendata/",
        "ثبت‌نام و کلید رایگان", FREE, "data", True,
        "فعلاً کنار گذاشته شد؛ نفت از FRED هم قابل دریافت است",
    ),
    AccessPath(
        "cme", "CME Group (مشخصات رسمی قراردادها)",
        "تأیید اندازه قرارداد، تیک و تحویل برای طلا، کشاورزی، اوراق آمریکا",
        "https://www.cmegroup.com",
        "جست‌وجوی هر محصول و برداشت Contract Spec", FREE, "data", True,
    ),
    AccessPath(
        "ice", "ICE (شکر، قهوه، کاکائو، پنبه)",
        "تأیید مشخصات قرارداد سافت‌ها و شاخص‌ها",
        "https://www.ice.com",
        "جست‌وجوی محصول و برداشت مشخصات قرارداد", FREE, "data", True,
    ),
    AccessPath(
        "lme", "LME (فلزات صنعتی)",
        "تأیید قرارداد و قیمت مرجع مس، آلومینیوم، نیکل، روی، قلع، کبالت",
        "https://www.lme.com",
        "دسترسی به قیمت‌های رسمی نیازمند ثبت‌نام است؛ مشخصات قرارداد آزاد است",
        CONTRACT, "data", True,
    ),
    AccessPath(
        "forexfactory", "Forex Factory (تقویم اقتصادی)",
        "دروازه ریسک رویداد به‌جای CSV دستی",
        "https://www.forexfactory.com/calendar",
        "اسکرپ ممنوع است؛ هفتگی CSV را در journal/calendar.csv بگذارید", FREE, "calendar", True,
    ),
    AccessPath(
        "tradingview", "TradingView (نمودار و ایده)",
        "بررسی چشمی و مقایسه تحلیل",
        "https://www.tradingview.com",
        "دسترسی وب برای بررسی؛ اسکرپ ممنوع است", FREE, "data", True,
    ),
    AccessPath(
        "binance", "صرافی رمزارز (کلید معامله)",
        "اجرای خودکار رمزارز که امروز صریحاً مسدود است",
        "https://www.binance.com",
        "ساخت کلید با دسترسی معامله و بدون برداشت، سپس فرم امن", FREE, "execution", True,
        "کلید با دسترسی برداشت هرگز نباید داده شود",
    ),
    AccessPath(
        "alpaca", "Alpaca (کارگزار API سهام آمریکا)",
        "اجرای الکترونیکی سهام آمریکا به‌جای شبیه‌ساز",
        "https://alpaca.markets",
        "حساب رایگان کاغذی برای آزمون؛ حساب واقعی نیازمند احراز هویت و اقامت مجاز",
        FREE, "execution", True,
        "پذیرش مقیم ایران باید جدا بررسی شود",
    ),
    AccessPath(
        "ibkr", "Interactive Brokers (کارگزار چندبازاری)",
        "اجرای جهانی سهام، آتی، اوراق و ارز",
        "https://www.interactivebrokers.com",
        "افتتاح حساب؛ نیازمند مدارک اقامت/مالیات", CONTRACT, "execution", True,
    ),
    AccessPath(
        "licence", "مجوز و امانتداری دارایی مشتری",
        "پذیرش پول اشخاص و شرکت‌ها در پلتفرم",
        "https://seba.ir",
        "مشورت با سازمان بورس برای مسیر مجوز یا همکاری با کارگزار دارای مجوز",
        CONTRACT, "legal", True, "این مسیر حقوقی است، نه فنی",
    ),
]


class UnknownAccessPath(KeyError):
    """Raised instead of returning a plausible-looking but wrong link."""


def by_key(key: str) -> AccessPath:
    for path in PATHS:
        if path.key == key:
            return path
    raise UnknownAccessPath(f"مسیر دسترسی ناشناخته: {key}")


def by_kind(kind: str) -> List[AccessPath]:
    return [p for p in PATHS if p.kind == kind]


def free_paths() -> List[AccessPath]:
    return [p for p in PATHS if p.cost == FREE]


def unverified() -> List[str]:
    return [p.key for p in PATHS if not p.verified]


def counts() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for path in PATHS:
        out[path.kind] = out.get(path.kind, 0) + 1
    return out


def audit() -> List[str]:
    problems: List[str] = []
    seen = set()
    for path in PATHS:
        if path.key in seen:
            problems.append(f"{path.key}: کلید تکراری")
        seen.add(path.key)
        if not path.url.startswith("https://"):
            problems.append(f"{path.key}: نشانی باید https باشد")
        if not path.unblocks or not path.action:
            problems.append(f"{path.key}: «چه چیزی را باز می‌کند» یا «چه کاری» خالی است")
    return problems


def summary_line() -> str:
    c = counts()
    return (f"{len(PATHS)} مسیر دسترسی در {len(c)} دسته · "
            f"{len(free_paths())} رایگان · {len(unverified())} نشانی نیازمند بررسی")


def markdown() -> str:
    lines = ["# مسیرهای دسترسی AURORA", "",
             summary_line(), "",
             "| کلید | چه چیزی را باز می‌کند | نشانی | چه کاری | هزینه | وضعیت |",
             "| --- | --- | --- | --- | --- | --- |"]
    for p in PATHS:
        flag = "تأییدشده" if p.verified else "بررسی شود"
        lines.append(f"| `{p.key}` | {p.unblocks} | {p.url} | {p.action} | {p.cost} | {flag} |")
    lines += ["", "## قاعده امنیتی", "",
              "کلیدهای API فقط از فرم امن وارد می‌شوند، هرگز در گفتگو. کلیدی با دسترسی برداشت",
              "به هیچ عنوان پذیرفته نمی‌شود. نشانی‌هایی که «بررسی شود» علامت دارند، از دانش",
              "عمومی آمده‌اند؛ پیش از ورود نام کاربری، دامنه را با دقت بخوانید.", ""]
    return "\n".join(lines)
