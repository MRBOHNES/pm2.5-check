import { act, render, screen } from "@testing-library/react";
import { Skeleton } from "./Skeleton";

afterEach(() => vi.useRealTimers());

test("explains the cold start only after 3 seconds", () => {
  vi.useFakeTimers();
  render(<Skeleton label="Loading chart" />);
  expect(screen.getByRole("status", { name: "Loading chart" })).toBeInTheDocument();
  expect(screen.queryByText(/Waking up the server/)).not.toBeInTheDocument();
  act(() => { vi.advanceTimersByTime(3000); });
  expect(screen.getByText("Waking up the server, this can take a few seconds on the free plan…")).toBeInTheDocument();
});
