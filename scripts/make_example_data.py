#!/usr/bin/env python3
"""Seeded generator for the made-up example: 24 months of daily numbers for one store.

Not from any store, client or ad account. For the first 16 months platform-attributed
revenue is a steady share of store revenue. From month 17 that share drifts up each month,
so platform ROAS climbs while EBITDA doesn't follow.
"""
import csv
import datetime as dt
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "example_data"
random.seed(20261113)
START = dt.date(2024, 11, 1)
END = dt.date(2026, 10, 31)
MARGIN_BEFORE_MARKETING = 0.45
FIXED_PER_DAY = 2600.0


def main():
    OUT.mkdir(exist_ok=True)
    with open(OUT / "EXAMPLE_daily.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "revenue", "ad_spend", "platform_revenue", "contribution_margin", "ebitda"])
        d, i = START, 0
        while d <= END:
            month_idx = (d.year - START.year) * 12 + d.month - START.month
            season = 1 + 0.25 * math.sin(2 * math.pi * (d.timetuple().tm_yday - 250) / 365)
            spend = 3000 * season * random.uniform(0.85, 1.15) * (1 + 0.01 * month_idx)
            demand = 12000 * season * random.gauss(1, 0.12)
            revenue = demand + 1.1 * spend * random.gauss(1, 0.2)
            share = 0.55 if month_idx < 16 else 0.55 + 0.04 * (month_idx - 15)
            platform = revenue * share * random.gauss(1, 0.08)
            cm = revenue * MARGIN_BEFORE_MARKETING - spend
            ebitda = cm - FIXED_PER_DAY
            w.writerow([d.isoformat(), f"{revenue:.2f}", f"{spend:.2f}", f"{platform:.2f}", f"{cm:.2f}", f"{ebitda:.2f}"])
            d += dt.timedelta(days=1)
            i += 1


if __name__ == "__main__":
    main()
