# Recommendations

Nine recommendations for Bellabeat's product and marketing teams, each tied to a
specific number from [`analysis/`](analysis/) and each paired with a way to tell
whether it worked.

**Read this first.** The evidence base is 33 pseudonymous Fitbit users over 31 days in
spring 2016, with **no gender recorded**. It cannot describe women specifically, it
cannot describe Bellabeat customers, and it is a decade old. Treat what follows as
*hypotheses with quantified motivation* — the strongest ones are cheap to test against
Bellabeat's own app telemetry, which would settle in a week what this dataset can only
suggest. Limits are catalogued in [`docs/DATA_QUALITY.md`](docs/DATA_QUALITY.md).

---

## A. Product

### 1. Treat the first four weeks as the retention battleground, not the onboarding flow

**Evidence.** Devices producing at least one step fell from **31 per day in week 1 to
23 per day in the final week — a 26% decline in 31 days**, before any user had owned
the device long enough to get bored of it. Separately, **8.2% of all person-days record
zero steps**, and 15 of 33 users have at least one such day. One user has 31 days of
records but movement on only 17 of them.

This is the single largest effect in the dataset, and it is invisible if you only
analyse the days people *did* wear the device. Every activity insight below is
conditional on the device being on a wrist — and it increasingly is not.

**What to do.** Move retention ahead of feature depth on the roadmap. Instrument day-7,
day-14 and day-30 wear rates as the primary product metric. Trigger a lightweight
re-engagement path when a user's wear streak breaks for two consecutive days, and make
charging frictionless enough that a charge day does not become a lost day.

**How you'd know it worked.** Day-30 wear rate rises; the gap between "days with a
record" and "days with movement" narrows.

### 2. Schedule prompts by day type, not by the clock

**Evidence.** The active window sits at a genuinely different time on weekends:

| | Weekday | Weekend |
|---|---:|---:|
| Peak hour | **18:00** (640 steps) | **13:00** (639 steps) |
| Steps at 07:00 | 349 | 184 |
| Steps at 06:00 | 220 | 62 |

The weekend day starts roughly **two hours later** and peaks **five hours earlier**. A
single fixed reminder schedule — the kind the original analysis proposed, and the kind
most trackers ship — is tuned to the weekday shape and misfires on two days in seven,
arriving before the user is up on Saturday and after her most active window has closed.

**What to do.** Split the notification schedule into weekday and weekend profiles at
minimum; better, learn each user's actual active window from her own first two weeks of
data and place prompts at its leading edge. Prompt *before* a known-active window, not
during it — a nudge at 17:30 on a weekday and 12:30 on a Sunday.

**How you'd know it worked.** Notification tap-through by day type converges; the gap
between weekday and weekend response rates closes.

### 3. Make the sedentary *bout* the unit of intervention, not the daily step total

**Evidence.** Sitting arrives in long blocks, not as a steady background:

- The median waking day contains an unbroken sedentary stretch of **105 minutes**.
- **78.5%** of waking days contain a block of **60+ minutes**; **43.4%** contain one of
  **120+ minutes**.
- The average waking day contains **4.3 separate sedentary blocks of 30 minutes or more**.
- **74.5%** of waking minutes (07:00–21:59) register zero intensity.

A daily step goal cannot see any of this — 8,000 steps looks identical whether it was
accumulated steadily or in two bursts around a four-hour block of sitting. But the bout
is what an app can actually interrupt, and it is where the intervention is both easy and
timely.

**What to do.** Ship an hourly move prompt keyed to *elapsed* sedentary time rather than
the clock, firing at 50 minutes of continuous stillness during the user's waking window.
Target the ~4 long blocks a day rather than a single end-of-day summary. Report "longest
sit" and "blocks broken" alongside step count.

**How you'd know it worked.** Median longest daily bout falls; the share of days
containing a 120-minute block falls. Both are measurable from data Bellabeat already
collects.

### 4. Never show a non-wear day as a sedentary day

**Evidence.** Of the 77 zero-step days in the file, **72 report exactly 1440 sedentary
minutes** — a full 24 hours of recorded stillness. The pipeline encodes *absence of
data* as *maximum sedentary behaviour*.

For analytics this inflates the headline sedentary share from 79.4% to 81.3%. In a
product it is worse: a user who charges her tracker overnight opens the app to a perfect
red day she did not earn. For a brand built on encouragement, the one thing worse than
no feedback is discouraging feedback that is factually wrong.

**What to do.** Classify a day as non-wear rather than sedentary when steps and
heart-rate coverage are both absent, and display it as "no data" — neutral, not
negative. Exclude non-wear days from streaks, averages and any goal calculation.

**How you'd know it worked.** Sedentary-time distributions lose their spike at exactly
1440 minutes.

### 5. Remove every dependency on manual entry

**Evidence.** Anything requiring the user to act is close to unused in this panel:

- **32 of 940 person-days (3.4%)** have a manually logged activity, from **4 of 33 users**.
- **Only 8 of 33 users (24%) ever recorded a weight**, and two of them account for 54 of
  the 67 entries — so 76% of the panel never logged once, and the feature's apparent
  usage is two enthusiasts.
- Body fat is present on **2 rows** in the entire dataset.

Meanwhile the fully automatic metric — steps — has 100% coverage. Capture that happens
by itself produces data; capture that depends on remembering does not.

*(This dataset cannot cleanly separate manual from automatic weight logging: the 5
manual and 3 automatic users log at similar median rates, and both groups contain one
heavy user. The argument above rests on adoption breadth, not on that comparison.)*

**What to do.** Assume nothing will be typed in. Any feature whose value depends on
manual input — food logging, mood, symptom tracking, workout tagging — should either be
inferred, reduced to a single tap, or cut. If body composition matters to the roadmap,
bundle a connected scale rather than asking for a number.

**How you'd know it worked.** Share of records arriving without user action rises;
completeness of any given metric stops correlating with user conscientiousness.

---

## B. Marketing and positioning

### 6. Lead with intensity, not volume

**Evidence.** Correlation with daily calorie burn:

| Predictor | r | R² |
|---|---:|---:|
| Total distance | 0.625 | 0.391 |
| **Very active minutes** | **0.612** | **0.375** |
| Total steps | 0.562 | 0.316 |
| Fairly active minutes | 0.265 | 0.070 |
| **Lightly active minutes** | **0.182** | **0.033** |
| Sedentary minutes | −0.031 | 0.001 |

Very active minutes explain **11× more variance in calorie burn than lightly active
minutes** (R² 0.375 vs 0.033) — and the panel spends **210 minutes a day lightly active
against 23 minutes very active**. The scarce input is the one that matters.

This is a genuinely useful message for the target customer, because it inverts the
time objection: the barrier to fitness is assumed to be an hour you don't have, and the
data says twenty hard minutes does more.

**What to do.** Build campaign messaging around short, hard, achievable efforts —
"twenty minutes that count" — rather than step-count volume. Position it as respecting
the customer's time rather than demanding more of it.

**Caveat worth stating internally.** These correlations are descriptive, and calorie
burn is partly a proxy for body size, which this dataset does not record. Intensity is
the best-supported lever here; it is not a controlled finding.

### 7. Segment the message — half the base is nowhere near the goal

**Evidence.** Users split into four clearly separated groups by mean daily steps:

| Segment | Users | Mean steps | Sedentary min/day | MVPA min/day |
|---|---:|---:|---:|---:|
| Inactive (<5k) | 7 (21%) | 3,687 | 1,093 | 12 |
| Low active (5–7.5k) | 9 (27%) | 6,550 | 1,083 | 17 |
| Somewhat active (7.5–10k) | 10 (30%) | 8,790 | 786 | 46 |
| Active (10k+) | 7 (21%) | 12,680 | 975 | 66 |

**48% of the panel averages under 7,500 steps**, sits over 18 hours a day, and gets
12–17 minutes of moderate-to-vigorous activity — well under the WHO's 150 minutes a
week. Only **7 of 33 users average 10,000 steps**; **19 of 33 meet the WHO threshold**.

A "10,000 steps" campaign speaks to the fifth of the base already achieving it and reads
as unreachable to the near-half who are at a third of it.

**What to do.** Set relative goals — a percentage improvement on the user's own
baseline — instead of a universal target, and segment lifecycle messaging by starting
activity level. The largest commercial opportunity is the 48% who are furthest from the
goal and therefore have the most to gain, provided the goal is set where they can reach it.

**How you'd know it worked.** Goal-completion rates converge across segments rather than
concentrating in the most active one.

### 8. Make sleep the wedge — but fix overnight wear first

**Evidence.** Sleep is where the panel is measurably struggling:

- Mean sleep is **6 h 59 m**, just under the recommended seven hours.
- **44.1% of nights fall under 7 hours**; **13 of 24 tracked sleepers average under 7 hours**.
- Users lie awake in bed **39 minutes a night** (91.6% sleep efficiency).

But the tracking itself is the bottleneck: only **24 of 33 users produced any sleep
data, and only 15 wore the device overnight on 10 or more nights**. Sleep coverage is
less than half the panel, while step coverage is 100%.

Bellabeat's jewellery-form products are unusually well placed here — an unobtrusive
device is easier to wear to bed than a sports watch, and that is a product advantage
that maps directly onto the gap in the data.

**What to do.** Position overnight comfort as the reason to choose Bellabeat, and make
battery life span a full sleep cycle without a bedtime charge. Then build the sleep
feature set on the 39 idle minutes in bed — a wind-down prompt is a concrete, defensible
intervention.

**How you'd know it worked.** Share of users with 10+ nights of sleep data per month —
today's equivalent is 45% — becomes the headline sleep metric, ahead of any sleep-score
feature.

---

## C. Measurement

### 9. Fix the evidence base before betting on it

The most valuable output of this analysis is a precise list of what it could not
determine. Bellabeat's own app can answer all of it:

| Question this data cannot answer | What to instrument |
|---|---|
| Do any of these patterns hold for women? | Gender and age at onboarding — **the business task asks about women and this dataset cannot identify one** |
| Which app features get used? | Screen-open and feature-tap telemetry; there is none here |
| Do notifications change behaviour? | Notification send/open/act events, held against a control group |
| Do habits survive past a month? | A retention cohort longer than 31 days |
| Is there seasonality? | 12+ months of data; this window is one spring month |
| Does the membership change outcomes? | Member vs non-member activity, matched on baseline |

Two cheap, high-value additions: **a holdout group that receives no prompts**, without
which none of recommendations 2–4 can be causally evaluated; and **wear-time as a
first-class metric**, since it silently conditions every other number in the product.

---

## Findings I deliberately did not turn into recommendations

Recording these matters as much as the recommendations — three plausible headlines in
this dataset do not survive checking.

**"Sitting less improves sleep."** Minutes asleep correlate with sedentary minutes at
r = −0.601, the strongest relationship in the daily data. It is arithmetic, not
behaviour: sleep and intensity minutes already account for the day, so sedentary time is
close to `1440 − sleep − active` by construction. Normalised as a share of *awake* time,
the correlation collapses to **−0.088**. No recommendation here rests on it.

**"Activity peaks on Tuesday."** The 31-day window contains five Tuesdays, Wednesdays
and Thursdays but only four of every other day. Ranking weekdays by *total* steps ranks
them by how often they appear in the calendar. On a per-person-day basis Wednesday falls
from 2nd to 5th, Saturday ties Tuesday for the lead, and the spread across all seven days
is 17% — a weak effect on 110–139 person-days. There is no Tuesday campaign here.

**"Users burn ~1,700 calories doing nothing."** The intercept of a calorie-vs-active-minutes
regression is not a basal metabolic rate. It is an average across 33 people of unknown
size, sex and age, extrapolated to a region with few observations. It should not be used
as a weight-loss threshold for any individual customer.
