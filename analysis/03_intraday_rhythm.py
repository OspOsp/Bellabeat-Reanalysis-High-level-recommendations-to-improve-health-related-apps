"""Step 3 - when the day actually happens, and how it is broken up.

Two questions the daily grain cannot answer:
  1. Does the active window sit at the same clock time on weekdays and weekends?
  2. How long are the uninterrupted sedentary stretches inside a waking day?

The bout analysis reads ~1.3M minute-level rows and takes a minute or two.

Writes: hourly_steps_weekday_weekend.csv, hourly_profile.csv, sedentary_bouts.csv
"""
import numpy as np
import pandas as pd

from common import daily_activity, hourly, minute_intensities, save_table

WAKING = range(7, 22)      # 07:00-21:59
WEAR_STEP_FLOOR = 500      # a day below this is treated as non-wear


def hourly_profile() -> None:
    hs, hi, hc = hourly("Steps"), hourly("Intensities"), hourly("Calories")

    prof = pd.DataFrame({
        "MeanSteps": hs.groupby("Hour").StepTotal.mean(),
        "MeanIntensity": hi.groupby("Hour").TotalIntensity.mean(),
        "MeanCalories": hc.groupby("Hour").Calories.mean(),
    }).round(1)
    prof["ShareOfDailySteps"] = (
        hs.groupby("Hour").StepTotal.sum() / hs.StepTotal.sum()).round(4)
    print("=== HOURLY PROFILE (mean per user-hour) ===")
    print(prof.to_string())
    save_table(prof, "hourly_profile")

    split = hs.groupby(["Hour", "IsWeekend"]).StepTotal.mean().unstack().round(1)
    split.columns = ["Weekday", "Weekend"]
    split["Difference"] = (split.Weekend - split.Weekday).round(1)
    print("\n=== MEAN STEPS PER HOUR: WEEKDAY vs WEEKEND ===")
    print(split.to_string())
    save_table(split, "hourly_steps_weekday_weekend")

    print("\nweekday peak hour %02d:00 (%.0f steps); weekend peak hour %02d:00 (%.0f steps)"
          % (split.Weekday.idxmax(), split.Weekday.max(),
             split.Weekend.idxmax(), split.Weekend.max()))
    print("07:00 activity: weekday %.0f vs weekend %.0f steps -> the weekend day starts later"
          % (split.Weekday[7], split.Weekend[7]))
    print("share of all steps taken 17:00-20:59: %.1f%%"
          % (100 * prof.ShareOfDailySteps[17:21].sum()))
    print("share of all steps taken 12:00-14:59: %.1f%%"
          % (100 * prof.ShareOfDailySteps[12:15].sum()))


def sedentary_bouts() -> None:
    """Longest uninterrupted zero-intensity stretch inside each waking day."""
    da = daily_activity()
    wear = set(zip(*da.loc[da.TotalSteps >= WEAR_STEP_FLOOR, ["Id", "Date"]].values.T))

    mi = minute_intensities()
    mi["Date"] = mi.Timestamp.dt.normalize()
    mi = mi[mi.Timestamp.dt.hour.isin(WAKING)].sort_values(["Id", "Timestamp"])
    mi = mi[[k in wear for k in zip(mi.Id, mi.Date)]]

    sed = (mi.Intensity == 0).to_numpy()
    key = (mi.Id.astype(str) + "|" + mi.Date.astype(str)).to_numpy()
    # Run-length encode sedentary streaks, breaking at every person-day boundary.
    start = np.r_[True, (key[1:] != key[:-1]) | (sed[1:] != sed[:-1])]
    runs = pd.DataFrame({"PersonDay": key[start],
                         "Minutes": np.bincount(np.cumsum(start) - 1),
                         "Sedentary": sed[start]})
    sr = runs[runs.Sedentary]
    longest = sr.groupby("PersonDay").Minutes.max()
    n30 = sr[sr.Minutes >= 30].groupby("PersonDay").size().reindex(longest.index).fillna(0)

    out = pd.DataFrame({
        "Metric": ["Person-days analysed",
                   "Median longest sedentary bout (min)",
                   "Mean longest sedentary bout (min)",
                   "Share of days with a bout >= 60 min",
                   "Share of days with a bout >= 120 min",
                   "Mean number of >= 30 min bouts per waking day",
                   "Share of waking minutes at zero intensity"],
        "Value": [len(longest), longest.median(), round(longest.mean(), 1),
                  round((longest >= 60).mean(), 3), round((longest >= 120).mean(), 3),
                  round(n30.mean(), 2), round((mi.Intensity == 0).mean(), 3)],
    }).set_index("Metric")
    print("\n=== SEDENTARY BOUTS, waking window 07:00-21:59, wear days only ===")
    print(out.to_string())
    save_table(out, "sedentary_bouts")

    dist = pd.cut(longest, [0, 30, 60, 120, 240, 10_000],
                  labels=["<30", "30-59", "60-119", "120-239", "240+"])
    share = dist.value_counts(normalize=True).sort_index().round(3).rename("ShareOfDays")
    print("\nlongest-bout distribution (minutes):")
    print(share.to_string())
    save_table(share.to_frame(), "sedentary_bout_distribution")


if __name__ == "__main__":
    hourly_profile()
    sedentary_bouts()
