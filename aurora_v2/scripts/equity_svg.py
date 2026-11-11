#!/usr/bin/env python3
"""Draw an equity curve and its drawdown as a dependency-free SVG.

    python scripts/equity_svg.py results/X_oos_equity.csv out.svg "title"
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


def read_curve(path: Path) -> list[float]:
    with path.open(encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        return [float(row["equity"]) for row in r]


def svg(curve: list[float], title: str, width: int = 880, height: int = 320) -> str:
    if len(curve) < 2:
        raise ValueError("curve needs at least two points")
    pad_l, pad_r, pad_t, pad_b = 64, 16, 34, 42
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    lo, hi = min(curve), max(curve)
    span = (hi - lo) or 1.0
    peak, dd = curve[0], []
    for v in curve:
        peak = max(peak, v)
        dd.append((peak - v) / peak * 100 if peak else 0.0)
    dd_max = max(dd) or 1.0

    def x(i): return pad_l + i / (len(curve) - 1) * w
    def y(v): return pad_t + h - (v - lo) / span * h
    def yd(v): return pad_t + v / dd_max * h * 0.28

    line = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(curve))
    area = f"{pad_l},{pad_t + h} " + line + f" {pad_l + w},{pad_t + h}"
    dd_line = " ".join(f"{x(i):.1f},{yd(v):.1f}" for i, v in enumerate(dd))
    zero_pct = (curve[0] * 0 - 0)
    ret = (curve[-1] / curve[0] - 1) * 100

    ticks = 5
    grid = []
    for k in range(ticks + 1):
        v = lo + span * k / ticks
        yy = y(v)
        grid.append(
            f'<line x1="{pad_l}" y1="{yy:.1f}" x2="{pad_l + w}" y2="{yy:.1f}" '
            f'stroke="#e8e8ea" stroke-width="1"/>'
            f'<text x="{pad_l - 8}" y="{yy + 4:.1f}" text-anchor="end" '
            f'font-size="11" fill="#6b6b72">{v:,.0f}</text>'
        )
    color = "#1f7a4d" if ret >= 0 else "#a33a3a"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif">
  <rect width="{width}" height="{height}" fill="#fbfbfc"/>
  <text x="{pad_l}" y="20" font-size="13" font-weight="600" fill="#1c1c20">{title}</text>
  {''.join(grid)}
  <polygon points="{area}" fill="{color}" opacity="0.10"/>
  <polyline points="{line}" fill="none" stroke="{color}" stroke-width="2"/>
  <polyline points="{dd_line}" fill="none" stroke="#8a8a92" stroke-width="1" stroke-dasharray="3 3" opacity="0.9"/>
  <text x="{pad_l + w}" y="{pad_t + h + 26}" text-anchor="end" font-size="11" fill="#6b6b72">bars {len(curve)}  |  total {ret:+.2f}%  |  max drawdown {max(dd):.2f}% (dashed)</text>
</svg>'''


def main(argv):
    src, dest, title = Path(argv[0]), Path(argv[1]), argv[2] if len(argv) > 2 else "equity"
    dest.write_text(svg(read_curve(src), title), encoding="utf-8")
    print(f"wrote {dest}")


if __name__ == "__main__":
    main(sys.argv[1:])
