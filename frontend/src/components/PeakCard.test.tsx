import { render, screen } from "@testing-library/react";
import type { PeakResponse } from "../types";
import { PeakCard } from "./PeakCard";

const measured: PeakResponse = {
  city: "delhi", standard: 60, window_days: 30, source: "measured", days_compared: 27,
  peak: { date: "2026-10-21", value: 149.6, measured: 149.6, modelled: 91.8, difference: -57.8,
          category: "Very Poor", ratio_to_standard: 2.5 },
};

test("measured peak shows value, badge, ratio and the model's miss", () => {
  render(<PeakCard data={measured} />);
  expect(screen.getByText("Peak day · last 30 days")).toBeInTheDocument();
  expect(screen.getByText("149.6")).toBeInTheDocument();
  expect(screen.getByText("Very Poor")).toHaveClass("aqi-very-poor");
  expect(screen.getByText(/21 Oct: 2\.5× India's 24-hour standard\./)).toBeInTheDocument();
  expect(screen.getByText(/The model estimated 91\.8 µg\/m³ that day, off by 57\.8 µg\/m³ \(too low\)/)).toBeInTheDocument();
});

test("modelled peak says there is no station data", () => {
  const modelled: PeakResponse = {
    ...measured, source: "modelled",
    peak: { ...measured.peak!, measured: null, difference: null, category: "Poor", value: 95, ratio_to_standard: 1.6 },
  };
  render(<PeakCard data={modelled} />);
  expect(screen.getByText("No station data; modelled estimate.")).toBeInTheDocument();
  expect(screen.queryByText(/The model estimated/)).not.toBeInTheDocument();
});

test("empty state when there is no peak", () => {
  render(<PeakCard data={{ ...measured, peak: null, source: null, days_compared: 0, reason: "no valid daily PM2.5 values in the last 30 days" }} />);
  expect(screen.getByText("No valid daily readings")).toBeInTheDocument();
  expect(screen.getByText(/last 30 days/, { selector: "p.muted" })).toBeInTheDocument();
});
