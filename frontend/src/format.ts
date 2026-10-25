const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2026-10-21" -> "21 Oct". Plain string maths, so no time zone or locale can shift it. */
export function formatDay(iso: string): string {
  const [, month, day] = iso.split("-").map(Number);
  return `${day} ${MONTHS[month - 1]}`;
}

/** "Very Poor" -> "very-poor", used for CSS class names. */
export function slug(category: string): string {
  return category.toLowerCase().replace(/\s+/g, "-");
}
