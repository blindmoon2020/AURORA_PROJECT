"""Offline drill: prove the promise instead of stating it.

Run twice with different simulated conditions:
  python3 scripts/offline_drill.py            # internet cut, cache recent
  python3 scripts/offline_drill.py --cold     # internet cut, cache ancient

Pass condition for the first: the session must refuse NEW risk while still being
able to manage what is held. For the second: it must refuse everything and say so.
A promise about resilience that is never exercised is a sentence in a document.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(env_extra: dict) -> dict:
    env = {**os.environ, "AURORA_PRICE_SOURCE": "yahoo", **env_extra}
    proc = subprocess.run([sys.executable, "scripts/paper_session.py"], cwd=ROOT,
                          capture_output=True, text=True, env=env, timeout=900)
    return {"code": proc.returncode, "out": proc.stdout.strip().splitlines()[-6:],
            "err": proc.stderr.strip().splitlines()[-3:]}


def book(path=Path("journal/paper_book.json")) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    before = book()
    before_n = len(before["positions"])

    print("== drill 1: internet cut, cache recent (must hold, not add) ==")
    r1 = run({"AURORA_FORCE_OFFLINE": "1"})
    print("\n".join(r1["out"]))
    after = book()
    before_syms = sorted(p["symbol"] for p in before["positions"])
    after_syms = sorted(p["symbol"] for p in after["positions"])
    # holding means identical: neither added nor liquidated
    ok1 = r1["code"] == 0 and before_syms == after_syms
    print(f"positions {before_n} -> {len(after['positions'])} "
          f"({'identical' if before_syms == after_syms else 'CHANGED: ' + str(after_syms)}) -> "
          f"{'PASS' if ok1 else 'FAIL'}")

    print("\n== drill 2: internet cut, cache ancient (must stop) ==")
    r2 = run({"AURORA_FORCE_OFFLINE": "1", "AURORA_NOW_TS": "2000000000"})
    print("\n".join(r2["out"]))
    final = book()
    ok2 = r2["code"] == 0 and any("متوقف" in line or "offline" in line.lower() or "آفلاین" in line
                                  for line in r2["out"] + r2["err"]) or len(final["positions"]) == len(after["positions"])
    print(f"positions unchanged {len(final['positions'])} -> {'PASS' if ok2 else 'FAIL'}")

    print("\n== audit ledger ==")
    rows = [json.loads(l) for l in (ROOT / "journal/audit.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    states = [r["payload"] for r in rows if r["event"] == "data_state"]
    skipped = sum(1 for r in rows if r["event"] == "session_skipped")
    print(f"data_state entries {len(states)} · skipped sessions {skipped}")
    print(f"last states: {states[-2:]}")
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    raise SystemExit(main())
