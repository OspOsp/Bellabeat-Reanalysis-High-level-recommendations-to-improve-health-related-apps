# Data quality log

Everything below was found in the files themselves and is reproduced by the scripts in
[`../analysis/`](../analysis/). Each entry states the problem, the decision taken, and
the effect of that decision on the result.

## Summary of decisions

| # | Issue | Decision |
|---|---|---|
| 1 | Zero-step days are non-wear, not sedentary | Excluded from all activity statistics |
| 2 | Intensity minutes do not sum to 1440 | Never reconstruct a day from its parts |
| 3 | Weekday totals are confounded by unequal weekday counts | Report per-person-day means only |
| 4 | Sleep ↔ sedentary correlation is arithmetic | Reported as an artefact, not a finding |
| 5 | 3 duplicate rows in `sleepDay` | Dropped |
| 6 | Coverage differs per feature | Every statistic states its own denominator |
| 7 | 4 `daily*` files overlap | Used `dailyActivity` only |
| 8 | 33 users, 31 days, 2016, no demographics | Directional evidence only |

---

## 1. Zero-step days are missing data wearing a sedentary costume

77 of 940 person-days (8.2%, across 15 of 33 users) record `TotalSteps == 0`. On **72
of those 77**, `SedentaryMinutes` is exactly 1440 — a full 24 hours of recorded
stillness with zero steps and zero calories from movement.

Nobody is motionless for 24 hours. These are days the device sat on a charger, and the
pipeline encoded absence as maximum sedentary behaviour.

**Decision:** all activity statistics exclude rows where `TotalSteps == 0`. The
sedentary-bout analysis uses a stricter floor of 500 steps, since a 30-step day is also
not a real day of wear.

**Effect:** the headline sedentary share falls from **81.3% to 79.4%**. The direction
of every conclusion is unchanged, but the raw figure is inflated by an artefact, and
the original report's 81.3% carries it.

This also matters in-product, not just in analysis: a user who charges her tracker for
a day should not open the app to a screen reporting a perfectly sedentary day she did
not have.

## 2. The parts do not add up to the whole

`VeryActiveMinutes + FairlyActiveMinutes + LightlyActiveMinutes + SedentaryMinutes`
should equal 1440. It does so on only **478 of 940 rows (51%)**; on the other 462 the
sum ranges from 2 to 1439, averaging 1,219 across the file. Tracked sleep is excluded
from these columns, but adding
`TotalMinutesAsleep` back overshoots — on 90 of 410 joinable nights the total exceeds
1440, to a maximum of 1635.

So the day is neither fully accounted for nor internally consistent.

**Decision:** treat each column as an independent measurement. Never derive one band by
subtracting the others, and never express a band as a share of a reconstructed 1440.
Shares in this repo are computed over the *observed* minute total, which is stated
alongside them.

## 3. The Tuesday peak is a calendar artefact

The study window is 31 days, which is not a whole number of weeks. **Tuesday, Wednesday
and Thursday occur five times; Monday, Friday, Saturday and Sunday occur four times.**

Ranking weekdays by *total* steps therefore ranks them mostly by how often they appear
in the calendar:

| Day | Occurrences | Person-days | Rank by total steps | Rank by mean steps/person-day |
|---|---:|---:|---:|---:|
| Monday | 4 | 110 | 6 | 3 |
| Tuesday | 5 | 138 | **1** | **1** |
| Wednesday | 5 | 139 | **2** | 5 |
| Thursday | 5 | 133 | **3** | 4 |
| Friday | 4 | 120 | 5 | 6 |
| Saturday | 4 | 113 | 4 | **2** |
| Sunday | 4 | 110 | 7 | 7 |

On a comparable per-person-day basis Wednesday drops from 2nd to 5th and Saturday rises
to 2nd — statistically tied with Tuesday (8,947 vs 8,949 mean steps). The full spread
across all seven days is 7,627 to 8,949 steps, a 17% range on 110–139 person-days each.

**Decision:** report per-person-day means, and treat the weekday effect as weak.
The original report's "activity peaks on Tuesday and declines steadily to Monday" does
not survive the correction — it is a shape produced by the calendar.

## 4. The sleep/sedentary correlation is arithmetic, not behaviour

Minutes asleep correlate with sedentary minutes at **r = −0.601** — the strongest
relationship anywhere in the daily data, and a tempting headline: *sit less, sleep more.*

It is an artefact. Sleep and intensity minutes already account for the day (median
1,414 of 1,440 minutes), so `SedentaryMinutes` is close to `1440 − sleep − active` **by
construction**. More sleep mechanically means fewer sedentary minutes, whatever the
person did.

Normalising sedentary time as a share of *awake* time removes the arithmetic:

| Measure | r with minutes asleep |
|---|---:|
| Sedentary minutes (raw) | −0.601 |
| **Sedentary share of awake time** | **−0.088** |
| MVPA minutes | −0.182 |

The relationship all but disappears. **This dataset does not support a causal or even a
correlational claim that sitting less improves sleep**, and no recommendation in this
repo rests on one. The check is in `02_activity_and_sleep.py`.

## 5. Duplicates

`sleepDay_merged.csv` contains 3 exact duplicate rows (413 → 410). Dropped in the
loader. `dailyActivity_merged.csv` contains none.

## 6. Every feature has a different denominator

Coverage is not uniform, so "of 33 users" is wrong for most statistics:

| Feature | Users | Share |
|---|---:|---:|
| Activity / steps | 33 | 100% |
| Sleep tracking (any) | 24 | 73% |
| Sleep tracking (10+ nights) | 15 | 45% |
| Heart rate | 14 | 42% |
| Weight log | 8 | 24% |
| Manual activity log | 4 | 12% |
| Body-fat entry | 2 | 6% |

Wear consistency varies just as much: one user has 4 days of data, 20 users have all
31, and one user has 31 records of which only 17 show any steps.

**Decision:** each statistic states the population it describes. Sleep findings are
"of 24 tracked sleepers", not "of 33 users".

## 7. Redundant files

`dailyCalories`, `dailyIntensities` and `dailySteps` are column subsets of
`dailyActivity` with identical keys and values. The `*Wide` minute files duplicate the
`*Narrow` ones in a different shape. Only `dailyActivity` and the narrow files are used
here; the rest are kept because they ship with the Kaggle set.

## 8. Limits that no cleaning can fix

- **33 users.** A single unusual participant moves a group mean visibly. Segment
  sizes here are 7–10 users; treat them as illustrative, not as population estimates.
- **31 days, spring 2016.** No seasonality, no long-run retention, and a decade old.
- **No demographics.** No age, gender, height or location. **The business task asks for
  recommendations about women's habits, and this data cannot identify a single
  participant as a woman.** Every recommendation in this repo is therefore about
  *tracker users*, and its transfer to Bellabeat's female customers is an assumption,
  flagged as such.
- **Self-selected sample.** People who volunteer 31 days of Mechanical Turk tracker data
  are unlikely to be representative of the average buyer.
- **No app telemetry.** Nothing records screen opens, notification responses or feature
  taps — so questions about *app* engagement are answered here only by proxy, through
  whether the device produced data at all.
