import type { City, PeakResponse, SeriesResponse } from "./types";

// An empty or missing VITE_API_URL counts as "not set". The localhost fallback is for `npm run dev` only,
// so a production build without the address fails with a clear message instead of calling localhost.
const configured = (import.meta.env.VITE_API_URL ?? "").trim().replace(/\/$/, "");
export const BASE = configured || (import.meta.env.DEV ? "http://localhost:8000" : "");
const TIMEOUT_MS = 60_000; // generous: a cold serverless start plus a 30-day OpenAQ fetch

export class ApiError extends Error {
  status: number | null;
  constructor(message: string, status: number | null = null) {
    super(message);
    this.status = status;
  }
}

/** GET a JSON path from the backend with a timeout; throws ApiError on any failure. */
export async function getJson<T>(path: string, params: Record<string, string | number> = {}, signal?: AbortSignal): Promise<T> {
  if (!BASE) throw new ApiError("This site is missing its API address (VITE_API_URL was empty when it was built)");
  const url = new URL(`${BASE}${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const timeout = AbortSignal.timeout(TIMEOUT_MS);
  try {
    const resp = await fetch(url, { signal: signal ? AbortSignal.any([signal, timeout]) : timeout });
    if (!resp.ok) throw new ApiError(`The server answered ${resp.status}`, resp.status);
    return (await resp.json()) as T;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (signal?.aborted) throw e; // the caller cancelled; not an error to show
    if (timeout.aborted) throw new ApiError("The server took too long to answer");
    throw new ApiError("Could not reach the server");
  }
}

export const fetchCities = (signal?: AbortSignal) => getJson<City[]>("/cities", {}, signal);

export const fetchPeak = (city: string, days: number, signal?: AbortSignal) =>
  getJson<PeakResponse>("/peak", { city, days }, signal);

export const fetchSeries = (city: string, days: number, signal?: AbortSignal) =>
  getJson<SeriesResponse>("/series", { city, days }, signal);
