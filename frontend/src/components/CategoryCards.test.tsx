import { render, screen, within } from "@testing-library/react";
import type { SeriesResponse } from "../types";
import { CategoryCards } from "./CategoryCards";

const data: SeriesResponse = {
  city: "delhi", window_days: 30, standard: 60, source: "measured", series: [], stats: null,
  category_counts: { Good: 0, Satisfactory: 3, Moderate: 8, Poor: 10, "Very Poor": 6, Severe: 0 },
  latest_day: { date: "2026-10-23", value: 110, category: "Poor" },
};

test("shows six cards with range and day counts", () => {
  render(<CategoryCards data={data} peak={{ date: "2026-10-21", category: "Very Poor" }} />);
  const cards = screen.getAllByRole("listitem");
  expect(cards).toHaveLength(6);
  expect(within(cards[0]).getByText("0–30 µg/m³")).toBeInTheDocument();
  expect(within(cards[2]).getByText("8")).toBeInTheDocument();
  expect(within(cards[5]).getByText("Above 250 µg/m³")).toBeInTheDocument();
});

test("marks the latest-day and peak-day categories in text", () => {
  render(<CategoryCards data={data} peak={{ date: "2026-10-21", category: "Very Poor" }} />);
  const cards = screen.getAllByRole("listitem");
  expect(within(cards[3]).getByText("Latest day · 23 Oct")).toBeInTheDocument();
  expect(within(cards[4]).getByText("Peak day · 21 Oct")).toBeInTheDocument();
  expect(within(cards[0]).queryByText(/day ·/)).not.toBeInTheDocument();
});

test("one card can carry both marks and singular wording is used", () => {
  const one = { ...data, category_counts: { ...data.category_counts, Poor: 1 } };
  render(<CategoryCards data={one} peak={{ date: "2026-10-22", category: "Poor" }} />);
  const poor = screen.getAllByRole("listitem")[3];
  expect(within(poor).getByText("Latest day · 23 Oct")).toBeInTheDocument();
  expect(within(poor).getByText("Peak day · 22 Oct")).toBeInTheDocument();
  expect(within(poor).getByText("day")).toBeInTheDocument();
});
