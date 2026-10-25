import { render, screen, within } from "@testing-library/react";
import App from "./App";

const CITIES = [{ name: "delhi", label: "Delhi", has_measured: true }];
const PEAK = {
  city: "delhi", standard: 60, window_days: 30, source: "measured", days_compared: 27,
  peak: { date: "2026-10-21", value: 149.6, measured: 149.6, modelled: 91.8, difference: -57.8,
          category: "Very Poor", ratio_to_standard: 2.5 },
};

const SERIES = {
  city: "delhi", window_days: 30, standard: 60, source: "measured", stats: null,
  series: [{ date: "2026-10-20", modelled: 50, measured: 60 }],
  category_counts: { Good: 0, Satisfactory: 1, Moderate: 0, Poor: 0, "Very Poor": 0, Severe: 0 },
  latest_day: { date: "2026-10-20", value: 60, category: "Satisfactory" },
};

function stubFetch(peakStatus = 200) {
  vi.stubGlobal("fetch", vi.fn(async (url: URL) => {
    const body = url.pathname === "/cities" ? CITIES : url.pathname === "/series" ? SERIES : PEAK;
    const ok = url.pathname === "/cities" || peakStatus === 200;
    return { ok, status: ok ? 200 : peakStatus, json: async () => body } as Response;
  }));
}
afterEach(() => vi.unstubAllGlobals());

test("shows title, tagline, headline above the peak card, and the city list", async () => {
  stubFetch();
  render(<App />);
  expect(screen.getByText("PM2.5 Check")).toBeInTheDocument();
  expect(screen.getByText("Modelled vs measured PM2.5 in Delhi")).toBeInTheDocument();
  const h1 = screen.getByRole("heading", { level: 1 });
  expect(h1).toHaveTextContent("Can you trust the free air-quality numbers for Delhi?");
  const card = await screen.findByLabelText("Peak day");
  expect(h1.compareDocumentPosition(card) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(await screen.findByRole("option", { name: "Delhi" })).toBeInTheDocument();
});

test("shows an error with a retry button when the backend fails", async () => {
  stubFetch(502);
  render(<App />);
  const alerts = await screen.findAllByRole("alert"); // peak card and chart each report the failure
  expect(alerts[0]).toHaveTextContent("The server answered 502");
  expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
});

test("shows the category cards once the series has loaded", async () => {
  stubFetch();
  render(<App />);
  expect(await screen.findByRole("heading", { name: "Days in each CPCB category" })).toBeInTheDocument();
  const cards = screen.getByRole("list", { name: "Days in each CPCB category" });
  expect(within(cards).getAllByRole("listitem")).toHaveLength(6);
});
