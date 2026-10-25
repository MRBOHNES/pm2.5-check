# PM2.5 Check: can you trust the free air-quality numbers for Delhi?

[![CI](https://github.com/MRBOHNES/pm2.5-check/actions/workflows/ci.yml/badge.svg)](https://github.com/MRBOHNES/pm2.5-check/actions/workflows/ci.yml)
[![Deploy](https://github.com/MRBOHNES/pm2.5-check/actions/workflows/deploy.yml/badge.svg)](https://github.com/MRBOHNES/pm2.5-check/actions/workflows/deploy.yml)

Compares **modelled** PM2.5 (Open-Meteo, CAMS model) with **measured** PM2.5 (OpenAQ stations in Delhi), finds the
worst day, and bins days into India's CPCB air-quality categories.

**Live:** frontend and API links are added here after the first deploy (see [Deployment](#deployment)).

![Desktop, light](docs/screenshots/desktop-light.png)

<p>
  <img src="docs/screenshots/mobile-light.png" alt="Mobile, light" width="260">
  <img src="docs/screenshots/desktop-dark.png" alt="Desktop, dark mode" width="520">
</p>

## What it shows
1. **Peak day** (last 30 days): highest daily PM2.5, its CPCB category, how many times India's 24-hour standard
   it was, and how far the model was off that day.
2. **Model vs measured chart** with the peak day shaded, the 60 µg/m³ standard, and MAE / correlation / bias.
3. **CPCB category cards**: days spent in each of the six categories; the latest and the peak day's category are marked.
4. **Limitations** with links to every source.

Measured values exist for Delhi only (five stations). Other cities fall back to modelled values and say so.

## Findings (last 30 days to 25 Oct 2026, Delhi)
- **The model gets the shape right but misses the extremes.** Over 26 comparable days: MAE **17.0 µg/m³**, correlation
  **r = 0.72**, average bias +3.3 µg/m³.
- **The worst day was 21 Oct: 149.6 µg/m³ measured (Very Poor, 2.5x the standard) vs 91.8 modelled**, off by 57.8. A
  ~45 km grid cell smooths out local peaks that point stations record. 21 Oct is also the only outlier day.
- **Delhi was above India's 24-hour standard (60 µg/m³) on 17 of the 26 days with station data.**

Numbers come from a live run on 26 Oct 2026 and change daily. 26 of 30 days have station data (see Limitations).

## Run locally
Needs Python 3.12+, Node 22+, and a free [OpenAQ API key](https://explore.openaq.org) (only the Delhi measured
data needs it; the tests need no key and no network).

```bash
git clone https://github.com/MRBOHNES/pm2.5-check.git && cd pm2.5-check

# backend
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cp .env.example .env                  # set OPENAQ_API_KEY=<your key>
.venv/bin/uvicorn app.main:app        # http://127.0.0.1:8000/docs

# frontend (second terminal)
cd frontend && cp .env.example .env.local && npm ci && npm run dev    # http://localhost:5173
```

Tests and checks (the same ones CI runs):
```bash
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/pytest -q --cov=app --cov-fail-under=80      # 74 tests, ~85% coverage
cd frontend && npm run lint && npm run typecheck && npm test -- --run && npm run build   # 22 tests
```
`.env` is gitignored: the key lives only there (and in Vercel's settings), never in `.env.example`.

**API:** `GET /peak?city=Delhi&days=30`, `GET /series?city=Delhi&days=30`, `GET /cities`, `GET /health`,
plus `/summary/{city}`, `/compare?cities=delhi,mumbai`, `/delhi/model-vs-measured`.
`python -m app.charts` writes two PNG charts to `output/`.

**Docker** is for local runs and the CI check only; Vercel does not run the container:
```bash
docker build -t pm25-check . && docker run -p 8000:8000 --env-file .env pm25-check
```

## How it works
```
Open-Meteo (1 call, 4 cities) --+                         +--> /peak ----+
                                +--> pydantic models --> pandas (IST, dedupe, daily mean >= 18 h)
OpenAQ (5 Delhi stations,   ----+      (retry, backoff,   +--> /series --+--> React + Recharts page
 concurrent, paginated)                 concurrency cap)      CPCB category (np.select), MAE, r
```
- `app/client.py`: one shared async `httpx` client; retry on 429/5xx/timeouts with exponential backoff and jitter,
  `Retry-After` honoured, other 4xx fail at once; a semaphore caps concurrency. Timeout becomes HTTP 504, other
  upstream failures 502.
- `app/cleaning.py`: timestamps to `Asia/Kolkata`, duplicates dropped, impossible values become NaN (never interpolated),
  daily means need 18+ valid hours.
- `app/analysis.py`: vectorised CPCB category (`np.select`, inclusive upper bounds so 30 is Good and 30.5 is
  Satisfactory), MAE, Pearson r, z-score outliers, peak day (measured first, modelled fallback, ties go to the
  earliest date, today excluded).
- `app/cache.py`: best-effort 10-minute cache so `/peak` and `/series` share upstream calls.
  **Serverless instances come and go, so nothing depends on it.**
- `frontend/`: Vite + React + TypeScript; design tokens in `src/styles/tokens.css`; dark mode follows the OS.

## Deployment
Two Vercel projects from this one repo, shipped only by GitHub Actions:

```
push/merge to main --> CI (ruff, pytest>=80%, frontend checks, docker /health)
                         |  success on main only
                         v
                  Deploy workflow --> backend project (FastAPI, repo root)  --> smoke test /health + /peak
                                  --> frontend project (Vite, frontend/)    --> smoke test page text
```
Vercel's own Git production deploys are switched off (`git.deploymentEnabled` for `main` in both `vercel.json`
files), so nothing reaches production unless CI is green. Pull requests still get Vercel preview deployments.

### One-time setup (you do this in the dashboards)
1. **Backend project.** Vercel → Add New → Project → import this repo. Name it e.g. `pm25-check-api`.
   Root Directory `./`, Framework Preset **FastAPI** (Vercel finds `app` in `app/main.py`; Python comes from
   `.python-version`). Add env vars: `OPENAQ_API_KEY` (Production **and** Preview) and `ALLOWED_ORIGINS` (below).
2. **Frontend project.** Import the same repo again, e.g. `pm25-check-web`. Root Directory `frontend`, preset **Vite**.
   Add `VITE_API_URL` = the backend's production URL, no trailing slash (Production **and** Preview).
   Save it as a plain variable (type **Config**), **not Secret/Sensitive**: `vercel pull` cannot read sensitive
   values, so the workflow would build the site with an empty address. The deploy workflow checks the built
   files for the backend address and fails if it is missing.
3. **Allowed origins.** `ALLOWED_ORIGINS` is comma-separated; `*` matches one host label, never a dot:
   `https://pm25-check-web.vercel.app,https://pm25-check-web-*-<your-team-slug>.vercel.app`
   (production domain, then preview deployments). Keep it narrow; do not use `https://*.vercel.app`.
4. **Token and IDs.** Create a token (Account Settings → Tokens). Project IDs and the Org ID are in each project's
   Settings → General (or `.vercel/project.json` after `vercel link`).
5. **GitHub secrets** (Settings → Secrets and variables → Actions). Names only here, never values:

   | Secret | What |
   |---|---|
   | `VERCEL_TOKEN` | the token from step 4 |
   | `VERCEL_ORG_ID` | team/user ID |
   | `VERCEL_PROJECT_ID_BACKEND` | backend project ID |
   | `VERCEL_PROJECT_ID_FRONTEND` | frontend project ID |
   | `BACKEND_URL` | backend production URL, used by the smoke test |
   | `FRONTEND_URL` (optional) | frontend production URL; if unset the smoke test uses the fresh deployment URL, which can sit behind Vercel's deployment protection |

6. **First deploy.** Actions → Deploy → Run workflow, or merge to `main`.
7. **Branch protection** (Settings → Branches → Add rule for `main`): require a pull request, require status checks
   `backend (3.12)`, `backend (3.14)`, `frontend` and `docker` to pass, and block direct pushes.

Env var summary: backend `OPENAQ_API_KEY`, `ALLOWED_ORIGINS`; frontend `VITE_API_URL`. Examples in `.env.example` and
`frontend/.env.example`.

### Rollback
In Vercel, open each project → Deployments → pick the previous good production deployment → **Promote to Production**
(do the backend and frontend separately). Then fix forward with a pull request, or `git revert <commit>` and merge it.

### Free-plan notes
Vercel Hobby functions can take a moment on a cold start; the page shows "Waking up the server…" after 3 seconds.
The function allows up to 60 s per request (a 30-day fetch from five stations takes about 3 s warm).
Hobby is for non-commercial use.

## Limitations
- **Modelled is not measured.** Open-Meteo gives CAMS model values on a ~45 km grid cell (it snaps coordinates to that
  grid); stations read at a point. Part of the gap is that mismatch, not model error.
- **Five hand-picked Delhi stations** (R K Puram, Punjabi Bagh, Pusa, Mandir Marg, Anand Vihar), not a full network.
  Other cities have no station data here.
- **Station feeds lag.** The latest days often have too few readings (daily means need 18 hours), so the last 1-2 days
  usually show modelled values only.
- **Thirty days** is too few to say how the model behaves across seasons.
- **Colours.** Category names and PM2.5 bands follow CPCB; the colours are adjusted for text contrast (all pass WCAG AA)
  and I could not check them against CPCB's official scale. CPCB's official label for 61-90 is "Moderately polluted";
  this app says "Moderate".
- 60 µg/m³ is the 24-hour PM2.5 limit in India's 2009 national standards. I did not check for later revisions.

## What I'd add next
Station data for more cities, a longer window (a season), a city comparison chart, an outlier table, Dependabot,
preview-URL comments on pull requests, structured request logs, and a multi-stage non-root Docker image.

## Sources
- Open-Meteo Air Quality API: https://open-meteo.com/en/docs/air-quality-api
- OpenAQ API: https://docs.openaq.org
- CPCB National AQI: https://cpcb.nic.in/national-air-quality-index/
- India's 2009 air quality standards (CPCB notification B-29016/20/90/PCI-L, 18 Nov 2009):
  https://leap.unep.org/akn/in/act/2009/b-29016-20-90-pci-l/eng@2009-11-18
