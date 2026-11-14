# kpi-ebitda-tracking-check

Check whether the number you steer by day to day (MER, platform ROAS, contribution margin, anything you can build from your own columns) still moves with EBITDA, at daily, weekly and monthly grain.

> **Built by [Brinker Analytics](https://brinkeranalytics.com).** Eric Brinker's marketing-measurement practice for DTC brands.
> **Contact:** [eric@brinkeranalytics.com](mailto:eric@brinkeranalytics.com) or the [contact page](https://brinkeranalytics.com/contact).

## Why check

Start from the final goal, which for many brands is EBITDA, and work backwards to the numbers that lead to it. Almost no supporting KPI is 100% the same as the final one. Hopefully it lines up about 90% of the time; that's my rule of thumb, not a measured statistic or a correlation cutoff. The job isn't to find a perfect proxy. It's to use the supporting number in context and notice when it has stopped tracking the goal.

You can check that with a correlation test: daily, weekly and monthly. The answer is often different at each grain, and monthly correlation is the most valuable.

This tool doesn't set a cutoff for how tightly the two must move together. It shows you the numbers at each grain, for the whole history and for its earlier and later halves, so you can see whether the relationship has changed.

## Run it on the example data

Python 3.9 or newer, standard library only.

```bash
python kpi_check.py --data example_data/EXAMPLE_daily.csv \
  --kpi "MER=revenue/ad_spend" \
  --kpi "platform_ROAS=platform_revenue/ad_spend" \
  --out output
```

```
KPI             grain     points     all  earlier   later
MER             daily        730   0.730    0.742   0.741
MER             weekly       103   0.508    0.599   0.472
MER             monthly       24   0.451    0.589   0.493
platform_ROAS   daily        730   0.360    0.614   0.294
platform_ROAS   weekly       103  -0.044    0.487  -0.204
platform_ROAS   monthly       24  -0.090    0.490  -0.247
```

The data is made up (see `example_data/README.md`). In it, platform ROAS moved with EBITDA in the earlier half and stopped in the later half, after platform-attributed revenue started drifting up. MER held up better. The daily, weekly and monthly answers differ for both.

## Run it on your own data

1. Export one row per day (or per week, or per month) with a `date` column and the raw columns you need: revenue, ad spend, platform-attributed revenue, contribution margin, EBITDA. Use totals that add up, not ratios.
2. Define each KPI with `--kpi`, either a column (`contribution_margin`) or a ratio of two columns (`MER=revenue/ad_spend`). Ratios are rebuilt from totals at each grain, so a week's MER is the week's revenue over the week's spend, not an average of daily MERs.
3. Name the goal column with `--goal` (default `ebitda`).

If EBITDA only exists monthly in your P&L, give the tool monthly rows. It only computes the grains your data supports. Partial first and last weeks or months are dropped unless you pass `--keep-partial`. Monthly needs enough months to mean anything, so the output always shows how many points each correlation uses.

## Reading the results

- **`all`** is the correlation over the whole history at that grain.
- **`earlier` and `later`** split the history in half. A drop from earlier to later is the "stopped tracking" pattern.
- **Different answers at different grains** are normal. Weight the monthly read most.

A correlation shows two numbers moving together. It can't tell you whether one causes the other.

## What to do with this

- **If a KPI tracks EBITDA monthly and still does in the later half,** keep steering by it, in context, and run the check again each quarter.
- **If it tracked in the earlier half and not the later half,** put it back in context before you move budget on it. Find what changed around the split: tracking, attribution settings, a new channel, pricing.
- **If it tracks daily but not monthly,** don't let the daily view drive monthly or quarterly budget calls.
- **If no supporting KPI tracks EBITDA well,** the leftover question is which spend actually moves the business. Test it only if the answer might change the budget and you will act on the result.

If you want to know which number your team should steer by, send me a note and we'll talk it through: [Get in touch](https://brinkeranalytics.com/contact).

## Free reading on brinkeranalytics.com

- [A marketing reporting system is not a dashboard](https://brinkeranalytics.com/insights/reporting-system-not-dashboard)
- [Marketing reporting systems for DTC brands](https://brinkeranalytics.com/marketing-reporting-system-dtc)
- [Why your Meta, Google, GA4, Shopify, and finance numbers disagree](https://brinkeranalytics.com/insights/why-marketing-numbers-disagree)
- [Marketing measurement glossary for DTC brands](https://brinkeranalytics.com/insights/measurement-glossary-dtc)

## Files

```
kpi_check.py                   the script
example_data/                  made-up example data and how it was generated
example_output/                correlations.csv from the example
scripts/make_example_data.py   seeded generator for the example data
tests/test_kpi_check.py        checks the correlation math, ratio rebuilding and grain handling
```

Run the tests with `python -m unittest discover -s tests`.

## License

The code is MIT licensed (see `LICENSE`). The documentation, including this README, is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) (see `LICENSE-docs`). If you reuse it, please credit Eric Brinker at [Brinker Analytics](https://www.brinkeranalytics.com).
