# Interview Q&A

Short answers about how PM2.5 Check is built. The reasoning is in [`ARCHITECTURE.md`](ARCHITECTURE.md); the failures that
shaped it are in [`BUG_JOURNAL.md`](BUG_JOURNAL.md).

## Python, pandas and NumPy

**Why `np.select` for the AQI category?**
It is vectorised: one pass over the whole array with an ordered list of conditions and no Python loop. Upper bounds are inclusive, so 30 is Good and 30.5 is Satisfactory; NaN is set to `None` afterwards.

**How do you stop a daily mean from misleading?**
A day needs at least 18 valid hourly readings, otherwise it is NaN. Negative values and values above 1000 become NaN, and nothing is interpolated across gaps.

**How are time zones handled?**
Open-Meteo is requested in IST. OpenAQ sends UTC, so it is converted with `tz_convert("Asia/Kolkata")` and grouped by IST calendar day. A test checks the boundary: 18:00Z is 23:30 IST and belongs to that IST day.

**Why z-scores on model minus measured?**
The outlier is a day the model misses unusually, not simply a high-pollution day. Zero variance returns no outliers.

**How is the peak day chosen?**
`idxmax` on a frame sorted by date, so ties go to the earliest date. It prefers measured values, falls back to modelled and says so in `source`, and excludes the day still in progress.

**Why is the correlation sometimes `null`?**
With one comparable day, or no variation, Pearson r is undefined. It must be `null` in the JSON, because NaN breaks JSON serialisation.

## API integration and async

**How does the retry logic work?**
It retries on 429, 5xx, timeouts and connection errors with exponential backoff plus jitter, and honours `Retry-After`. Other 4xx fail immediately. The jitter stops many clients retrying in lockstep.

**What does the semaphore do?**
It caps concurrent requests across the five station fetches, so OpenAQ's rate limit is not hammered.

**How do the two APIs run in parallel?**
`asyncio.gather` runs the Open-Meteo call and the station calls together; each station call follows OpenAQ's pagination until a short page.

**Why 502 and 504?**
A timeout upstream becomes 504; any other upstream failure is 502; a missing API key is 503. The client can tell "slow" from "broken" from "not configured".

**Why one shared `AsyncClient`?**
It reuses connections and keeps timeouts in one place. It is created in FastAPI's `lifespan`.

## Pydantic and FastAPI

**Why build the models from saved samples?**
The field names come from real responses, not guesses, so a schema change fails loudly at validation instead of silently producing NaN.

**How does CORS work here?**
`ALLOWED_ORIGINS` is a comma list; an entry with `*` becomes a regex where `*` matches one host label, never a dot. That keeps `evil.com-team.vercel.app` out while Vercel preview addresses work.

**Why a separate `/health`?**
It makes no upstream calls, so a smoke test can tell "the server is up" from "OpenAQ is down".

## Design and trade-offs

**Why can't you rely on the in-memory cache on Vercel?**
Serverless instances start and stop and each has its own copy, so it only saves calls while an instance is warm. Correctness never depends on it. It also shares in-flight fetches, so two simultaneous requests make one upstream call.

**Is modelled vs measured a fair comparison?**
Not exactly: a ~45 km grid cell is compared with point stations, so part of the gap is scale. Over 26 days in the last 30, MAE was 17.0 µg/m³ and r 0.72, and the model missed the 21 Oct peak (91.8 vs 149.6).

## Testing, CI/CD and deployment

**How do you test without calling real APIs?**
`respx` mocks httpx, so tests cover 429 then success, repeated 500 giving up, a timeout and a 404 failing fast. Cleaning tests use small hand-built DataFrames.

**Why must CI pass before deploy?**
The Deploy workflow runs only after CI succeeds on a push to `main`, and Vercel's own Git production deploys are off, so nothing ships another way. It checks out the exact commit that passed.

**Why did the deploy pass while the site was broken, and what changed?**
The smoke test only checked the page title. `VITE_API_URL` had been built in empty because it was stored as a Secret, which `vercel pull` cannot read. A build check now fails the deploy if the built JavaScript lacks the backend address.

**Why two Vercel projects?**
The backend is Python/FastAPI and the frontend is a Vite single-page app. They deploy, scale and roll back independently.

**What is the Dockerfile for, if Vercel does not run it?**
Local runs and a CI check that the image builds and `/health` answers.

**How do you roll back?**
In Vercel, promote the previous production deployment for each project, then fix forward with a pull request or `git revert`.

**Why split `requirements.txt` from `requirements-dev.txt`?**
Python bundles on Vercel include everything reachable, so test tools and matplotlib would only add weight. The runtime install is about 186 MB.
