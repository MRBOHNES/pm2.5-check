"""Matplotlib charts, saved to output/."""

import asyncio
from pathlib import Path

import httpx
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from app.analysis import AQI_LABELS, city_comparison, compare_model_measured, model_vs_measured  # noqa: E402  # noqa: E402
from app.cleaning import measured_daily, modelled_daily  # noqa: E402
from app.client import fetch_delhi_measured, fetch_open_meteo, window_utc  # noqa: E402

OUT = Path(__file__).parent.parent / "output"
BAND_COLOURS = ["#2e9e5b", "#9bc53d", "#f2c230", "#f08a24", "#d9482b", "#8b1e3f"]


def daily_trend_chart(daily, path: Path) -> None:
    """Daily modelled PM2.5 per city with the CPCB 'Poor' threshold marked."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for city, g in daily.groupby("city"):
        ax.plot(g["date"], g["pm25"], marker="o", label=city.title())
    ax.axhline(90, color="grey", linestyle="--", linewidth=1)
    ax.text(ax.get_xlim()[0], 92, "CPCB Moderate/Poor boundary (90)", fontsize=8, color="grey")
    ax.set(title="Daily mean PM2.5 (modelled, Open-Meteo/CAMS)", ylabel="PM2.5 (µg/m³)")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def category_chart(daily, path: Path) -> None:
    """Stacked bars: days per CPCB category for each city."""
    table = city_comparison(daily).set_index("city")[AQI_LABELS]
    ax = table.plot.bar(stacked=True, color=BAND_COLOURS, figsize=(8, 4.5), rot=0)
    ax.set(title="Days in each CPCB category (modelled PM2.5)", ylabel="Days", xlabel="")
    ax.figure.tight_layout()
    ax.figure.savefig(path, dpi=150)
    plt.close(ax.figure)


def model_vs_measured_chart(joined, stats: dict, path: Path) -> None:
    """Delhi daily modelled vs measured (station mean), with MAE and r in the title."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(joined["date"], joined["modelled"], marker="o", label="Modelled (Open-Meteo/CAMS)")
    ax.plot(joined["date"], joined["measured"], marker="s", label="Measured (mean of OpenAQ stations)")
    ax.set(
        title=f"Delhi daily PM2.5: MAE {stats['mae']:.0f} µg/m³, r = {stats['correlation']:.2f}, "
        f"bias {stats['bias']:+.0f} (n={stats['days']} days)",
        ylabel="PM2.5 (µg/m³)",
    )
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


async def main() -> None:
    OUT.mkdir(exist_ok=True)
    async with httpx.AsyncClient(timeout=10) as client:
        start, end = window_utc()
        locations, hours = await asyncio.gather(
            fetch_open_meteo(client), fetch_delhi_measured(client, start, end)
        )
    daily = modelled_daily(locations)
    joined = model_vs_measured(daily[daily["city"] == "delhi"], measured_daily(hours))
    stats = compare_model_measured(joined)
    model_vs_measured_chart(joined, stats, OUT / "delhi_model_vs_measured.png")
    print(joined.to_string(index=False))
    print(stats)
    daily_trend_chart(daily, OUT / "daily_trend_modelled.png")
    category_chart(daily, OUT / "category_days_modelled.png")
    print(city_comparison(daily).round(1).to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
