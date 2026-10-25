import { useState } from "react";
import { BASE, fetchCities, fetchPeak, fetchSeries } from "./api";
import { CategoryCards } from "./components/CategoryCards";
import { ErrorCard } from "./components/ErrorCard";
import { Header } from "./components/Header";
import { Limitations } from "./components/Limitations";
import { ModelVsMeasuredChart } from "./components/ModelVsMeasuredChart";
import { PeakCard } from "./components/PeakCard";
import { Skeleton } from "./components/Skeleton";
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

  const retry = () => setAttempt((n) => n + 1);
  const category = peak.status === "ok" ? peak.data.peak?.category : undefined;
  return (
    <>
      <Header cities={cities.status === "ok" ? cities.data : []} city={city} onCity={setCity} />
      <main className={`hero ${category ? `haze-${slug(category)}` : ""}`}>
        <div className="container">
          <h1 className="display hero__headline">Can you trust the free air-quality numbers for Delhi?</h1>
          {peak.status === "loading" && <Skeleton label="Loading peak day" />}
          {peak.status === "error" && (
            <ErrorCard title="Couldn't load the peak day" message={peak.error.message} onRetry={retry} />
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
          {series.status === "loading" && <Skeleton label="Loading chart" />}
          {series.status === "error" && (
            <ErrorCard title="Couldn't load the chart" message={series.error.message} onRetry={retry} />
          )}
          {series.status === "ok" && series.data.source === null && (
            <section className="card notice">
              <p className="h3">No daily values yet</p>
              <p className="muted">No day in the last {DAYS} days has enough readings to plot.</p>
            </section>
          )}
          {series.status === "ok" && series.data.source !== null && (
            <div className="chart-row">
              <ModelVsMeasuredChart data={series.data} peak={peak.status === "ok" ? peak.data.peak : null} />
              <StatsPanel stats={series.data.stats} />
            </div>
          )}
        </div>
      </section>
      {series.status === "ok" && series.data.source !== null && (
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
      <Limitations apiUrl={BASE} />
    </>
  );
}
