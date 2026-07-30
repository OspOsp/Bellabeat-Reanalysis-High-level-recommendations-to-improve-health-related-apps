# Analysis

Four scripts that reproduce every number quoted in
[`../RECOMMENDATIONS.md`](../RECOMMENDATIONS.md) and
[`../docs/DATA_QUALITY.md`](../docs/DATA_QUALITY.md). Run them in order from this
directory; each prints its findings and writes CSVs to
[`../outputs/tables/`](../outputs/tables/).

```bash
pip install -r ../requirements.txt
python 01_data_quality.py
python 02_activity_and_sleep.py
python 03_intraday_rhythm.py     # reads ~1.3M rows, takes ~2 minutes
python 04_figures.py
```

| Script | Answers | Writes |
|---|---|---|
| `common.py` | — shared loaders, timestamp formats, SVG chart builder | — |
| `01_data_quality.py` | Who is actually in this data? How consistently was the device worn? What cannot be trusted? | `feature_adoption`, `wear_coverage`, `daily_active_users` |
| `02_activity_and_sleep.py` | How is the day spent? Who are the segments? What drives calorie burn? Is the weekday effect real? Is the sleep correlation real? | `time_budget`, `user_segments`, `user_profiles`, `weekday_profile`, `calorie_correlations`, `sleep_by_sedentary_quartile` |
| `03_intraday_rhythm.py` | When does the day happen, and how is it broken up? | `hourly_profile`, `hourly_steps_weekday_weekend`, `sedentary_bouts`, `sedentary_bout_distribution` |
| `04_figures.py` | Renders the five README figures from the tables above | 10 SVGs in `../outputs/figures/` |

## Conventions the scripts enforce

**Non-wear days are excluded.** A day with `TotalSteps == 0` is missing data, not a
sedentary day — 72 of the 77 such days claim exactly 1440 sedentary minutes. Leaving
them in inflates the sedentary share from 79.4% to 81.3%. The bout analysis uses a
stricter 500-step floor.

**Weekdays are compared per person-day, never by total.** The 31-day window contains
five Tuesdays and four Sundays, so totals rank days by calendar frequency.

**Timestamps are parsed explicitly** with `%m/%d/%Y` — these are US-format dates and
inferred parsing reads `4/12/2016` as 4 December.

**Denominators are stated.** Sleep statistics describe 24 tracked sleepers, heart-rate
statistics describe 14 users, not 33.

## Why hand-built SVG

`common.py` emits SVG directly rather than using matplotlib. It keeps the analysis
dependency to pandas + numpy, produces figures that stay readable in a diff, and lets
each chart ship a light and a dark variant that GitHub swaps with `<picture>`. Colours
come from a validated categorical palette — blue and orange for two-series charts, a
single-hue blue ramp for ordinal magnitude — and every chart carries direct value labels
so identity is never conveyed by colour alone.
