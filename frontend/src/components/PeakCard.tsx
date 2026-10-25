import { formatDay, slug } from "../format";
import type { PeakResponse } from "../types";

/** The highest daily PM2.5 in the window, with how far the model was off. */
export function PeakCard({ data }: { data: PeakResponse }) {
  const { peak } = data;
  const eyebrow = `Peak day · last ${data.window_days} days`;

  if (!peak) {
    return (
      <section className="card notice" aria-label="Peak day">
        <p className="eyebrow">{eyebrow}</p>
        <p className="h3">No valid daily readings</p>
        <p className="muted">{data.reason ?? "There is no data for this window."}</p>
      </section>
    );
  }

  const diff = peak.difference;
  return (
    <section className="card peak" aria-label="Peak day">
      <p className="eyebrow">{eyebrow}</p>
      <div className="peak__value">
        <p>
          <span className="big-number">{peak.value.toFixed(1)}</span>
          <span className="peak__unit">µg/m³</span>
        </p>
        <span className={`badge aqi-${slug(peak.category)}`}>{peak.category}</span>
      </div>
      <p className="h3">
        {formatDay(peak.date)}: {peak.ratio_to_standard.toFixed(1)}× India&apos;s 24-hour standard.
      </p>
      {data.source === "measured" && peak.modelled !== null && diff !== null ? (
        <p className="muted">
          The model estimated {peak.modelled.toFixed(1)} µg/m³ that day, off by{" "}
          {Math.abs(diff).toFixed(1)} µg/m³ ({diff < 0 ? "too low" : "too high"}).
        </p>
      ) : (
        <p className="muted">No station data; modelled estimate.</p>
      )}
    </section>
  );
}
