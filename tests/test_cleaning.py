import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.cleaning import clean_pm25, daily_mean, open_meteo_to_frame, to_kolkata
from app.models import OpenMeteoLocation

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
    df = _frame(["2026-01-01 00:00", "2026-01-01 00:00", "2026-01-01 01:00", "2026-01-01 02:00"],
                [10.0, 99.0, -5.0, 5000.0])
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
    vals[24 + 6:] = np.nan  # day 2 has only 6 valid hours
    out = daily_mean(_frame(times, vals))
    assert out["pm25"].iloc[0] == 10.0
    assert np.isnan(out["pm25"].iloc[1])
    assert out["hours"].tolist() == [24, 6]


def test_daily_mean_by_group():
    times = pd.date_range("2026-01-01", periods=24, freq="h")
    df = pd.concat([_frame(times, 10.0).assign(city="a"), _frame(times, 20.0).assign(city="b")])
    out = daily_mean(df, group="city")
    assert out.set_index("city")["pm25"].to_dict() == {"a": 10.0, "b": 20.0}
