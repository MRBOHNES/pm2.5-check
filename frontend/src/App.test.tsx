import { render, screen } from "@testing-library/react";
import App from "./App";

const CITIES = [{ name: "delhi", label: "Delhi", has_measured: true }];
const PEAK = {
  city: "delhi", standard: 60, window_days: 30, source: "measured", days_compared: 27,
  peak: { date: "2026-10-21", value: 149.6, measured: 149.6, modelled: 91.8, difference: -57.8,
          category: "Very Poor", ratio_to_standard: 2.5 },
};

function stubFetch(peakStatus = 200) {
  vi.stubGlobal("fetch", vi.fn(async (url: URL) => {
    const body = url.pathname === "/cities" ? CITIES : PEAK;
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
  expect(await screen.findByRole("alert")).toHaveTextContent("The server answered 502");
  expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
});
