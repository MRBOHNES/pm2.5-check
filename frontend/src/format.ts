/** "2026-10-21" -> "21 Oct". Parsed as UTC so the viewer's time zone can't shift the day. */
export function formatDay(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

/** "Very Poor" -> "very-poor", used for CSS class names. */
export function slug(category: string): string {
  return category.toLowerCase().replace(/\s+/g, "-");
}
