"""NumPy / pandas analysis: AQI categories, model-vs-measured stats, city comparison."""
import numpy as np
import pandas as pd

# CPCB National AQI, PM2.5 24-h bands (ug/m3). Upper bound of each band, inclusive.
AQI_UPPER = [30, 60, 90, 120, 250]
AQI_LABELS = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]


def aqi_category(pm25) -> np.ndarray:
    """Category per value. 30.5 is above Good's 30 so it is Satisfactory; NaN stays NaN."""
    values = np.asarray(pm25, dtype=float)
    conds = [values <= u for u in AQI_UPPER]
    out = np.select(conds, AQI_LABELS[:-1], default=AQI_LABELS[-1]).astype(object)
    out[np.isnan(values)] = None
    return out


def _paired(a, b) -> tuple[np.ndarray, np.ndarray]:
    """Drop positions where either series is NaN."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    ok = ~(np.isnan(a) | np.isnan(b))
    return a[ok], b[ok]


def mae(modelled, measured) -> float:
    """Mean absolute error over days present in both."""
    m, o = _paired(modelled, measured)
    return float(np.mean(np.abs(m - o)))


def correlation(modelled, measured) -> float:
    """Pearson r over days present in both (needs 2+ days with variation)."""
    m, o = _paired(modelled, measured)
    return float(np.corrcoef(m, o)[0, 1])


def zscore_outliers(values, threshold: float = 2.0) -> np.ndarray:
    """Boolean mask: |z| > threshold. NaN is never an outlier."""
    v = np.asarray(values, dtype=float)
    std = np.nanstd(v)
    if std == 0 or np.isnan(std):
        return np.zeros(v.shape, dtype=bool)
    z = (v - np.nanmean(v)) / std
    return np.nan_to_num(np.abs(z), nan=0.0) > threshold


def compare_model_measured(daily: pd.DataFrame) -> dict:
    """daily has columns date, modelled, measured. Returns MAE, r, bias, outlier days."""
    d = daily.dropna(subset=["modelled", "measured"]).copy()
    diff = d["modelled"] - d["measured"]
    d["outlier"] = zscore_outliers(diff.to_numpy())
    return {
        "days": int(len(d)),
        "mae": mae(d["modelled"], d["measured"]),
        "correlation": correlation(d["modelled"], d["measured"]) if len(d) > 1 else None,
        "bias": float(diff.mean()),  # positive = model reads higher than stations
        "outlier_dates": [str(x.date()) for x in d.loc[d["outlier"], "date"]],
    }


def city_comparison(daily: pd.DataFrame) -> pd.DataFrame:
    """daily has city, date, pm25. One row per city: mean and days in each category."""
    d = daily.dropna(subset=["pm25"]).copy()
    d["category"] = aqi_category(d["pm25"])
    counts = d.pivot_table(index="city", columns="category", values="pm25",
                           aggfunc="count", fill_value=0)
    counts = counts.reindex(columns=AQI_LABELS, fill_value=0)
    out = d.groupby("city")["pm25"].agg(mean_pm25="mean", days="count")
    return out.join(counts).reset_index()


def model_vs_measured(modelled: pd.DataFrame, measured: pd.DataFrame) -> pd.DataFrame:
    """Join daily modelled and measured PM2.5 on date (columns date, modelled, measured)."""
    m = modelled[["date", "pm25"]].rename(columns={"pm25": "modelled"})
    o = measured[["date", "pm25"]].rename(columns={"pm25": "measured"})
    return m.merge(o, on="date", how="inner")
