#!/usr/bin/env python3
"""Check whether a supporting KPI still moves with EBITDA, at daily, weekly and monthly grain.

Standard library only. You define each KPI from summable columns (MER = revenue / ad_spend),
so ratios are rebuilt from totals at every grain instead of averaging daily ratios.
It reports the correlation at each grain, for the whole history and for its earlier and
later halves. It sets no cutoff for "tracking": the answer often differs by grain, and
monthly is usually the most valuable read.

By Eric Brinker, Brinker Analytics (https://brinkeranalytics.com). MIT license.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import os
import sys
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Tuple

GRAINS = ("daily", "weekly", "monthly")


def grain_key(d: dt.date, grain: str) -> str:
    if grain == "daily":
        return d.isoformat()
    if grain == "weekly":
        return (d - dt.timedelta(days=d.weekday())).isoformat()
    if grain == "monthly":
        return f"{d.year:04d}-{d.month:02d}"
    raise ValueError(grain)


def parse_kpi(spec: str) -> Tuple[str, str, Optional[str]]:
    """'MER=revenue/ad_spend' -> ('MER', 'revenue', 'ad_spend'); 'cm=contribution_margin' -> summed column."""
    if "=" not in spec:
        return spec, spec, None
    name, expr = spec.split("=", 1)
    if "/" in expr:
        num, den = expr.split("/", 1)
        return name.strip(), num.strip(), den.strip()
    return name.strip(), expr.strip(), None


def load(path: str) -> Tuple[List[dt.date], Dict[str, List[float]]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if "date" not in (r.fieldnames or []):
            sys.exit(f"{path}: needs a 'date' column")
        cols = [c for c in r.fieldnames if c != "date"]
        dates, data = [], {c: [] for c in cols}
        seen = set()
        for row in r:
            d = dt.date.fromisoformat(row["date"].strip()[:10])
            if d in seen:
                sys.exit(f"{path}: {d} appears twice")
            seen.add(d)
            dates.append(d)
            for c in cols:
                v = (row[c] or "").strip()
                data[c].append(float(v) if v else math.nan)
    order = sorted(range(len(dates)), key=lambda i: dates[i])
    return [dates[i] for i in order], {c: [v[i] for i in order] for c, v in data.items()}


def input_grain(dates: List[dt.date]) -> str:
    if len(dates) < 2:
        return "monthly"
    gaps = sorted((b - a).days for a, b in zip(dates, dates[1:]))
    g = gaps[len(gaps) // 2]
    return "daily" if g <= 1 else "weekly" if g <= 7 else "monthly"


def aggregate(dates, data, grain, columns) -> "OrderedDict[str, Dict[str, float]]":
    """Sum each column into grain buckets. A bucket with any missing value in a column is dropped for it."""
    out: "OrderedDict[str, Dict[str, float]]" = OrderedDict()
    bad: Dict[str, set] = defaultdict(set)
    for i, d in enumerate(dates):
        k = grain_key(d, grain)
        b = out.setdefault(k, {c: 0.0 for c in columns})
        for c in columns:
            v = data[c][i]
            if math.isnan(v):
                bad[k].add(c)
            else:
                b[c] += v
    for k, cs in bad.items():
        for c in cs:
            out[k][c] = math.nan
    return out


def kpi_series(buckets, name, num, den) -> List[float]:
    vals = []
    for b in buckets.values():
        n = b[num]
        if den is None:
            vals.append(n)
        else:
            dv = b[den]
            vals.append(n / dv if dv and not math.isnan(dv) and not math.isnan(n) else math.nan)
    return vals


def pearson(x: List[float], y: List[float]) -> Tuple[Optional[float], int]:
    pairs = [(a, b) for a, b in zip(x, y) if not (math.isnan(a) or math.isnan(b))]
    n = len(pairs)
    if n < 3:
        return None, n
    mx = sum(a for a, _ in pairs) / n
    my = sum(b for _, b in pairs) / n
    sxy = sum((a - mx) * (b - my) for a, b in pairs)
    sxx = sum((a - mx) ** 2 for a, _ in pairs)
    syy = sum((b - my) ** 2 for _, b in pairs)
    if sxx == 0 or syy == 0:
        return None, n
    return sxy / math.sqrt(sxx * syy), n


def check(dates, data, goal: str, kpis: List[str], drop_partial: bool = True) -> List[dict]:
    first = GRAINS.index(input_grain(dates))
    rows = []
    for spec in kpis:
        name, num, den = parse_kpi(spec)
        cols = [goal, num] + ([den] if den else [])
        for c in cols:
            if c not in data:
                sys.exit(f"column {c!r} not found (have {sorted(data)})")
        for grain in GRAINS[first:]:
            buckets = aggregate(dates, data, grain, cols)
            if drop_partial and grain != GRAINS[first] and len(buckets) > 2:
                keys = list(buckets)
                for k in (keys[0], keys[-1]):  # first and last buckets may be partial
                    if _is_partial(dates, k, grain):
                        del buckets[k]
            x = kpi_series(buckets, name, num, den)
            y = [b[goal] for b in buckets.values()]
            r_all, n_all = pearson(x, y)
            h = len(x) // 2
            r_early, n_early = pearson(x[:h], y[:h])
            r_late, n_late = pearson(x[h:], y[h:])
            keys = list(buckets)
            rows.append({
                "kpi": name, "goal": goal, "grain": grain,
                "points": n_all, "correlation": r_all,
                "earlier_half": f"{keys[0]} to {keys[h - 1]}" if h else "",
                "earlier_points": n_early, "earlier_correlation": r_early,
                "later_half": f"{keys[h]} to {keys[-1]}" if keys else "",
                "later_points": n_late, "later_correlation": r_late,
            })
    return rows


def _is_partial(dates, key, grain) -> bool:
    days = [d for d in dates if grain_key(d, grain) == key]
    if grain == "weekly":
        return len(days) < 7
    if grain == "monthly":
        d0 = days[0]
        nxt = dt.date(d0.year + (d0.month == 12), d0.month % 12 + 1, 1)
        return len(days) < (nxt - dt.date(d0.year, d0.month, 1)).days
    return False


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.3f}"
    return "n/a" if v is None else v


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", required=True, help="CSV with a date column and summable value columns")
    ap.add_argument("--goal", default="ebitda", help="the final goal column (default: ebitda)")
    ap.add_argument("--kpi", action="append", required=True,
                    help="a KPI to check, e.g. 'MER=revenue/ad_spend' or 'contribution_margin'. Repeatable.")
    ap.add_argument("--keep-partial", action="store_true", help="keep partial first and last weeks or months")
    ap.add_argument("--out", default="output")
    a = ap.parse_args(argv)
    dates, data = load(a.data)
    rows = check(dates, data, a.goal, a.kpi, drop_partial=not a.keep_partial)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "correlations.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(v) for k, v in r.items()})
    wk = max(16, max(len(r['kpi']) for r in rows) + 2)
    print(f"{'KPI':<{wk}}{'grain':<9}{'points':>7}{'all':>8}{'earlier':>9}{'later':>8}")
    for r in rows:
        print(f"{r['kpi']:<{wk}}{r['grain']:<9}{r['points']:>7}{_fmt(r['correlation']):>8}"
              f"{_fmt(r['earlier_correlation']):>9}{_fmt(r['later_correlation']):>8}")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
