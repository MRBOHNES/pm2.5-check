/** Shapes of the backend's JSON responses (see app/main.py). */
export type Category = "Good" | "Satisfactory" | "Moderate" | "Poor" | "Very Poor" | "Severe";

export interface City {
  name: string;
  label: string;
  has_measured: boolean;
}

export interface Peak {
  date: string; // YYYY-MM-DD, an IST calendar day
  value: number; // ug/m3
  measured: number | null;
  modelled: number | null;
  difference: number | null; // modelled - measured; negative = model reads lower
  category: Category;
  ratio_to_standard: number;
}

export interface PeakResponse {
  city: string;
  standard: number;
  window_days: number;
  source: "measured" | "modelled" | null;
  days_compared: number;
  peak: Peak | null;
  reason?: string;
}

export interface SeriesPoint {
  date: string;
  modelled: number | null;
  measured: number | null;
}

export interface Stats {
  days: number;
  mae: number;
  bias: number; // modelled - measured, averaged; negative = model reads lower
  correlation: number | null;
  outlier_dates: string[];
}

export interface SeriesResponse {
  city: string;
  window_days: number;
  standard: number;
  source: "measured" | "modelled" | null;
  series: SeriesPoint[];
  stats: Stats | null; // null when there is no station data to compare with
  category_counts: Record<Category, number>;
  latest_day: { date: string; value: number; category: Category } | null;
}
