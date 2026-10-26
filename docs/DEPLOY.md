# Deploying PM2.5 Check

Two Vercel projects from this one repo, shipped only by GitHub Actions:

```
push/merge to main --> CI (ruff, pytest >= 80%, frontend checks, docker /health)
                         |  success on main only
                         v
                  Deploy workflow --> backend project (FastAPI, repo root)  --> smoke test /health + /peak
                                  --> frontend project (Vite, frontend/)    --> bundle check + smoke test page text
```

Vercel's own Git production deploys are switched off (`git.deploymentEnabled` for `main` in both `vercel.json` files), so
nothing reaches production unless CI is green. Pull requests still get Vercel preview deployments. The Dockerfile is for
local runs and the CI check only; Vercel does not run the container.

## One-time setup (done in the dashboards)

1. **Backend project.** Vercel → Add New → Project → import this repo (e.g. name it `pm25-check-api`). Root Directory
   `./`, Framework Preset **FastAPI** (Vercel finds `app` in `app/main.py`; the Python version comes from
   `.python-version`). Add the environment variables `OPENAQ_API_KEY` (Production **and** Preview) and `ALLOWED_ORIGINS`
   (step 3).
2. **Frontend project.** Import the same repo again (e.g. `pm25-check-web`), Root Directory `frontend`, preset **Vite**.
   The Root Directory picker only lists folders that exist on the default branch, so `frontend/` must already be merged
   to `main`. Add `VITE_API_URL` = the backend's production URL, no trailing slash (Production **and** Preview), saved as
   a plain variable (type **Config**), **not Secret/Sensitive**: `vercel pull` cannot read sensitive values, so the
   workflow would build the site with an empty address. (See bug 7 in [`BUG_JOURNAL.md`](BUG_JOURNAL.md).)
3. **Allowed origins** (backend project). `ALLOWED_ORIGINS` is comma-separated; `*` matches one host label, never a dot:
   `https://pm25-check-web.vercel.app,https://pm25-check-web-*-<your-team-slug>.vercel.app`
   (production domain, then preview deployments; the team slug is the last part of any preview address). Keep it
   narrow: do not use `https://*.vercel.app`. Save the variable, then **redeploy the backend**; a new value only applies
   to new deployments.
4. **Token and IDs.** Create a token (Account Settings → Tokens). Project IDs and the Org ID are in each project's
   Settings → General, or in `.vercel/project.json` after `npx vercel link`.
5. **GitHub secrets** (Settings → Secrets and variables → Actions). Names only here, never values:

   | Secret | What |
   |---|---|
   | `VERCEL_TOKEN` | the token from step 4 |
   | `VERCEL_ORG_ID` | team ID (starts with `team_`) |
   | `VERCEL_PROJECT_ID_BACKEND` | backend project ID (starts with `prj_`) |
   | `VERCEL_PROJECT_ID_FRONTEND` | frontend project ID |
   | `BACKEND_URL` | the backend's public production URL, used by the smoke test |
   | `FRONTEND_URL` (optional) | the frontend's public production URL; if unset the smoke test uses the fresh deployment URL, which sits behind Vercel's deployment protection |

6. **First deploy.** Actions → Deploy → Run workflow on `main`, or merge to `main`.
7. **Branch protection** (Settings → Branches → rule for `main`): require a pull request, require the status checks
   `backend (3.12)`, `backend (3.14)`, `frontend` and `docker`, and block direct pushes.

## Environment variables

| Variable | Where | Notes |
|---|---|---|
| `OPENAQ_API_KEY` | backend (Production and Preview) | read from the environment or a local `.env`; never committed |
| `ALLOWED_ORIGINS` | backend | comma-separated origins; defaults to the local Vite server when unset |
| `VITE_API_URL` | frontend (Production and Preview) | plain (Config) variable; empty is treated as "not set" and fails the build check |

Examples (names only) are in `.env.example` and `frontend/.env.example`.

## Checking a deployment

- **GitHub:** Actions → Deploy. Green means the build, the deploy and the smoke tests (`/health`, `/peak`, the backend
  address inside the built JS, and the page title) all passed.
- **Vercel:** each project's Deployments tab. The top row should say *Ready* and *Current* (Production), with the commit
  you expect. Deployments made by the workflow show the CLI as their source; one made by a Git push would show a branch,
  which would mean Vercel deployed on its own.
- **Is the live version the latest?** `curl https://<backend>/health` returns the deployed commit in `version`. Compare it
  with `git rev-parse --short origin/main`.
- **The page itself:** open it and check that the peak card and the chart load.
- **Deployment URLs vs aliases.** A deployment's own unique URL is behind Vercel Authentication and returns a login
  redirect to anonymous clients. Test the public production domains.

## Rollback

In Vercel, open each project → Deployments → pick the previous good production deployment → **Promote to Production**
(do the backend and frontend separately). Then fix forward with a pull request, or `git revert <commit>` and merge it.

## Free-plan notes

- The first request after idle can be slow; the page shows "Waking up the server…" after 3 seconds.
- A function may run for up to 60 seconds (`vercel.json`); a 30-day fetch from five stations takes about 3 seconds warm.
- The in-memory cache is best-effort: serverless instances come and go, and each has its own copy.
- Vercel Hobby is for non-commercial use.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| The page shows "Could not reach the server" and the browser console mentions CORS | `ALLOWED_ORIGINS` lacks the page's origin, was not saved, or the backend was not redeployed |
| The page shows "missing its API address" | `VITE_API_URL` was empty when the site was built (set as a Secret, or missing for that environment) |
| `vercel pull` says "Project not found" | `VERCEL_ORG_ID` or a project ID is wrong, or the token belongs to another scope |
| `vercel build` says "uv is required but was not found" | the runner lacks `uv`; the workflow installs it with `pip install uv` |
| The deploy smoke test gets a 302 or 401 | it is calling a protected deployment URL; use the public production URL |
