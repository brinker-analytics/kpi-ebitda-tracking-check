# Example data

Everything in this folder is made up. `scripts/make_example_data.py` generated it with a fixed seed, so you can rebuild the same file. It comes from no store, client or ad account.

- `EXAMPLE_daily.csv`: 730 days (Nov 1, 2024 to Oct 31, 2026) of revenue, ad spend, platform-attributed revenue, contribution margin and EBITDA for one made-up store. From month 17, platform-attributed revenue drifts up as a share of store revenue, so platform ROAS rises while EBITDA doesn't follow.

The seasonality, noise and the drift are settings in the script. Don't read the example correlations as a benchmark.
