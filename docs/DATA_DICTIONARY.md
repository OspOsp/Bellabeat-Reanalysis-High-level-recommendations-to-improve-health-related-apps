# Data dictionary

Column definitions for the 18 Fitbit files in [`../data/`](../data/). Values marked
**verified** were confirmed against the files themselves rather than taken from the
Fitabase documentation.

Every table keys on `Id` — a pseudonymous integer, one per user, 33 distinct values.

## Timestamp formats

Parsing these wrong is the most common way to get a silently wrong answer, because
`pandas` will happily read `4/12/2016` as 4 December.

| Column | Format | Example |
|---|---|---|
| `ActivityDate`, `ActivityDay` | `%m/%d/%Y` | `4/12/2016` |
| `SleepDay`, `ActivityHour`, `ActivityMinute`, `Time`, `Date`, `date` | `%m/%d/%Y %I:%M:%S %p` | `4/12/2016 12:00:00 AM` |

All timestamps are **device local time**. No timezone is recorded, so cross-user
hour-of-day comparisons assume every participant's clock means the same thing.

---

## `daily/dailyActivity_merged.csv` — 940 rows

The main analysis table. One row per user per day. The other three `daily*` files are
strict column subsets of this one and can be ignored.

| Column | Type | Unit | Notes |
|---|---|---|---|
| `Id` | int | — | User key |
| `ActivityDate` | date | — | |
| `TotalSteps` | int | steps | `0` means **the device was not worn**, not a still day |
| `TotalDistance` | float | km | Includes manually logged activity |
| `TrackerDistance` | float | km | Device-measured only. Differs from `TotalDistance` on 15 rows |
| `LoggedActivitiesDistance` | float | km | Non-zero on only **32 of 940 rows**, from 4 users |
| `VeryActiveDistance` | float | km | Distance while in the "very active" intensity band |
| `ModeratelyActiveDistance` | float | km | |
| `LightActiveDistance` | float | km | |
| `SedentaryActiveDistance` | float | km | Near-zero by definition; effectively unusable |
| `VeryActiveMinutes` | int | min | Intensity band 3 |
| `FairlyActiveMinutes` | int | min | Intensity band 2 |
| `LightlyActiveMinutes` | int | min | Intensity band 1 |
| `SedentaryMinutes` | int | min | Intensity band 0. **Excludes tracked sleep** |
| `Calories` | int | kcal | Total daily burn, including basal metabolism |

The four intensity-minute columns **do not sum to 1440** on 462 of 940 rows (range 2
to 1440) — see [`DATA_QUALITY.md`](DATA_QUALITY.md).

Fitbit's intensity bands are derived from METs, but **the thresholds are not published
in this dataset**. "Very active" cannot be mapped to a specific pace or heart rate here.

## `daily/dailyCalories_merged.csv` · `dailyIntensities_merged.csv` · `dailySteps_merged.csv`

940 rows each, keyed `Id` + `ActivityDay`. Every column appears in `dailyActivity`
under the same name. Redundant.

## `daily/sleepDay_merged.csv` — 413 rows, 24 users

| Column | Type | Unit | Notes |
|---|---|---|---|
| `Id` | int | — | |
| `SleepDay` | datetime | — | Time component is always `12:00:00 AM`; it is a date |
| `TotalSleepRecords` | int | count | Sleep sessions that day; >1 means naps were logged |
| `TotalMinutesAsleep` | int | min | |
| `TotalTimeInBed` | int | min | Always ≥ `TotalMinutesAsleep` |

Contains **3 exact duplicate rows** (413 → 410 after dropping). Derive sleep
efficiency as `TotalMinutesAsleep / TotalTimeInBed`.

## `hourly/hourlySteps_merged.csv` · `hourlyCalories_merged.csv` — 22,099 rows each

| Column | Type | Unit |
|---|---|---|
| `Id` | int | — |
| `ActivityHour` | datetime | start of the hour |
| `StepTotal` / `Calories` | int | steps / kcal |

## `hourly/hourlyIntensities_merged.csv` — 22,099 rows

| Column | Type | Notes |
|---|---|---|
| `TotalIntensity` | int | Sum of the 60 per-minute intensity codes in the hour |
| `AverageIntensity` | float | `TotalIntensity / 60` |

Because the per-minute code is an ordinal band (0–3) and not a physical quantity,
summing it produces an index, not a unit. It is fine for comparing hours; it does not
convert to anything.

## `minute/minuteIntensitiesNarrow_merged.csv` — 1,325,580 rows

| Column | Type | Notes |
|---|---|---|
| `ActivityMinute` | datetime | |
| `Intensity` | int | **Verified codes:** `0` sedentary (83.9%), `1` light (13.6%), `2` moderate (1.0%), `3` very active (1.5%) |

## `minute/minuteMETsNarrow_merged.csv` — 1,325,580 rows

| Column | Type | Notes |
|---|---|---|
| `METs` | int | **Stored ×10 — divide by 10 for true METs.** Verified: median 10 (= 1.0 MET, resting), max 157 (= 15.7 METs) |

Forgetting the ×10 scaling is the classic error with this file; it makes every
participant look like an elite athlete at rest.

## `minute/minuteStepsNarrow_merged.csv` · `minuteCaloriesNarrow_merged.csv` — 1,325,580 rows each

| Column | Type | Unit |
|---|---|---|
| `ActivityMinute` | datetime | |
| `Steps` / `Calories` | int / float | steps / kcal |

## `minute/*Wide_merged.csv` — 21,645 rows each, 62 columns

One row per user-hour: `Id`, `ActivityHour`, then 60 columns `<Metric>00` … `<Metric>59`
holding the value for each minute of that hour. Melt to long form before use. Contains
the same data as the matching narrow file.

## `minute/minuteSleep_merged.csv` — 188,521 rows

| Column | Type | Notes |
|---|---|---|
| `date` | datetime | Lowercase column name, unlike every other file |
| `value` | int | **Verified codes:** `1` asleep (91.5%), `2` restless (7.4%), `3` awake (1.1%) |
| `logId` | int | Groups minutes into one sleep session |

Only `value == 1` counts as asleep. Treating every record in the file as sleep
overstates sleep duration by roughly 9%.

## `seconds/heartrate_seconds_merged.csv` — 2,483,658 rows, 14 users

| Column | Type | Notes |
|---|---|---|
| `Time` | datetime | Roughly every 5 s while worn, but irregular — gaps are non-wear |
| `Value` | int | bpm. Panel mean 77.3; mean over 03:00–04:59 is 60.7, a rough resting proxy |

Covers only 14 of 33 users, so any heart-rate finding describes a sub-panel.

## `logs/weightLogInfo_merged.csv` — 67 rows, 8 users

| Column | Type | Notes |
|---|---|---|
| `Date` | datetime | Irregular; not one row per day |
| `WeightKg` / `WeightPounds` | float | Same measurement, two units |
| `Fat` | float | Body-fat %. **Only 2 non-null values in the entire file** |
| `BMI` | float | Range 21.5–47.5 |
| `IsManualReport` | bool | `True` = typed in by hand (61% of rows) |
| `LogId` | int | Unix epoch in milliseconds |

Two users supply 54 of the 67 rows. This table cannot support a weight-change
analysis, and nothing in this repo attempts one.
