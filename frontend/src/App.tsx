import { useState } from "react";
import { fetchCities, fetchPeak, fetchSeries } from "./api";
import { CategoryCards } from "./components/CategoryCards";
import { Header } from "./components/Header";
import { ModelVsMeasuredChart } from "./components/ModelVsMeasuredChart";
import { PeakCard } from "./components/PeakCard";
import { StatsPanel } from "./components/StatsPanel";
import { slug } from "./format";
import { useAsync } from "./useAsync";

const DAYS = 30; // length of the window every section looks at

export default function App() {
  const [city, setCity] = useState("delhi");
  const [attempt, setAttempt] = useState(0); // bumped by "Try again" to re-run the request
  const cities = useAsync(fetchCities, "cities");
  const peak = useAsync((signal) => fetchPeak(city, DAYS, signal), `${city}:${attempt}`);

  const series = useAsync((signal) => fetchSeries(city, DAYS, signal), `${city}:${attempt}`);

  const category = peak.status === "ok" ? peak.data.peak?.category : undefined;
  return (
    <>
      <Header cities={cities.status === "ok" ? cities.data : []} city={city} onCity={setCity} />
      <main className={`hero ${category ? `haze-${slug(category)}` : ""}`}>
        <div className="container">
          <h1 className="display hero__headline">Can you trust the free air-quality numbers for Delhi?</h1>
          {peak.status === "loading" && <div className="skeleton" role="status" aria-label="Loading peak day" />}
          {peak.status === "error" && (
            <section className="card notice" role="alert">
              <p className="h3">Couldn&apos;t load the peak day</p>
              <p className="muted">{peak.error.message}.</p>
              <button className="btn" onClick={() => setAttempt((n) => n + 1)}>Try again</button>
            </section>
          )}
          {peak.status === "ok" && <PeakCard data={peak.data} />}
        </div>
      </main>
      <section className="section">
        <div className="container">
          <div className="section__head">
            <h2 className="h2">Model vs measured</h2>
            <p className="muted">Daily PM2.5 over the last {DAYS} days, with the peak day marked.</p>
          </div>
          {series.status === "loading" && <div className="skeleton" role="status" aria-label="Loading chart" />}
          {series.status === "error" && (
            <section className="card notice" role="alert">
              <p className="h3">Couldn&apos;t load the chart</p>
              <p className="muted">{series.error.message}.</p>
            </section>
          )}
          {series.status === "ok" && (
            <div className="chart-row">
              <ModelVsMeasuredChart data={series.data} peak={peak.status === "ok" ? peak.data.peak : null} />
              <StatsPanel stats={series.data.stats} />
            </div>
          )}
        </div>
      </section>
      {series.status === "ok" && (
        <section className="section">
          <div className="container">
            <div className="section__head">
              <h2 className="h2">Days in each CPCB category</h2>
              <p className="muted">
                Last {DAYS} days, from {series.data.source ?? "no"} daily means. CPCB bands for 24-hour PM2.5.
              </p>
            </div>
            <CategoryCards data={series.data} peak={peak.status === "ok" ? peak.data.peak : null} />
          </div>
        </section>
      )}
    </>
  );
}
