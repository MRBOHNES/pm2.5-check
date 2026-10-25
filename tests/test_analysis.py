import numpy as np
import pandas as pd
import pytest

from app.analysis import (aqi_category, city_comparison, compare_model_measured,
                          correlation, mae, zscore_outliers)


@pytest.mark.parametrize("value,label", [
    (0, "Good"), (30, "Good"), (30.5, "Satisfactory"), (31, "Satisfactory"),
    (60, "Satisfactory"), (61, "Moderate"), (90, "Moderate"), (91, "Poor"),
    (120, "Poor"), (121, "Very Poor"), (250, "Very Poor"), (251, "Severe"),
    (900, "Severe"),
])
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
    d = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=3),
                      "modelled": [100.0, 110.0, np.nan], "measured": [90.0, 100.0, 50.0]})
    r = compare_model_measured(d)
    assert r["days"] == 2 and r["mae"] == 10 and r["bias"] == 10


def test_city_comparison_counts():
    d = pd.DataFrame({"city": ["a", "a", "b"], "date": pd.date_range("2026-01-01", periods=3),
                      "pm25": [20.0, 300.0, 70.0]})
    out = city_comparison(d).set_index("city")
    assert out.loc["a", "Good"] == 1 and out.loc["a", "Severe"] == 1
    assert out.loc["b", "Moderate"] == 1 and out.loc["b", "days"] == 1
