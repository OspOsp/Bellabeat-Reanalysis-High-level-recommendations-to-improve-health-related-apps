"""Step 2 - what the panel actually does, and how sleep relates to it.

Non-wear days (0 steps) are excluded throughout: they are missing data, not
sedentary days, and leaving them in inflates every sedentary statistic.

Writes: user_segments.csv, weekday_profile.csv, calorie_correlations.csv,
        time_budget.csv, sleep_by_sedentary_quartile.csv
"""
import pandas as pd

from common import DOW, daily_activity, save_table, sleep_day

WHO_MVPA_PER_DAY = 150 / 7  # WHO: 150 min moderate-to-vigorous activity per week


def main() -> None:
    da = daily_activity()
    worn = da[da.Worn].copy()

    # -- how the tracked day is spent --------------------------------------
    budget = pd.DataFrame({
        "Minutes": [worn.VeryActiveMinutes.sum(), worn.FairlyActiveMinutes.sum(),
                    worn.LightlyActiveMinutes.sum(), worn.SedentaryMinutes.sum()],
    }, index=["Very active", "Fairly active", "Lightly active", "Sedentary"])
    budget["Share"] = (budget.Minutes / budget.Minutes.sum()).round(4)
    budget["MeanMinPerDay"] = (budget.Minutes / len(worn)).round(1)
    print("=== TIME BUDGET (wear days only, %d person-days) ===" % len(worn))
    print(budget.to_string())
    save_table(budget, "time_budget")

    # -- per-user segments --------------------------------------------------
    u = worn.groupby("Id").agg(
        Days=("Date", "nunique"),
        MeanSteps=("TotalSteps", "mean"),
        MeanCalories=("Calories", "mean"),
        MeanSedentaryMin=("SedentaryMinutes", "mean"),
        MeanLightMin=("LightlyActiveMinutes", "mean"),
        MeanMVPAMin=("MVPAMinutes", "mean"),
        MeanVeryActiveMin=("VeryActiveMinutes", "mean"),
    )
    bands = pd.cut(u.MeanSteps, [0, 5000, 7500, 10000, float("inf")],
                   labels=["Inactive (<5k)", "Low active (5-7.5k)",
                           "Somewhat active (7.5-10k)", "Active (10k+)"])
    u["Segment"] = bands
    seg = u.groupby("Segment", observed=False).agg(
        Users=("MeanSteps", "size"),
        MeanSteps=("MeanSteps", "mean"),
        MeanCalories=("MeanCalories", "mean"),
        MeanSedentaryMin=("MeanSedentaryMin", "mean"),
        MeanMVPAMin=("MeanMVPAMin", "mean"),
    ).round(0)
    seg["ShareOfPanel"] = (seg.Users / len(u)).round(3)
    print("\n=== USER SEGMENTS (mean daily steps) ===")
    print(seg.to_string())
    save_table(seg, "user_segments")
    save_table(u.round(1), "user_profiles")

    print("\npanel mean sedentary time: %.1f h/day" % (u.MeanSedentaryMin.mean() / 60))
    print("users meeting WHO 150 min/week MVPA: %d of %d"
          % ((u.MeanMVPAMin >= WHO_MVPA_PER_DAY).sum(), len(u)))
    print("users averaging 10k+ steps: %d of %d" % ((u.MeanSteps >= 10000).sum(), len(u)))

    # -- weekday profile ----------------------------------------------------
    # The 31-day window is not a whole number of weeks: Tue/Wed/Thu occur five
    # times, the other four days occur four times. Ranking weekdays by TOTAL
    # steps therefore ranks them by how often they appear in the calendar.
    # Only the per-person-day mean is comparable.
    wk = worn.groupby("DayOfWeek").agg(
        PersonDays=("Id", "size"),
        TotalSteps=("TotalSteps", "sum"),
        MeanSteps=("TotalSteps", "mean"),
        MeanCalories=("Calories", "mean"),
        MeanSedentaryMin=("SedentaryMinutes", "mean"),
        MeanMVPAMin=("MVPAMinutes", "mean"),
    ).reindex(DOW).round(1)
    wk.insert(0, "CalendarOccurrences",
              da[["Date"]].drop_duplicates().Date.dt.day_name().value_counts().reindex(DOW))
    wk["RankByTotal"] = wk.TotalSteps.rank(ascending=False).astype(int)
    wk["RankByMean"] = wk.MeanSteps.rank(ascending=False).astype(int)
    print("\n=== WEEKDAY PROFILE (wear days only) ===")
    print(wk.to_string())
    print("\nranking by TOTAL steps puts Tue/Wed/Thu first - the three days that occur"
          " five times.\nOn a per-person-day basis Wednesday falls from rank 2 to rank %d"
          " and Saturday rises to rank %d." % (wk.RankByMean["Wednesday"], wk.RankByMean["Saturday"]))
    print("spread of daily means is only %.0f to %.0f steps (%.1f%%): weekday effect is weak."
          % (wk.MeanSteps.min(), wk.MeanSteps.max(),
             100 * (wk.MeanSteps.max() / wk.MeanSteps.min() - 1)))
    save_table(wk, "weekday_profile")

    # -- what drives calories ----------------------------------------------
    cols = ["TotalSteps", "TotalDistance", "VeryActiveMinutes", "FairlyActiveMinutes",
            "LightlyActiveMinutes", "SedentaryMinutes"]
    corr = worn[cols + ["Calories"]].corr()["Calories"].drop("Calories")
    corr = corr.rename("PearsonRWithCalories").to_frame().round(3)
    corr["R2"] = (corr.PearsonRWithCalories ** 2).round(3)
    print("\n=== DRIVERS OF DAILY CALORIE BURN ===")
    print(corr.sort_values("PearsonRWithCalories", ascending=False).to_string())
    save_table(corr, "calorie_correlations")

    # -- sleep --------------------------------------------------------------
    sl = sleep_day()
    print("\n=== SLEEP ===")
    print("%d nights, %d users; mean %.0f min asleep (%.2f h), efficiency %.1f%%"
          % (len(sl), sl.Id.nunique(), sl.TotalMinutesAsleep.mean(),
             sl.TotalMinutesAsleep.mean() / 60, 100 * sl.SleepEfficiency.mean()))
    print("mean %.0f min awake in bed per night" % sl.AwakeInBed.mean())
    print("nights under 7 h: %.1f%%" % (100 * (sl.TotalMinutesAsleep < 420).mean()))
    per_user = sl.groupby("Id").TotalMinutesAsleep.mean()
    print("users averaging under 7 h: %d of %d tracked sleepers"
          % ((per_user < 420).sum(), len(per_user)))

    m = da.merge(sl, on=["Id", "Date"])
    print("\ncorrelation of minutes asleep with:")
    for c in ["SedentaryMinutes", "TotalSteps", "VeryActiveMinutes", "LightlyActiveMinutes"]:
        print("  %-22s r = %+.3f" % (c, m.TotalMinutesAsleep.corr(m[c])))

    # The headline r = -0.60 is mostly an artefact of the tracker's time
    # accounting: sleep + intensity minutes already sum to roughly 1440, so
    # SedentaryMinutes is close to (1440 - sleep - active) by construction.
    # Normalising sedentary time by awake time removes the arithmetic and the
    # relationship all but disappears - so "sit less and you will sleep more"
    # is NOT supported by this dataset.
    closes = m.SedentaryMinutes + m.ActiveMinutes + m.TotalMinutesAsleep
    m["SedentaryShareOfAwake"] = m.SedentaryMinutes / (1440 - m.TotalMinutesAsleep)
    print("\n--- is that correlation real? ---")
    print("sleep + intensity minutes per night: median %.0f of 1440 -> the day is"
          " already fully accounted for" % closes.median())
    print("  r(sleep, sedentary minutes)          = %+.3f" % m.TotalMinutesAsleep.corr(m.SedentaryMinutes))
    print("  r(sleep, sedentary SHARE of awake)   = %+.3f  <- artefact removed"
          % m.TotalMinutesAsleep.corr(m.SedentaryShareOfAwake))
    print("  r(sleep, MVPA minutes)               = %+.3f" % m.TotalMinutesAsleep.corr(m.MVPAMinutes))
    print("  => treat the raw correlation as arithmetic, not behaviour.")

    q = pd.qcut(m.SedentaryMinutes, 4,
                labels=["Q1 least sedentary", "Q2", "Q3", "Q4 most sedentary"])
    sq = m.groupby(q, observed=False).agg(
        Nights=("TotalMinutesAsleep", "size"),
        MeanSedentaryMin=("SedentaryMinutes", "mean"),
        MeanMinutesAsleep=("TotalMinutesAsleep", "mean"),
        MeanSteps=("TotalSteps", "mean"),
    ).round(0)
    sq["MeanHoursAsleep"] = (sq.MeanMinutesAsleep / 60).round(2)
    print("\n=== SLEEP BY SEDENTARY QUARTILE ===")
    print(sq.to_string())
    save_table(sq, "sleep_by_sedentary_quartile")


if __name__ == "__main__":
    main()
