"""One command: the state of every data source, in a table you can read in ten seconds."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aurora.health import source_rows, verdict

CACHE = Path("data_cache")


def main() -> int:
    rows = source_rows(CACHE)
    usable, degraded, blocked = verdict(rows)
    width = max(len(r["source"]) for r in rows)
    print(f"{'source'.ljust(width)}  {'credential':10s}  {'status':14s}  note")
    print("-" * (width + 50))
    for r in rows:
        cred = "keyless" if r["credential"] is None else ("yes" if r["credential"] else "MISSING")
        print(f"{r['source'].ljust(width)}  {cred:10s}  {r['status']:14s}  {r['note']}")
    print(f"\nusable {usable} · stale {degraded} · blocked {len(blocked)}"
          + (f" ({', '.join(blocked)})" if blocked else ""))
    return 0 if usable else 1


if __name__ == "__main__":
    raise SystemExit(main())
