import { CartesianGrid, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { dayBand, gapDays, toChartData, xTicks } from "../chartData";
import { formatDay } from "../format";
import type { Peak, SeriesResponse } from "../types";

const tick = { fill: "var(--muted)", fontSize: 12 };
const dayLabel = (t: number) => formatDay(new Date(t).toISOString().slice(0, 10));

interface LabelBox { x: number; y: number; width: number }

/** Peak label drawn beside the (narrow) band, on whichever side has room. */
function peakLabel(text: string, onRight: boolean) {
  return function PeakLabel({ viewBox }: { viewBox?: LabelBox }) {
    if (!viewBox) return null;
    const x = onRight ? viewBox.x + viewBox.width + 6 : viewBox.x - 6;
    return (
      <text x={x} y={viewBox.y + 14} textAnchor={onRight ? "start" : "end"}
            fill="var(--text)" fontSize={12} fontWeight={600}>{text}</text>
    );
  };
}

interface Props {
  data: SeriesResponse;
  peak: Peak | null; // the peak date comes from /peak, never hard-coded here
}

/** Modelled (dashed) vs measured (solid) daily PM2.5, with the peak day and the India standard. */
export function ModelVsMeasuredChart({ data, peak }: Props) {
  const points = toChartData(data.series);
  const hasMeasured = data.source === "measured";
  const gaps = hasMeasured ? gapDays(data.series) : [];
  const [peakFrom, peakTo] = peak ? dayBand(peak.date) : [0, 0];
  const peakIndex = peak ? points.findIndex((p) => p.date === peak.date) : -1;
  const onRight = peakIndex >= 0 && peakIndex < points.length / 2; // peak in the left half: write to its right
  return (
    <figure className="chart" aria-label="Daily PM2.5, modelled and measured">
      <ul className="legend small">
        {hasMeasured && <li><svg width="28" height="8" aria-hidden><line x1="0" y1="4" x2="28" y2="4" stroke="var(--line-measured)" strokeWidth="2" /></svg>Measured (OpenAQ stations)</li>}
        <li><svg width="28" height="8" aria-hidden><line x1="0" y1="4" x2="28" y2="4" stroke="var(--line-modelled)" strokeWidth="2" strokeDasharray="6 4" /></svg>Modelled (Open-Meteo / CAMS)</li>
        <li><svg width="28" height="8" aria-hidden><line x1="0" y1="4" x2="28" y2="4" stroke="var(--text)" strokeOpacity="0.6" strokeWidth="2" strokeDasharray="2 3" /></svg>India 24-hr standard ({data.standard} µg/m³)</li>
      </ul>
      <div className="chart__plot">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="t" type="number" scale="time" domain={["dataMin - 43200000", "dataMax + 43200000"]}
                   ticks={xTicks(points)} tickFormatter={dayLabel} tick={tick} stroke="var(--border)"
                   label={{ value: "Day (IST)", position: "insideBottom", offset: -4, fill: "var(--muted)", fontSize: 12 }} />
            <YAxis tick={tick} stroke="var(--border)" width={52}
                   label={{ value: "PM2.5 (µg/m³)", angle: -90, position: "insideLeft", fill: "var(--muted)", fontSize: 12 }} />
            {gaps.map((d) => {
              const [a, b] = dayBand(d);
              return <ReferenceArea key={d} x1={a} x2={b} fill="var(--gap-fill)" stroke="none" ifOverflow="hidden" />;
            })}
            {peak && (
              <ReferenceArea x1={peakFrom} x2={peakTo} fill="var(--peak-band)" stroke="none" ifOverflow="hidden"
                             label={peakLabel(`Peak: ${peak.value.toFixed(1)} µg/m³ on ${formatDay(peak.date)}`, onRight)} />
            )}
            <ReferenceLine y={data.standard} stroke="var(--text)" strokeDasharray="2 3" strokeOpacity={0.6} />
            <Tooltip labelFormatter={(t) => dayLabel(Number(t))} formatter={(v) => `${v} µg/m³`}
                     contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8 }} />
            {hasMeasured && <Line type="monotone" dataKey="measured" name="Measured" stroke="var(--line-measured)"
                                  strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />}
            <Line type="monotone" dataKey="modelled" name="Modelled" stroke="var(--line-modelled)"
                  strokeWidth={2} strokeDasharray="6 4" dot={false} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <figcaption className="small muted">
        {hasMeasured
          ? "Solid = measured by stations, dashed = modelled. Shaded days have no station data."
          : "No station data for this city; showing the modelled values only."}
      </figcaption>
    </figure>
  );
}
