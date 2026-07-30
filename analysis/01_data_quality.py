"""Step 1 - data quality, device wear and feature adoption.

Answers: how many users does each dataset actually cover, how consistently was
the device worn, and which records cannot be trusted.

Writes: feature_adoption.csv, wear_coverage.csv, daily_active_users.csv
"""
import pandas as pd

from common import (DATA, STUDY_END, STUDY_START, daily_activity, heartrate,
                    save_table, sleep_day, weight_log)


def main() -> None:
    da = daily_activity()
    sl = sleep_day()
    wt = weight_log()
    sl_raw = len(pd.read_csv(DATA / "daily" / "sleepDay_merged.csv"))

    print("=" * 70)
    print("STUDY WINDOW", STUDY_START.date(), "->", STUDY_END.date())
    print("daily activity: %d rows, %d users, %d exact duplicates"
          % (len(da), da.Id.nunique(), da.duplicated().sum()))
    print("sleepDay      : %d raw rows, %d exact duplicates removed -> %d"
          % (sl_raw, sl_raw - len(sl), len(sl)))

    # -- feature adoption funnel ------------------------------------------
    hr = heartrate()
    adoption = pd.DataFrame(
        [
            ("Activity / steps", da.Id.nunique(), "worn during the day"),
            ("Sleep tracking", sl.Id.nunique(), "worn overnight"),
            ("Sleep, 10+ nights", (sl.groupby("Id").Date.nunique() >= 10).sum(),
             "habitual overnight wear"),
            ("Heart rate", hr.Id.nunique(), "device supports/enables HR"),
            ("Weight log", wt.Id.nunique(), "any weight entry"),
            ("Manual activity log", (da.LoggedActivitiesDistance > 0).groupby(da.Id).any().sum(),
             "ever logged a workout by hand"),
            ("Body-fat entry", wt.loc[wt.Fat.notna(), "Id"].nunique(), "any body-fat entry"),
        ],
        columns=["Feature", "Users", "Meaning"],
    ).set_index("Feature")
    adoption["ShareOf33"] = (adoption.Users / da.Id.nunique()).round(3)
    print("\n=== FEATURE ADOPTION (out of %d users) ===" % da.Id.nunique())
    print(adoption.to_string())
    save_table(adoption, "feature_adoption")

    # -- wear coverage -----------------------------------------------------
    cov = pd.DataFrame({
        "DaysWithRecord": da.groupby("Id").Date.nunique(),
        "DaysWorn": da[da.Worn].groupby("Id").Date.nunique(),
        "SleepNights": sl.groupby("Id").Date.nunique(),
        "MeanSteps": da[da.Worn].groupby("Id").TotalSteps.mean().round(0),
    }).fillna(0).astype({"SleepNights": int})
    cov["NonWearDays"] = cov.DaysWithRecord - cov.DaysWorn
    print("\n=== WEAR COVERAGE PER USER ===")
    print(cov.sort_values("DaysWorn").to_string())
    save_table(cov, "wear_coverage")

    zero = da[~da.Worn]
    print("\nnon-wear days (0 steps): %d of %d rows (%.1f%%) across %d users"
          % (len(zero), len(da), 100 * len(zero) / len(da), zero.Id.nunique()))
    print("  of those, %d report exactly 1440 sedentary minutes -> a full phantom"
          " sedentary day that inflates every sedentary average" % (zero.SedentaryMinutes == 1440).sum())

    # -- integrity checks --------------------------------------------------
    mins = (da.VeryActiveMinutes + da.FairlyActiveMinutes
            + da.LightlyActiveMinutes + da.SedentaryMinutes)
    print("\n=== INTEGRITY ===")
    print("intensity minutes != 1440 on %d of %d rows (min %d, max %d)"
          % ((mins != 1440).sum(), len(da), mins.min(), mins.max()))
    print("TrackerDistance != TotalDistance on %d rows" % (~da.TrackerDistance.eq(da.TotalDistance)).sum())
    print("weight logs: %d rows, %.0f%% entered by hand; one user supplies %d of them"
          % (len(wt), 100 * (wt.IsManualReport == True).mean(),  # noqa: E712
             wt.Id.value_counts().iloc[0]))

    # -- daily active users (engagement decay) -----------------------------
    dau = (da[da.Worn].groupby("Date").Id.nunique().rename("ActiveUsers").to_frame())
    dau["ShareOfPanel"] = (dau.ActiveUsers / da.Id.nunique()).round(3)
    print("\n=== DAILY ACTIVE DEVICES ===")
    print("first 7 days mean %.1f -> last 7 days mean %.1f (%.0f%% decline)"
          % (dau.ActiveUsers.head(7).mean(), dau.ActiveUsers.tail(7).mean(),
             100 * (1 - dau.ActiveUsers.tail(7).mean() / dau.ActiveUsers.head(7).mean())))
    print(dau.to_string())
    save_table(dau, "daily_active_users")


if __name__ == "__main__":
    main()
