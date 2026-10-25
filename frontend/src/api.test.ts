async function loadApi(env: { VITE_API_URL: string; DEV: boolean }) {
  vi.resetModules();
  vi.stubEnv("VITE_API_URL", env.VITE_API_URL);
  vi.stubEnv("DEV", env.DEV);
  return import("./api");
}
afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

test("uses VITE_API_URL without a trailing slash", async () => {
  const api = await loadApi({ VITE_API_URL: "https://api.example.com/", DEV: false });
  expect(api.BASE).toBe("https://api.example.com");
});

test("falls back to localhost only in dev", async () => {
  expect((await loadApi({ VITE_API_URL: "", DEV: true })).BASE).toBe("http://localhost:8000");
  expect((await loadApi({ VITE_API_URL: "", DEV: false })).BASE).toBe("");
});

test("a production build with an empty address fails with a clear message, not an Invalid URL error", async () => {
  const fetchSpy = vi.fn();
  vi.stubGlobal("fetch", fetchSpy);
  const api = await loadApi({ VITE_API_URL: "", DEV: false });
  await expect(api.fetchCities()).rejects.toThrow(/missing its API address/);
  expect(fetchSpy).not.toHaveBeenCalled();
});
