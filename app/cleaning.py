"""Turn API responses into tidy DataFrames (Asia/Kolkata, deduped, daily means)."""

import pandas as pd

from app.models import OpenAQHour, OpenMeteoLocation

TZ = "Asia/Kolkata"
MAX_PM25 = 1000.0  # above this a reading is treated as a sensor fault
MIN_HOURS_PER_DAY = 18  # 75% hourly coverage needed for a daily mean


def ist_today() -> pd.Timestamp:
    """Today's date in IST as a naive midnight timestamp (same form as daily_mean's `date`)."""
    return pd.Timestamp.now(tz=TZ).tz_localize(None).normalize()


def open_meteo_to_frame(loc: OpenMeteoLocation) -> pd.DataFrame:
    """Hourly modelled PM2.5 with tz-aware timestamps."""
    df = pd.DataFrame({"timestamp": loc.hourly.time, "pm25": loc.hourly.pm2_5})
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(TZ)
    df["pm25"] = df["pm25"].astype(float)
    return df


def to_kolkata(ts: pd.Series) -> pd.Series:
    """Parse timestamps that carry an offset (e.g. UTC) and convert to IST."""
    return pd.to_datetime(ts, utc=True).dt.tz_convert(TZ)


def clean_pm25(df: pd.DataFrame, key: list[str] | None = None) -> pd.DataFrame:
    """Drop duplicate (key, timestamp) rows; blank out negative or impossible values.

    Bad values become NaN rather than being dropped, so a gap stays a gap.
    No interpolation: filling long gaps would invent data.
    """
    key = (key or []) + ["timestamp"]
    out = df.drop_duplicates(subset=key, keep="first").copy()
    bad = (out["pm25"] < 0) | (out["pm25"] > MAX_PM25)
    out.loc[bad, "pm25"] = float("nan")
    return out.sort_values(key).reset_index(drop=True)


def daily_mean(
    df: pd.DataFrame, min_hours: int = MIN_HOURS_PER_DAY, group: str | None = None
) -> pd.DataFrame:
    """Mean per local calendar day; NaN when fewer than `min_hours` valid readings."""
    day = df["timestamp"].dt.tz_localize(None).dt.normalize().rename("date")
    keys = [df[group], day] if group else [day]
    g = df.groupby(keys)["pm25"]
    out = pd.DataFrame({"pm25": g.mean(), "hours": g.count()})
    out.loc[out["hours"] < min_hours, "pm25"] = float("nan")
    return out.reset_index()


def modelled_daily(locations: dict[str, OpenMeteoLocation]) -> pd.DataFrame:
    """Daily modelled PM2.5 for every city: columns city, date, pm25, hours."""
    parts = []
    for city, loc in locations.items():
        hourly = clean_pm25(open_meteo_to_frame(loc))
        parts.append(daily_mean(hourly).assign(city=city))
    return pd.concat(parts, ignore_index=True)[["city", "date", "pm25", "hours"]]


MIN_COVERAGE = 75.0  # drop hours where under 75% of expected readings arrived


def openaq_to_frame(station: str, hours: list[OpenAQHour]) -> pd.DataFrame:
    """Hourly measured PM2.5 for one station; low-coverage hours become NaN."""
    df = pd.DataFrame(
        {
            "station": station,
            "timestamp": to_kolkata(pd.Series([h.period.datetimeFrom.utc for h in hours], dtype="object")),
            "pm25": [h.value for h in hours],
            "coverage": [h.coverage.percentComplete for h in hours],
        }
    )
    df.loc[df["coverage"] < MIN_COVERAGE, "pm25"] = float("nan")
    return df


def measured_daily(stations: dict[str, list[OpenAQHour]]) -> pd.DataFrame:
    """Daily measured PM2.5: per-station daily means, then the mean across stations.

    Returns date, pm25 (station mean), stations (how many stations had a valid day).
    """
    frames = [clean_pm25(openaq_to_frame(name, hrs), key=["station"]) for name, hrs in stations.items()]
    per_station = daily_mean(pd.concat(frames, ignore_index=True), group="station")
    g = per_station.groupby("date")["pm25"]
    return pd.DataFrame({"pm25": g.mean(), "stations": g.count()}).reset_index()
