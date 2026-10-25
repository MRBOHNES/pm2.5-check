import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.cleaning import clean_pm25, daily_mean, ist_today, measured_daily, open_meteo_to_frame, to_kolkata
from app.models import OpenAQHour, OpenMeteoLocation

SAMPLE = Path(__file__).parent.parent / "samples" / "open_meteo.json"


def _frame(times, values):
    return pd.DataFrame({"timestamp": pd.to_datetime(times).tz_localize("Asia/Kolkata"), "pm25": values})


def test_open_meteo_frame_is_tz_aware():
    loc = OpenMeteoLocation.model_validate(json.loads(SAMPLE.read_text())[0])
    df = open_meteo_to_frame(loc)
    assert str(df["timestamp"].dt.tz) == "Asia/Kolkata"
    assert len(df) == 192


def test_to_kolkata_converts_utc():
    out = to_kolkata(pd.Series(["2026-01-01T00:00:00Z"]))
    assert out.iloc[0].hour == 5 and out.iloc[0].minute == 30


def test_clean_drops_duplicates_and_blanks_bad_values():
    df = _frame(
        ["2026-01-01 00:00", "2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 02:00"],
        [10.0, 99.0, -5.0, 5000.0],
    )
    out = clean_pm25(df)
    assert len(out) == 3
    assert out["pm25"].iloc[0] == 10.0  # first duplicate kept
    assert out["pm25"].iloc[1:].isna().all()


def test_clean_dedupes_per_station():
    df = _frame(["2026-01-01 00:00"] * 2, [1.0, 2.0])
    df["station"] = ["a", "b"]
    assert len(clean_pm25(df, key=["station"])) == 2


def test_daily_mean_needs_coverage():
    times = pd.date_range("2026-01-01", periods=48, freq="h")
    vals = np.full(48, 10.0)
    vals[24 + 6 :] = np.nan  # day 2 has only 6 valid hours
    out = daily_mean(_frame(times, vals))
    assert out["pm25"].iloc[0] == 10.0
    assert np.isnan(out["pm25"].iloc[1])
    assert out["hours"].tolist() == [24, 6]


def test_daily_mean_by_group():
    times = pd.date_range("2026-01-01", periods=24, freq="h")
    df = pd.concat([_frame(times, 10.0).assign(city="a"), _frame(times, 20.0).assign(city="b")])
    out = daily_mean(df, group="city")
    assert out.set_index("city")["pm25"].to_dict() == {"a": 10.0, "b": 20.0}


def _aq_hour(utc: str, value: float) -> OpenAQHour:
    """An OpenAQ hour that starts at the given UTC time (full coverage)."""
    t = {"utc": utc, "local": utc}
    return OpenAQHour.model_validate(
        {
            "value": value,
            "coverage": {"percentComplete": 100},
            "period": {"label": "1hour", "datetimeFrom": t, "datetimeTo": t},
        }
    )


def test_ist_day_boundary_for_measured_days():
    # IST day 2026-10-20: 00:00-22:00 IST on the hour (18:30Z the day before .. 16:30Z)
    day = [
        _aq_hour(f"2026-10-{19 + (h + 18) // 24:02d}T{(h + 18) % 24:02d}:30:00Z", 10.0) for h in range(0, 23)
    ]
    day.append(_aq_hour("2026-10-20T18:00:00Z", 10.0))  # 23:30 IST, still 20 Oct
    day.append(_aq_hour("2026-10-20T18:30:00Z", 500.0))  # 00:00 IST, already 21 Oct
    out = measured_daily({"a": day}).set_index("date")
    assert out.loc[pd.Timestamp("2026-10-20"), "pm25"] == 10.0
    assert np.isnan(out.loc[pd.Timestamp("2026-10-21"), "pm25"])  # 1 hour is below the 18-hour rule


def test_ist_today_is_midnight_and_naive():
    t = ist_today()
    assert t.tzinfo is None and t == t.normalize()
