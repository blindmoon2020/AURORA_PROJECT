"""A written contract for the core, so "do not damage it" is enforced by code.

The instruction "protect the core" fails in a specific way: not by a dramatic deletion,
but by a quiet one. A refactor removes `trend_brake`, the module still imports, one path
silently stops braking, and nobody notices for weeks. That is what happened in this very
project, when a new module was written over aurora/portfolio/overlay.py.

So the core is defined by its PUBLIC SURFACE - module, callable, argument names - and that
surface is written to a file that is committed. Verification fails if a name disappears or
its arguments change. Additions are allowed: a peripheral part may be attached at will,
which is exactly the requirement, while removal has to be a deliberate act that updates
the contract in the same commit and shows up in review.
"""
import importlib
import inspect
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "docs" / "core_contract.json"

# the modules whose behaviour the rest of the system is allowed to trust
CORE_MODULES: Tuple[str, ...] = (
    "aurora.core.types",
    "aurora.core.asset_universe",
    "aurora.core.market_registry",
    "aurora.execution.paper_book",
    "aurora.execution.manual_bridge",
    "aurora.execution.fill_capture",
    "aurora.execution.reconcile",
    "aurora.execution.impact",
    "aurora.portfolio.guard",
    "aurora.portfolio.overlay",
    "aurora.portfolio.brakes",
    "aurora.portfolio.scenarios",
    "aurora.portfolio.risk_budget",
    "aurora.portfolio.turnover",
    "aurora.strategies.cross_asset",
    "aurora.privacy",
    "aurora.security",
    "aurora.calibration",
)


def _signature(obj) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(?)"


def snapshot(modules: Optional[Tuple[str, ...]] = None) -> Dict[str, Dict[str, str]]:
    """The public callables of every core module, with their argument lists."""
    out: Dict[str, Dict[str, str]] = {}
    for name in (modules or CORE_MODULES):
        module = importlib.import_module(name)
        surface: Dict[str, str] = {}
        for attr in dir(module):
            if attr.startswith("_"):
                continue
            obj = getattr(module, attr)
            if inspect.isfunction(obj) and getattr(obj, "__module__", "") == module.__name__:
                surface[attr] = _signature(obj)
            elif inspect.isclass(obj) and getattr(obj, "__module__", "") == module.__name__:
                surface[attr] = "class"
        out[name] = surface
    return out


def verify(current: Dict[str, Dict[str, str]],
           contract: Dict[str, Dict[str, str]]) -> Tuple[List[str], List[str]]:
    """Return (missing, changed). Additions are deliberately not a failure."""
    missing: List[str] = []
    changed: List[str] = []
    for module, names in contract.items():
        if module not in current:
            missing.append(f"{module} (whole module)")
            continue
        for name, sig in names.items():
            if name not in current[module]:
                missing.append(f"{module}.{name}")
            elif sig != "class" and current[module][name] != sig:
                changed.append(f"{module}.{name}: {sig} -> {current[module][name]}")
    return missing, changed


def load(path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    file = path or CONTRACT_PATH
    return json.loads(file.read_text(encoding="utf-8"))


def write(path: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """Regenerate the contract. A deliberate act, made in the same commit as the change."""
    file = path or CONTRACT_PATH
    snap = snapshot()
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(snap, indent=1, ensure_ascii=False, sort_keys=True),
                    encoding="utf-8")
    return snap


def check(path: Optional[Path] = None) -> Tuple[bool, str]:
    file = path or CONTRACT_PATH
    if not file.exists():
        return False, "core contract missing: run core_contract.write() and commit it"
    missing, changed = verify(snapshot(), load(file))
    if missing or changed:
        parts = []
        if missing:
            parts.append("حذف‌شده: " + "، ".join(missing))
        if changed:
            parts.append("امضای تغییرکرده: " + "، ".join(changed))
        return False, "؛ ".join(parts)
    return True, f"قرارداد هسته سالم: {sum(len(v) for v in load(file).values())} عضو محافظت‌شده"


if __name__ == "__main__":
    import sys
    if "--write" in sys.argv:
        write()
        print("core contract written")
        raise SystemExit(0)
    ok, message = check()
    print(("OK  " if ok else "FAIL") + " " + message)
    raise SystemExit(0 if ok else 1)
