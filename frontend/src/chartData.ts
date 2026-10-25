import type { SeriesPoint } from "./types";

const DAY_MS = 24 * 60 * 60 * 1000;

export interface ChartPoint extends SeriesPoint {
  t: number; // midday UTC of the IST calendar day, so a day's band is [t - 12h, t + 12h]
}

/** Add a numeric time to each day so the chart can use a real time axis and day bands. */
export function toChartData(series: SeriesPoint[]): ChartPoint[] {
  return series.map((p) => ({ ...p, t: Date.parse(`${p.date}T12:00:00Z`) }));
}

/** The start and end of one day's shaded band on the time axis. */
export function dayBand(date: string): [number, number] {
  const mid = Date.parse(`${date}T12:00:00Z`);
  return [mid - DAY_MS / 2, mid + DAY_MS / 2];
}

/** Days with a modelled value but no station reading (only meaningful when stations exist). */
export function gapDays(series: SeriesPoint[]): string[] {
  return series.filter((p) => p.measured === null && p.modelled !== null).map((p) => p.date);
}

/** About six evenly spaced day ticks, so labels never crowd on a phone and no tick sits on the axis edge. */
export function xTicks(points: ChartPoint[], target = 6): number[] {
  const step = Math.max(1, Math.ceil(points.length / target));
  return points.filter((_, i) => i % step === 0).map((p) => p.t);
}
