import { formatDay, slug } from "./format";

test("formatDay gives D MMM", () => {
  expect(formatDay("2026-10-21")).toBe("21 Oct");
  expect(formatDay("2026-01-05")).toBe("5 Jan");
});

test("slug makes css-friendly names", () => {
  expect(slug("Very Poor")).toBe("very-poor");
  expect(slug("Good")).toBe("good");
});
