#!/usr/bin/env python3
"""Draw evidence/speedup.svg: client time / join time per base, for three settings.

Bars are the mean of per-field ratios over the 5 production 1e14 fields per base;
whiskers are the min-max over those fields. Data sources:
  CPU, 1 thread   evidence/cpu_bench_pair.jsonl (time_ratio per field)
  CPU, 10 threads gpu/results/cpu_context.jsonl (via the GPU report's table)
  GPU, Apple M4   gpu/README.md section 4.2 (whole-field client vs join, host tops)
"""
import json
import statistics as st
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASES = [57, 60, 64]

cpu1 = {}
rows = [json.loads(line) for line in open(HERE / "cpu_bench_pair.jsonl")]
for b in BASES:
    r = [x["time_ratio"] for x in rows if x["base"] == b]
    cpu1[b] = (st.mean(r), min(r), max(r))
# From the GPU report (gpu/README.md, sections 4.3 and 4.5).
cpu10 = {57: (7.3, 6.3, 8.1), 60: (4.9, 2.8, 5.7), 64: (2.9, 2.2, 3.4)}
gpu = {57: (27.2, 25.6, 29.6), 60: (9.8, 6.2, 13.0), 64: (17.4, 14.2, 21.9)}
SERIES = [("CPU, 1 thread", cpu1, "s1"), ("CPU, 10 threads", cpu10, "s2"), ("GPU (Apple M4)", gpu, "s3")]

W, H = 720, 400
L, R, T, B = 64, 24, 92, 56          # plot margins
PW, PH = W - L - R, H - T - B
YMAX = 35
BAR, GAP = 24, 2                     # bar width (<= 24px) and surface gap between adjacent bars


def y(v):
    return T + PH * (1 - v / YMAX)


def bar_path(x, v):
    """Column with a 4px rounded data end and a square baseline."""
    top, base, r = y(v), y(0), 4
    return (f"M{x:.1f},{base:.1f} V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} "
            f"H{x + BAR - r:.1f} Q{x + BAR:.1f},{top:.1f} {x + BAR:.1f},{top + r:.1f} V{base:.1f} Z")


out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           'role="img" aria-labelledby="t d" font-family="system-ui, -apple-system, Segoe UI, sans-serif">')
desc = "; ".join(
    f"base {b}: " + ", ".join(f"{name} {s[b][0]:.1f}x (range {s[b][1]:.1f}-{s[b][2]:.1f})" for name, s, _ in SERIES)
    for b in BASES)
out.append('<title id="t">Speedup of the overlap join over the public client</title>')
out.append(f'<desc id="d">Client time divided by join time on the same production fields. {desc}.</desc>')
out.append("""<style>
  .bg{fill:#fcfcfb} .ink{fill:#0b0b0b} .ink2{fill:#52514e} .muted{fill:#898781}
  .grid{stroke:#e1e0d9} .axis{stroke:#c3c2b7} .whisk{stroke:#52514e}
  .s1{fill:#2a78d6} .s2{fill:#eb6834} .s3{fill:#1baf7a}
  @media (prefers-color-scheme: dark){
    .bg{fill:#1a1a19} .ink{fill:#ffffff} .ink2{fill:#c3c2b7}
    .grid{stroke:#2c2c2a} .axis{stroke:#383835} .whisk{stroke:#c3c2b7}
    .s1{fill:#3987e5} .s2{fill:#d95926} .s3{fill:#199e70}
  }
</style>""")
out.append(f'<rect class="bg" width="{W}" height="{H}" rx="8"/>')
out.append(f'<text class="ink" x="{L}" y="30" font-size="16" font-weight="600">How much faster the overlap join is than the client</text>')
out.append(f'<text class="ink2" x="{L}" y="50" font-size="12">Client time ÷ join time on the same 1e14 production fields. '
           'Bar: mean over 5 fields; whisker: range.</text>')
# legend
lx = L
for name, _, cls in SERIES:
    out.append(f'<rect class="{cls}" x="{lx}" y="64" width="12" height="12" rx="2"/>')
    out.append(f'<text class="ink2" x="{lx + 18}" y="74" font-size="12">{name}</text>')
    lx += 18 + 7.2 * len(name) + 24
# gridlines and y ticks
for v in range(0, YMAX + 1, 5):
    cls = "axis" if v == 0 else "grid"
    out.append(f'<line class="{cls}" x1="{L}" x2="{L + PW}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke-width="1"/>')
    out.append(f'<text class="muted" x="{L - 8}" y="{y(v) + 4:.1f}" font-size="11" text-anchor="end" '
               f'style="font-variant-numeric:tabular-nums">{v}×</text>')
# groups
gw = PW / len(BASES)
for i, b in enumerate(BASES):
    cx = L + gw * (i + 0.5)
    total = len(SERIES) * BAR + (len(SERIES) - 1) * GAP
    x0 = cx - total / 2
    for j, (name, s, cls) in enumerate(SERIES):
        mean, lo, hi = s[b]
        x = x0 + j * (BAR + GAP)
        out.append(f'<path class="{cls}" d="{bar_path(x, mean)}"><title>{name}, base {b}: {mean:.1f}× (range {lo:.1f}–{hi:.1f}×)</title></path>')
        mx = x + BAR / 2
        out.append(f'<line class="whisk" x1="{mx:.1f}" x2="{mx:.1f}" y1="{y(hi):.1f}" y2="{y(lo):.1f}" stroke-width="1.5"/>')
        for v in (lo, hi):
            out.append(f'<line class="whisk" x1="{mx - 4:.1f}" x2="{mx + 4:.1f}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke-width="1.5"/>')
        # direct label: value above the whisker
        out.append(f'<text class="ink" x="{mx:.1f}" y="{y(hi) - 6:.1f}" font-size="11" text-anchor="middle" '
                   f'style="font-variant-numeric:tabular-nums">{mean:.1f}×</text>')
    out.append(f'<text class="ink2" x="{cx:.1f}" y="{T + PH + 22:.1f}" font-size="12" text-anchor="middle">Base {b}</text>')
out.append(f'<text class="muted" x="{L}" y="{H - 10}" font-size="11">One Apple M4 laptop. GPU: whole-field client run vs. join (mean of 3 rounds). '
           'NVIDIA untested.</text>')
out.append("</svg>")
(HERE / "speedup.svg").write_text("\n".join(out) + "\n")
print("wrote", HERE / "speedup.svg")
for name, s, _ in SERIES:
    print(name, {b: tuple(round(v, 1) for v in s[b]) for b in BASES})
