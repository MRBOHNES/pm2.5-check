import { render, screen } from "@testing-library/react";
import { StatsPanel } from "./StatsPanel";

test("shows MAE, correlation and the direction of the bias", () => {
  render(<StatsPanel stats={{ days: 6, mae: 22, bias: -16, correlation: 0.22, outlier_dates: [] }} />);
  expect(screen.getByText(/6 days compared/)).toBeInTheDocument();
  expect(screen.getByText("22.0", { exact: false })).toBeInTheDocument();
  expect(screen.getByText("0.22")).toBeInTheDocument();
  expect(screen.getByText("16.0 µg/m³ too low")).toBeInTheDocument();
});

test("says n/a when there is no station data", () => {
  render(<StatsPanel stats={null} />);
  expect(screen.getByText("n/a")).toBeInTheDocument();
  expect(screen.getByText(/No station data/)).toBeInTheDocument();
});

test("null correlation (one day, or no variation) shows n/a", () => {
  render(<StatsPanel stats={{ days: 1, mae: 5, bias: 5, correlation: null, outlier_dates: [] }} />);
  expect(screen.getByText("n/a")).toBeInTheDocument();
});
