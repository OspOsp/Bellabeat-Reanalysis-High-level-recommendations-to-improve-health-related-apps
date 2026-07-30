"""Step 4 - render the figures used in the README.

Reads the CSVs written by steps 1-3 (so it is cheap to re-run) and emits one
light and one dark SVG per figure. The README pairs them with <picture> so the
right variant shows in either GitHub theme.

Run steps 01-03 first.
"""
import pandas as pd

from common import FIGURES, FONT, TABLES, THEMES, Chart, _text, both_themes


def _read(name: str, index_col=0) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", index_col=index_col)


# --------------------------------------------------------------------------
# 1. Engagement decay
# --------------------------------------------------------------------------
def fig_daily_active_devices(theme: str) -> None:
    d = _read("daily_active_users")
    d.index = pd.to_datetime(d.index)

    c = Chart(theme,
              "Devices are abandoned faster than the study can measure",
              "Users recording at least one step, each day of the 31-day window "
              "(33 enrolled)")
    c.set_y(33, ticks=[0, 11, 22, 33])
    c.gridlines("Active devices")

    n = len(d)
    xs = [c.pl + c.plot_w * i / (n - 1) for i in range(n)]
    c.line(list(zip(xs, d.ActiveUsers)), c.t["series"][0], markers=False)
    for x, v in zip(xs, d.ActiveUsers):
        c.body.append(
            f'<circle cx="{x:.1f}" cy="{c.y(v):.1f}" r="3.5" '
            f'fill="{c.t["series"][0]}" stroke="{c.t["surface"]}" stroke-width="2"/>'
        )

    labels = [d.index[i].strftime("%b %d") if i % 5 == 0 or i == n - 1 else ""
              for i in range(n)]
    c.x_labels(xs, labels)
    c.x_axis_title("Date")

    c.point_label(xs[0], d.ActiveUsers.iloc[0], "31 devices", dy=-12, dx=0)
    c.point_label(xs[-1], d.ActiveUsers.iloc[-1], "17", anchor="end", dx=-6, dy=-10)
    c.note("Final day is a partial collection day. Comparing full weeks: "
           "31.0 devices/day in week 1 vs 23.0 in the last 7 days, a 26% decline.")
    c.save("01-daily-active-devices")


# --------------------------------------------------------------------------
# 2. Feature adoption
# --------------------------------------------------------------------------
def fig_feature_adoption(theme: str) -> None:
    d = _read("feature_adoption")
    d = d.loc[["Activity / steps", "Sleep tracking", "Sleep, 10+ nights", "Heart rate",
               "Weight log", "Manual activity log", "Body-fat entry"]]

    c = Chart(theme,
              "Everything beyond step counting is a minority behaviour",
              "Users out of 33 who ever produced a record for each feature",
              pad=(64, 28, 104, 74))
    c.set_y(33, ticks=[0, 11, 22, 33])
    c.gridlines("Users")

    n = len(d)
    slot = c.plot_w / n
    bw = min(slot * 0.62, 76)
    centres = []
    for i, (label, row) in enumerate(d.iterrows()):
        x = c.pl + slot * i + (slot - bw) / 2
        c.vbar(x, bw, row.Users, c.t["series"][0])
        c.value_label(x + bw / 2, row.Users,
                      f"{int(row.Users)}  ({row.ShareOf33:.0%})")
        centres.append(x + bw / 2)
    c.x_labels(centres, list(d.index), rotate=-30)
    c.note("Only 4 users ever logged a workout by hand: manual entry is not a "
           "habit worth designing around.")
    c.save("02-feature-adoption")


# --------------------------------------------------------------------------
# 3. Weekday vs weekend rhythm
# --------------------------------------------------------------------------
def fig_hourly_rhythm(theme: str) -> None:
    d = _read("hourly_steps_weekday_weekend")

    c = Chart(theme,
              "The weekend day runs on a different clock",
              "Mean steps per user-hour, by hour of day")
    c.set_y(700, ticks=[0, 175, 350, 525, 700])
    c.gridlines("Mean steps per hour")
    c.legend([("Weekday", c.t["series"][0]), ("Weekend", c.t["series"][1])])

    n = len(d)
    xs = [c.pl + c.plot_w * i / (n - 1) for i in range(n)]
    c.line(list(zip(xs, d.Weekday)), c.t["series"][0], markers=False)
    c.line(list(zip(xs, d.Weekend)), c.t["series"][1], markers=False)
    for col, colour in (("Weekday", c.t["series"][0]), ("Weekend", c.t["series"][1])):
        i = int(d[col].values.argmax())
        c.body.append(
            f'<circle cx="{xs[i]:.1f}" cy="{c.y(d[col].iloc[i]):.1f}" r="5" '
            f'fill="{colour}" stroke="{c.t["surface"]}" stroke-width="2"/>'
        )
    wd = int(d.Weekday.values.argmax())
    we = int(d.Weekend.values.argmax())
    # The two peaks sit at nearly the same height, so the weekend label drops
    # below its marker rather than colliding with the weekday one.
    c.point_label(xs[wd], d.Weekday.iloc[wd], "Weekday peak 18:00", anchor="end", dx=-10, dy=-8)
    c.point_label(xs[we], d.Weekend.iloc[we], "Weekend peak 13:00", dx=8, dy=22)

    labels = [f"{h:02d}" if h % 3 == 0 else "" for h in d.index]
    c.x_labels(xs, labels)
    c.x_axis_title("Hour of day")
    c.note("At 07:00 the weekday panel takes 349 steps to the weekend's 184. A single "
           "fixed reminder schedule misfires on two days in seven.")
    c.save("03-hourly-rhythm")


# --------------------------------------------------------------------------
# 4. Sedentary bouts
# --------------------------------------------------------------------------
def fig_sedentary_bouts(theme: str) -> None:
    d = _read("sedentary_bout_distribution")
    order = ["<30", "30-59", "60-119", "120-239", "240+"]
    d = d.loc[order]

    c = Chart(theme,
              "Sitting arrives in long blocks, not a steady drizzle",
              "Longest uninterrupted sedentary stretch in the waking day "
              "(07:00-21:59), 841 wear-days")
    c.set_y(0.40, ticks=[0, 0.1, 0.2, 0.3, 0.4], fmt=lambda v: f"{v:.0%}")
    c.gridlines("Share of days")

    n = len(d)
    slot = c.plot_w / n
    bw = min(slot * 0.6, 92)
    centres = []
    for i, (label, row) in enumerate(d.iterrows()):
        x = c.pl + slot * i + (slot - bw) / 2
        c.vbar(x, bw, row.ShareOfDays, c.t["series"][0])
        c.value_label(x + bw / 2, row.ShareOfDays, f"{row.ShareOfDays:.0%}")
        centres.append(x + bw / 2)
    c.x_labels(centres, order)
    c.x_axis_title("Longest sedentary bout (minutes)")
    c.note("43% of waking days contain an unbroken sedentary block of two hours or more; "
           "the median day's longest block is 105 minutes.")
    c.save("04-sedentary-bouts")


# --------------------------------------------------------------------------
# 5. Time budget (single stacked bar - a composition of one whole)
# --------------------------------------------------------------------------
def fig_time_budget(theme: str) -> None:
    d = _read("time_budget")
    order = ["Sedentary", "Lightly active", "Fairly active", "Very active"]
    d = d.loc[order]
    t = THEMES[theme]
    # Ordinal blue ramp: darkest step carries the largest share.
    ramp = [t["ordinal"][3], t["ordinal"][2], t["ordinal"][1], t["ordinal"][0]]

    w, h = 900, 300
    pl, pr = 28, 28
    bar_y, bar_h = 150, 56
    plot_w = w - pl - pr

    body = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" '
        f'height="{h}" role="img" aria-label="How the tracked day is spent">',
        f'<rect width="{w}" height="{h}" fill="{t["surface"]}"/>',
        _text(pl, 34, "Four fifths of the tracked day is sedentary", t["primary"], 16, weight=600),
        _text(pl, 54, "Share of all recorded minutes across 863 wear-days, by intensity band",
              t["secondary"], 12),
    ]

    # Slivers get stacked callouts above the bar; stacking avoids the collision
    # that centred labels would cause on two adjacent ~13px segments.
    callout_rows = [bar_y - 26, bar_y - 52]
    small = 0
    x = pl
    for i, (label, row) in enumerate(d.iterrows()):
        seg = plot_w * row.Share
        gap = 2 if i < len(d) - 1 else 0          # 2px surface gap between fills
        seg_w = max(seg - gap, 1.0)
        r = min(4.0, seg_w / 2)
        body.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" '
                    f'rx="{r:.1f}" fill="{ramp[i]}"/>')
        cx = x + seg_w / 2

        if row.Share > 0.10:                      # label inside only where it fits
            body.append(_text(cx, bar_y + 26, f"{row.Share:.1%}", "#ffffff", 15, "middle", weight=600))
            body.append(_text(cx, bar_y + 44, label, "#ffffff", 12, "middle"))
            body.append(_text(cx, bar_y + bar_h + 22, f"{row.MeanMinPerDay:,.0f} min/day",
                              t["muted"], 11, "middle"))
        else:
            row_y = callout_rows[small]
            small += 1
            body.append(f'<path d="M{cx:.1f} {bar_y - 4:.1f} L{cx:.1f} {row_y:.1f} '
                        f'L{cx - 7:.1f} {row_y:.1f}" fill="none" stroke="{t["axis"]}" '
                        f'stroke-width="1"/>')
            body.append(_text(cx - 12, row_y + 4,
                              f"{label}  {row.Share:.1%}  ({row.MeanMinPerDay:,.0f} min/day)",
                              t["secondary"], 11, "end", weight=600))
        x += seg

    body.append(_text(pl, h - 18,
                      "Non-wear days (0 steps) are excluded. Leaving them in, as the raw file "
                      "invites, pushes the sedentary share to 81.3%.",
                      t["muted"], 10))
    body.append("</svg>")

    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"05-time-budget.{theme}.svg"
    path.write_text("\n".join(body), encoding="utf-8")
    print(f"  -> outputs/figures/{path.name}")


if __name__ == "__main__":
    for fn in (fig_daily_active_devices, fig_feature_adoption, fig_hourly_rhythm,
               fig_sedentary_bouts, fig_time_budget):
        both_themes(fn)
