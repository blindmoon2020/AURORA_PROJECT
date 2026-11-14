"""Build the AURORA page from today's session files."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aurora.web.static_site import build_site  # noqa: E402


def main() -> int:
    built = build_site(".", "site/index.html")
    print(f"صفحه ساخته شد: {built.path}")
    if built.missing:
        print("فایل‌های غایب: " + "، ".join(built.missing))
    print(built.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
