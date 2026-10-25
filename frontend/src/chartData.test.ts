import { dayBand, gapDays, toChartData, xTicks } from "./chartData";

const series = [
  { date: "2026-10-20", modelled: 50, measured: 60 },
  { date: "2026-10-21", modelled: 91.8, measured: null },
  { date: "2026-10-22", modelled: null, measured: null },
];

test("toChartData adds a midday-UTC time per day", () => {
  expect(toChartData(series)[0].t).toBe(Date.parse("2026-10-20T12:00:00Z"));
});

test("dayBand spans exactly one day around midday", () => {
  const [a, b] = dayBand("2026-10-21");
  expect(b - a).toBe(24 * 60 * 60 * 1000);
  expect(a).toBe(Date.parse("2026-10-21T00:00:00Z"));
});

test("gapDays lists days with a model value but no station reading", () => {
  expect(gapDays(series)).toEqual(["2026-10-21"]);
});

test("xTicks gives about six ticks, all on real days", () => {
  const points = toChartData(Array.from({ length: 30 }, (_, i) => ({
    date: `2026-09-${String(i + 1).padStart(2, "0")}`, modelled: 1, measured: 1 })));
  const ticks = xTicks(points);
  expect(ticks).toHaveLength(6);
  expect(ticks.every((t) => points.some((p) => p.t === t))).toBe(true);
  expect(xTicks([])).toEqual([]);
});
