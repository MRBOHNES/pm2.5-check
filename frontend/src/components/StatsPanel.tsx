import type { Stats } from "../types";

/** Mean absolute error and correlation of the model against the stations. */
export function StatsPanel({ stats }: { stats: Stats | null }) {
  if (!stats) {
    return (
      <aside className="card stats" aria-label="Model accuracy">
        <p className="eyebrow">Model accuracy</p>
        <p className="h3">n/a</p>
        <p className="small muted">No station data for this city, so the model can&apos;t be checked against measurements.</p>
      </aside>
    );
  }
  return (
    <aside className="card stats" aria-label="Model accuracy">
      <p className="eyebrow">Model accuracy · {stats.days} days compared</p>
      <dl>
        <div>
          <dt className="small muted">Mean absolute error</dt>
          <dd className="h2">{stats.mae.toFixed(1)} <span className="small muted">µg/m³</span></dd>
        </div>
        <div>
          <dt className="small muted">Correlation (r)</dt>
          <dd className="h2">{stats.correlation === null ? "n/a" : stats.correlation.toFixed(2)}</dd>
        </div>
        <div>
          <dt className="small muted">Average bias</dt>
          <dd className="h3">
            {Math.abs(stats.bias).toFixed(1)} µg/m³ {stats.bias < 0 ? "too low" : "too high"}
          </dd>
        </div>
      </dl>
    </aside>
  );
}
