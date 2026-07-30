"""Shared paths, loaders and a small dependency-free SVG chart builder.

The chart helpers emit static SVG so the figures render on GitHub with no
plotting dependency. Colours come from the reference data-viz palette:
categorical slots 1-2 (blue, orange) and the ordinal blue ramp, used unchanged
in both light and dark variants.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"

# Study window covered by the Fitbit export.
STUDY_START = pd.Timestamp("2016-04-12")
STUDY_END = pd.Timestamp("2016-05-12")

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------

_DATE = "%m/%d/%Y"
_DATETIME = "%m/%d/%Y %I:%M:%S %p"


def daily_activity() -> pd.DataFrame:
    df = pd.read_csv(DATA / "daily" / "dailyActivity_merged.csv")
    df["Date"] = pd.to_datetime(df["ActivityDate"], format=_DATE)
    df["DayOfWeek"] = df["Date"].dt.day_name()
    # A day with zero steps is a non-wear day, not a perfectly sedentary one.
    df["Worn"] = df["TotalSteps"] > 0
    df["ActiveMinutes"] = (
        df["VeryActiveMinutes"] + df["FairlyActiveMinutes"] + df["LightlyActiveMinutes"]
    )
    df["MVPAMinutes"] = df["VeryActiveMinutes"] + df["FairlyActiveMinutes"]
    return df


def sleep_day() -> pd.DataFrame:
    df = pd.read_csv(DATA / "daily" / "sleepDay_merged.csv")
    df["Date"] = pd.to_datetime(df["SleepDay"], format=_DATETIME).dt.normalize()
    df = df.drop_duplicates()  # 3 exact duplicate rows ship in the raw file
    df["SleepEfficiency"] = df["TotalMinutesAsleep"] / df["TotalTimeInBed"]
    df["AwakeInBed"] = df["TotalTimeInBed"] - df["TotalMinutesAsleep"]
    return df


def weight_log() -> pd.DataFrame:
    df = pd.read_csv(DATA / "logs" / "weightLogInfo_merged.csv")
    df["Date"] = pd.to_datetime(df["Date"], format=_DATETIME)
    return df


def hourly(metric: str) -> pd.DataFrame:
    """metric: 'Steps' | 'Intensities' | 'Calories'."""
    df = pd.read_csv(DATA / "hourly" / f"hourly{metric}_merged.csv")
    df["Timestamp"] = pd.to_datetime(df["ActivityHour"], format=_DATETIME)
    df["Hour"] = df["Timestamp"].dt.hour
    df["DayOfWeek"] = df["Timestamp"].dt.day_name()
    df["IsWeekend"] = df["Timestamp"].dt.dayofweek >= 5
    return df


def minute_intensities() -> pd.DataFrame:
    """~1.3M rows; used only for the sedentary-bout analysis."""
    df = pd.read_csv(DATA / "minute" / "minuteIntensitiesNarrow_merged.csv")
    df["Timestamp"] = pd.to_datetime(df["ActivityMinute"], format=_DATETIME)
    return df


def heartrate() -> pd.DataFrame:
    """~2.5M rows, 5-second resolution."""
    df = pd.read_csv(DATA / "seconds" / "heartrate_seconds_merged.csv")
    df["Timestamp"] = pd.to_datetime(df["Time"], format=_DATETIME)
    return df


def save_table(df: pd.DataFrame, name: str, index: bool = True) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{name}.csv", index=index)
    print(f"  -> outputs/tables/{name}.csv")


# --------------------------------------------------------------------------
# SVG chart builder
# --------------------------------------------------------------------------

THEMES = {
    "light": dict(
        surface="#fcfcfb", primary="#0b0b0b", secondary="#52514e", muted="#898781",
        grid="#e1e0d9", axis="#c3c2b7",
        series=["#2a78d6", "#eb6834"],
        ordinal=["#86b6ef", "#5598e7", "#2a78d6", "#184f95"],
    ),
    "dark": dict(
        surface="#1a1a19", primary="#ffffff", secondary="#c3c2b7", muted="#898781",
        grid="#2c2c2a", axis="#383835",
        series=["#3987e5", "#d95926"],
        ordinal=["#cde2fb", "#86b6ef", "#3987e5", "#184f95"],
    ),
}

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def _esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def _text(x, y, s, fill, size=12, anchor="start", weight=400, tabular=False):
    extra = ' style="font-variant-numeric:tabular-nums"' if tabular else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-size="{size}" '
        f'font-family=\'{FONT}\' font-weight="{weight}" text-anchor="{anchor}"{extra}>'
        f"{_esc(s)}</text>"
    )


def _nice_ticks(vmax: float, count: int = 4) -> list[float]:
    """Round tick steps covering 0..vmax."""
    if vmax <= 0:
        return [0.0]
    raw = vmax / count
    mag = 10 ** (len(str(int(raw))) - 1) if raw >= 1 else 0.1
    for mult in (1, 2, 2.5, 5, 10):
        step = mag * mult
        if step * count >= vmax:
            break
    return [step * i for i in range(count + 1)]


class Chart:
    """Minimal SVG canvas with a linear y-scale and a categorical/linear x-scale."""

    def __init__(self, theme: str, title: str, subtitle: str = "",
                 width: int = 900, height: int = 470,
                 pad=(64, 28, 62, 74)):  # top, right, bottom, left
        self.t = THEMES[theme]
        self.theme = theme
        self.w, self.h = width, height
        self.pt, self.pr, self.pb, self.pl = pad
        self.title, self.subtitle = title, subtitle
        self.body: list[str] = []
        self.plot_w = width - self.pl - self.pr
        self.plot_h = height - self.pt - self.pb

    # -- scales -----------------------------------------------------------
    def set_y(self, vmax: float, ticks: list[float] | None = None,
              fmt=lambda v: f"{v:,.0f}") -> None:
        self.yticks = ticks if ticks is not None else _nice_ticks(vmax)
        self.ymax = max(self.yticks[-1], vmax)
        self.yfmt = fmt

    def y(self, v: float) -> float:
        return self.pt + self.plot_h * (1 - v / self.ymax)

    # -- chrome -----------------------------------------------------------
    def gridlines(self, y_label: str = "") -> None:
        for v in self.yticks:
            yy = self.y(v)
            colour = self.t["axis"] if v == 0 else self.t["grid"]
            self.body.append(
                f'<line x1="{self.pl}" y1="{yy:.1f}" x2="{self.pl + self.plot_w}" '
                f'y2="{yy:.1f}" stroke="{colour}" stroke-width="1"/>'
            )
            self.body.append(
                _text(self.pl - 12, yy + 4, self.yfmt(v), self.t["muted"], 11,
                      "end", tabular=True)
            )
        if y_label:
            cy = self.pt + self.plot_h / 2
            self.body.append(
                f'<text transform="rotate(-90 {self.pl - 52} {cy:.1f})" '
                f'x="{self.pl - 52}" y="{cy:.1f}" fill="{self.t["muted"]}" '
                f'font-size="11" font-family=\'{FONT}\' text-anchor="middle">'
                f"{_esc(y_label)}</text>"
            )

    def x_labels(self, positions: list[float], labels: list[str], rotate: int = 0) -> None:
        yy = self.pt + self.plot_h + 20
        for px, lab in zip(positions, labels):
            if lab == "":
                continue
            if rotate:
                self.body.append(
                    f'<text transform="rotate({rotate} {px:.1f} {yy:.1f})" x="{px:.1f}" '
                    f'y="{yy:.1f}" fill="{self.t["muted"]}" font-size="11" '
                    f'font-family=\'{FONT}\' text-anchor="end">{_esc(lab)}</text>'
                )
            else:
                self.body.append(_text(px, yy, lab, self.t["muted"], 11, "middle"))

    def x_axis_title(self, label: str) -> None:
        self.body.append(
            _text(self.pl + self.plot_w / 2, self.h - 22, label, self.t["muted"], 11, "middle")
        )

    def legend(self, entries: list[tuple[str, str]]) -> None:
        """entries: [(label, colour)] — always drawn for >= 2 series."""
        x = self.pl
        y = self.pt - 16
        for label, colour in entries:
            self.body.append(
                f'<rect x="{x:.1f}" y="{y - 8:.1f}" width="10" height="10" rx="2" fill="{colour}"/>'
            )
            self.body.append(_text(x + 16, y + 1, label, self.t["secondary"], 12))
            x += 20 + 7.4 * len(label)

    def note(self, text: str) -> None:
        self.body.append(_text(self.pl, self.h - 6, text, self.t["muted"], 10))

    # -- marks ------------------------------------------------------------
    def line(self, pts: list[tuple[float, float]], colour: str, markers: bool = True) -> None:
        d = " ".join(
            f"{'M' if i == 0 else 'L'}{x:.1f} {self.y(v):.1f}" for i, (x, v) in enumerate(pts)
        )
        self.body.append(
            f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )
        if markers:
            for x, v in pts:
                self.body.append(
                    f'<circle cx="{x:.1f}" cy="{self.y(v):.1f}" r="4" fill="{colour}" '
                    f'stroke="{self.t["surface"]}" stroke-width="2"/>'
                )

    def vbar(self, x: float, width: float, value: float, colour: str, r: float = 4) -> None:
        """Vertical bar anchored to the baseline, rounded on the value end only."""
        y0, y1 = self.y(0), self.y(value)
        h = max(y0 - y1, 0.1)
        r = min(r, width / 2, h)
        self.body.append(
            f'<path d="M{x:.1f} {y0:.1f} L{x:.1f} {y1 + r:.1f} '
            f'Q{x:.1f} {y1:.1f} {x + r:.1f} {y1:.1f} L{x + width - r:.1f} {y1:.1f} '
            f'Q{x + width:.1f} {y1:.1f} {x + width:.1f} {y1 + r:.1f} '
            f'L{x + width:.1f} {y0:.1f} Z" fill="{colour}"/>'
        )

    def value_label(self, x: float, value: float, text: str, dy: float = -10) -> None:
        self.body.append(
            _text(x, self.y(value) + dy, text, self.t["secondary"], 11, "middle",
                  weight=600, tabular=True)
        )

    def point_label(self, x: float, value: float, text: str, anchor="start", dx=8, dy=4) -> None:
        self.body.append(
            _text(x + dx, self.y(value) + dy, text, self.t["secondary"], 11, anchor,
                  weight=600, tabular=True)
        )

    # -- output -----------------------------------------------------------
    def render(self) -> str:
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
            f'width="{self.w}" height="{self.h}" role="img" '
            f'aria-label="{_esc(self.title)}">',
            f'<rect width="{self.w}" height="{self.h}" fill="{self.t["surface"]}"/>',
            _text(self.pl - 46, 30, self.title, self.t["primary"], 16, weight=600),
        ]
        if self.subtitle:
            head.append(_text(self.pl - 46, 48, self.subtitle, self.t["secondary"], 12))
        return "\n".join(head + self.body + ["</svg>"])

    def save(self, stem: str) -> None:
        FIGURES.mkdir(parents=True, exist_ok=True)
        path = FIGURES / f"{stem}.{self.theme}.svg"
        path.write_text(self.render(), encoding="utf-8")
        print(f"  -> outputs/figures/{path.name}")


def both_themes(build) -> None:
    """Call `build(theme)` once per theme so every figure ships light and dark."""
    for theme in ("light", "dark"):
        build(theme)
