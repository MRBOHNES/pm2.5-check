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
