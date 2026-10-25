import { CATEGORIES } from "../categories";
import { formatDay, slug } from "../format";
import type { Category, SeriesResponse } from "../types";

interface Props {
  data: SeriesResponse;
  peak: { date: string; category: Category } | null;
}

/** Six CPCB cards: range, colour and how many days the city spent in each category. */
export function CategoryCards({ data, peak }: Props) {
  const latest = data.latest_day;
  return (
    <ul className="cards" aria-label="Days in each CPCB category">
      {CATEGORIES.map(({ label, range }) => {
        const tags = [
          latest?.category === label ? `Latest day · ${formatDay(latest.date)}` : null,
          peak?.category === label ? `Peak day · ${formatDay(peak.date)}` : null,
        ].filter((t): t is string => t !== null);
        const days = data.category_counts[label];
        return (
          <li key={label} className={`card cat aqi-${slug(label)}${tags.length ? " cat--marked" : ""}`}>
            <span className="badge">{label}</span>
            <p className="small muted">{range} µg/m³</p>
            <p className="h2">{days} <span className="small muted">{days === 1 ? "day" : "days"}</span></p>
            {tags.map((t) => <p key={t} className="tag small">{t}</p>)}
          </li>
        );
      })}
    </ul>
  );
}
