"""Print the access paths, and write docs/ACCESS_LINKS.md from the same source."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aurora.core import access_registry as ar  # noqa: E402


def main() -> int:
    problems = ar.audit()
    if problems:
        print("ایراد ساختاری: " + "؛ ".join(problems))
        return 1
    print(ar.summary_line())
    for kind in sorted(ar.counts()):
        print(f"\n## {kind}")
        for path in ar.by_kind(kind):
            print("  " + path.line())
    target = Path("docs/ACCESS_LINKS.md")
    target.parent.mkdir(exist_ok=True)
    target.write_text(ar.markdown(), encoding="utf-8")
    print(f"\nسند نوشته شد: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
