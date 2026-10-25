import { render, screen } from "@testing-library/react";
import { Limitations } from "./Limitations";

test("links to every source, the repo and the API docs", () => {
  render(<Limitations apiUrl="https://api.example.com" />);
  expect(screen.getByRole("link", { name: /Open-Meteo/ })).toHaveAttribute("href", "https://open-meteo.com/en/docs/air-quality-api");
  expect(screen.getByRole("link", { name: /OpenAQ/ })).toHaveAttribute("href", "https://docs.openaq.org");
  expect(screen.getByRole("link", { name: "CPCB National AQI" })).toHaveAttribute("href", "https://cpcb.nic.in/national-air-quality-index/");
  expect(screen.getByRole("link", { name: /Source code on GitHub/ })).toHaveAttribute("href", "https://github.com/MRBOHNES/pm2.5-check");
  expect(screen.getByRole("link", { name: /API documentation/ })).toHaveAttribute("href", "https://api.example.com/docs");
  expect(screen.getByText(/Modelled is not measured/)).toBeInTheDocument();
});
