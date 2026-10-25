import type { Category } from "./types";

/** CPCB National AQI bands for PM2.5 (24-hour mean, ug/m3). */
export const CATEGORIES: { label: Category; range: string }[] = [
  { label: "Good", range: "0–30" },
  { label: "Satisfactory", range: "31–60" },
  { label: "Moderate", range: "61–90" },
  { label: "Poor", range: "91–120" },
  { label: "Very Poor", range: "121–250" },
  { label: "Severe", range: "Above 250" },
];
