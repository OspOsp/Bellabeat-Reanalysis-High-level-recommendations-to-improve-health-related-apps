# Data

18 CSV files from the **FitBit Fitness Tracker Data** set published on Kaggle by
*Mobius*, released under **CC0 1.0 (public domain)**. The files are the raw Kaggle
export — unmodified — reorganised here by time grain.

- **Source:** <https://www.kaggle.com/datasets/arashnic/fitbit>
- **Origin:** 30 Fitbit users who consented to share tracker data through an Amazon
  Mechanical Turk survey. 33 distinct `Id` values actually appear in the files.
- **Window:** 12 April 2016 – 12 May 2016 (31 days).
- **Licence:** CC0 1.0. No attribution required, but the source is credited above.
- **Privacy:** users are pseudonymous integer `Id`s. No names, no demographics —
  **no age, no gender, no height, no location**.

## Layout

Files are grouped by the grain of one row, which is the thing that decides how you
can join and aggregate them.

| Folder | Grain | Files |
|---|---|---|
| [`daily/`](daily/) | one row per user per day | 5 |
| [`hourly/`](hourly/) | one row per user per hour | 3 |
| [`minute/`](minute/) | one row per user per minute (narrow) or per hour with 60 columns (wide) | 8 |
| [`seconds/`](seconds/) | one row per heart-rate reading (~5 s) | 1 |
| [`logs/`](logs/) | one row per event, irregular | 1 |

## Files

| File | Rows | Cols | Size | Notes |
|---|---:|---:|---:|---|
| `daily/dailyActivity_merged.csv` | 940 | 15 | 0.1 MiB | **The main table.** Steps, distance, intensity minutes and calories per day. |
| `daily/dailyCalories_merged.csv` | 940 | 3 | 0.0 MiB | Redundant — a column subset of `dailyActivity`. |
| `daily/dailyIntensities_merged.csv` | 940 | 10 | 0.1 MiB | Redundant — a column subset of `dailyActivity`. |
| `daily/dailySteps_merged.csv` | 940 | 3 | 0.0 MiB | Redundant — a column subset of `dailyActivity`. |
| `daily/sleepDay_merged.csv` | 413 | 5 | 0.0 MiB | 24 users only. Contains 3 exact duplicate rows. |
| `hourly/hourlyCalories_merged.csv` | 22,099 | 3 | 0.8 MiB | |
| `hourly/hourlyIntensities_merged.csv` | 22,099 | 4 | 0.9 MiB | Total and average intensity per hour. |
| `hourly/hourlySteps_merged.csv` | 22,099 | 3 | 0.8 MiB | |
| `minute/minuteCaloriesNarrow_merged.csv` | 1,325,580 | 3 | 63.4 MiB | **Git LFS** |
| `minute/minuteCaloriesWide_merged.csv` | 21,645 | 62 | 21.9 MiB | Same data, 60 minute-columns per hour. |
| `minute/minuteIntensitiesNarrow_merged.csv` | 1,325,580 | 3 | 44.2 MiB | **Git LFS** |
| `minute/minuteIntensitiesWide_merged.csv` | 21,645 | 62 | 3.2 MiB | |
| `minute/minuteMETsNarrow_merged.csv` | 1,325,580 | 3 | 45.5 MiB | **Git LFS**. METs ×10 (see below). |
| `minute/minuteSleep_merged.csv` | 188,521 | 4 | 8.4 MiB | Per-minute sleep state. |
| `minute/minuteStepsNarrow_merged.csv` | 1,325,580 | 3 | 44.4 MiB | **Git LFS** |
| `minute/minuteStepsWide_merged.csv` | 21,645 | 62 | 3.3 MiB | |
| `seconds/heartrate_seconds_merged.csv` | 2,483,658 | 3 | 85.4 MiB | **Git LFS**. 14 users only. |
| `logs/weightLogInfo_merged.csv` | 67 | 8 | 0.0 MiB | 8 users. 61% entered by hand. |

Column-level definitions, units and known traps are in
[`../docs/DATA_DICTIONARY.md`](../docs/DATA_DICTIONARY.md).

## Narrow vs wide

The `minute/` folder ships the same three metrics twice. **Narrow** is one row per
minute (`Id, ActivityMinute, value`) and is what you want for anything time-series.
**Wide** is one row per hour with 60 value columns; it is smaller on disk but has to
be melted before use. Only the narrow files are used in this repo's analysis.

## Large files and Git LFS

Five files exceed 40 MiB and are tracked with [Git LFS](https://git-lfs.com) via
[`../.gitattributes`](../.gitattributes) — GitHub warns above 50 MiB and rejects any
single file above 100 MiB. Before your first clone or push:

```bash
git lfs install
git clone <your-repo-url>     # LFS files download automatically
```

If you would rather not use LFS, delete the `.gitattributes` entries and add the five
paths to `.gitignore` instead; every script in [`../analysis/`](../analysis/) except
the sedentary-bout section of `03_intraday_rhythm.py` runs on the small files alone,
and the large files can be re-downloaded from the Kaggle link above.

## Caveats before you use this

This is a small, old, undocumented convenience sample. The specific traps — phantom
sedentary days, minute totals that do not sum to 1440, unequal weekday counts, and a
sleep/sedentary correlation that is pure arithmetic — are written up in
[`../docs/DATA_QUALITY.md`](../docs/DATA_QUALITY.md). Read that before drawing a
conclusion from these files.
