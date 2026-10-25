import numpy as np
import pandas as pd
import pytest

from app.analysis import (
    aqi_category,
    category_counts,
    city_comparison,
    compare_model_measured,
    correlation,
    latest_day,
    mae,
    model_stats,
    peak_day,
    pick_source,
    zscore_outliers,
)


@pytest.mark.parametrize(
    "value,label",
    [
        (0, "Good"),
        (30, "Good"),
        (30.5, "Satisfactory"),
        (31, "Satisfactory"),
        (60, "Satisfactory"),
        (61, "Moderate"),
        (90, "Moderate"),
        (91, "Poor"),
        (120, "Poor"),
        (121, "Very Poor"),
        (250, "Very Poor"),
        (251, "Severe"),
        (900, "Severe"),
    ],
)
def test_aqi_edges(value, label):
    assert aqi_category([value])[0] == label


def test_aqi_nan_is_none_and_vectorised():
    out = aqi_category([10, np.nan, 300])
    assert list(out) == ["Good", None, "Severe"]


def test_mae_and_correlation_ignore_nan_pairs():
    m = [10, 20, 30, np.nan]
    o = [12, 18, 33, 99]
    assert mae(m, o) == pytest.approx((2 + 2 + 3) / 3)
    assert correlation(m, o) == pytest.approx(np.corrcoef([10, 20, 30], [12, 18, 33])[0, 1])


def test_perfect_correlation():
    assert correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)


def test_zscore_outliers():
    v = [10] * 20 + [100]
    mask = zscore_outliers(v)
    assert mask[-1] and mask.sum() == 1
    assert not zscore_outliers([5, 5, 5]).any()


def test_compare_model_measured():
    d = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=3),
            "modelled": [100.0, 110.0, np.nan],
            "measured": [90.0, 100.0, 50.0],
        }
    )
    r = compare_model_measured(d)
    assert r["days"] == 2 and r["mae"] == 10 and r["bias"] == 10


def test_city_comparison_counts():
    d = pd.DataFrame(
        {"city": ["a", "a", "b"], "date": pd.date_range("2026-01-01", periods=3), "pm25": [20.0, 300.0, 70.0]}
    )
    out = city_comparison(d).set_index("city")
    assert out.loc["a", "Good"] == 1 and out.loc["a", "Severe"] == 1
    assert out.loc["b", "Moderate"] == 1 and out.loc["b", "days"] == 1


def _daily(modelled, measured):
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=len(modelled)),
            "modelled": modelled,
            "measured": measured,
        }
    )


def test_peak_prefers_measured_and_reports_details():
    out = peak_day(_daily([50.0, 80.0, 300.0], [40.0, 126.0, 100.0]), days=3)
    assert out["source"] == "measured" and out["days_compared"] == 3
    assert out["peak"] == {
        "date": "2026-01-02",
        "value": 126.0,
        "measured": 126.0,
        "modelled": 80.0,
        "difference": -46.0,
        "category": "Very Poor",
        "ratio_to_standard": 2.1,
    }
    assert out["standard"] == 60 and out["window_days"] == 3


def test_peak_tie_goes_to_earliest_date():
    out = peak_day(_daily([0.0] * 3, [80.0, 120.0, 120.0]), days=3)
    assert out["peak"]["date"] == "2026-01-02"


def test_peak_ignores_nan_days():
    out = peak_day(_daily([1.0, 2.0, 3.0], [np.nan, 40.0, np.nan]), days=3)
    assert out["peak"]["date"] == "2026-01-02" and out["days_compared"] == 1


def test_peak_all_nan_is_null_with_reason():
    out = peak_day(_daily([np.nan, np.nan], [np.nan, np.nan]), days=30)
    assert out["peak"] is None and out["source"] is None
    assert "30 days" in out["reason"]


def test_peak_falls_back_to_modelled():
    out = peak_day(_daily([20.0, 95.0], [np.nan, np.nan]), days=2)
    assert out["source"] == "modelled"
    assert out["peak"]["value"] == 95.0 and out["peak"]["category"] == "Poor"
    assert out["peak"]["measured"] is None and out["peak"]["difference"] is None


def test_peak_excludes_today():
    d = _daily([10.0, 20.0, 999.0], [10.0, 20.0, 999.0])
    out = peak_day(d, days=3, today=pd.Timestamp("2026-01-03"))
    assert out["peak"]["date"] == "2026-01-02"


def test_category_counts_has_all_six_labels_and_skips_nan():
    out = category_counts([10, 30, 31, np.nan, 300])
    assert list(out) == ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
    assert out["Good"] == 2 and out["Satisfactory"] == 1 and out["Severe"] == 1
    assert sum(out.values()) == 4


def test_pick_source_and_latest_day():
    d = _daily([10.0, 20.0, 30.0], [5.0, 95.0, np.nan])
    assert pick_source(d) == "measured"
    assert latest_day(d, "measured") == {"date": "2026-01-02", "value": 95.0, "category": "Poor"}
    assert latest_day(d, "modelled")["date"] == "2026-01-03"
    assert latest_day(_daily([np.nan], [np.nan]), "modelled") is None


def test_model_stats_none_without_overlap_and_null_correlation_for_one_day():
    assert model_stats(_daily([10.0, 20.0], [np.nan, np.nan])) is None
    one = model_stats(_daily([10.0, 20.0], [np.nan, 25.0]))
    assert one["days"] == 1 and one["mae"] == 5.0 and one["correlation"] is None
    two = model_stats(_daily([10.0, 20.0, 30.0], [12.0, 18.0, 33.0]))
    assert two["days"] == 3 and two["correlation"] > 0.9
