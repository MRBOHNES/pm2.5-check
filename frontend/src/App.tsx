import { useState } from "react";
import { fetchCities, fetchPeak } from "./api";
import { Header } from "./components/Header";
import { PeakCard } from "./components/PeakCard";
import { slug } from "./format";
import { useAsync } from "./useAsync";

const DAYS = 30; // length of the window every section looks at

export default function App() {
  const [city, setCity] = useState("delhi");
  const [attempt, setAttempt] = useState(0); // bumped by "Try again" to re-run the request
  const cities = useAsync(fetchCities, "cities");
  const peak = useAsync((signal) => fetchPeak(city, DAYS, signal), `${city}:${attempt}`);

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
    </>
  );
}
