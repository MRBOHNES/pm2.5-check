# Bug journal

Real problems hit while building and deploying PM2.5 Check: symptom, cause, fix and what it taught. Short answers about
the design are in [`INTERVIEW_QA.md`](INTERVIEW_QA.md).

## 1. Open-Meteo returns the cities with no labels
**Symptom:** a multi-city call returns a bare JSON list; nothing says which entry is which city.
**Cause:** the API answers in request order and echoes only coordinates (snapped to its model grid, so Delhi's 28.6139 comes
back as 28.6).
**Fix:** cities are matched by position, and the code checks that the number of returned locations equals the number asked.
**Lesson:** when an API gives no key, make the assumption explicit and guard it.

## 2. OpenAQ sensors that look right return no data
**Symptom:** a station found through `/v3/locations` returned empty hourly data.
**Cause:** older sensor ids on the same station are dead; only the live sensor id carries data.
**Fix:** the live PM2.5 sensor id for each of the five stations is pinned in `app/client.py`, with a comment saying when it
was checked.
**Lesson:** verify against a real response before modelling a field, and re-verify when data looks empty.

## 3. "Today" looked like a real day
**Symptom:** the modelled series had a full daily mean for the current day, which was not measured at all.
**Cause:** Open-Meteo returns forecast hours for today, so 24 hours exist; the stations only have the hours that have passed.
**Fix:** days on or after today's IST date are dropped from the peak and the series.
**Lesson:** a "complete" day needs a definition; here it is a day that has fully passed.

## 4. The live page showed "Could not reach the server"
**Symptom:** the deployed frontend worked locally, but in production every request failed; the console said the response
had no `Access-Control-Allow-Origin` header.
**Cause:** the browser blocks a page from reading another origin's responses unless that server allows it. `ALLOWED_ORIGINS`
was unset, so the API only allowed the local Vite server. Later, the variable had been edited but not saved, and the
backend had not been redeployed.
**Fix:** set `ALLOWED_ORIGINS` to the production origin plus a one-label wildcard for previews, save it, and redeploy the
backend (a variable only applies to new deployments). Tested with real `Origin` headers.
**Lesson:** the API works fine from curl; CORS only shows up in a browser. Test with an `Origin` header.

## 5. `vercel pull` said "Project not found"
**Symptom:** the deploy workflow failed at its first Vercel step.
**Cause:** `VERCEL_ORG_ID` and a project ID did not match any project the token could see. The project's local link file
holds the correct `orgId` and `projectId`.
**Fix:** read both from `.vercel/project.json` after `vercel link`, and reset the secrets.
**Lesson:** IDs are not names; copy them from the source.

## 6. `vercel build` said "uv is required but was not found"
**Symptom:** the deploy workflow got past `pull` and failed on `build` for the FastAPI project.
**Cause:** Vercel's Python build uses the `uv` package manager, which the CI runner does not have.
**Fix:** a `pip install uv` step before the build.

## 7. The site deployed "successfully" with an empty API address
**Symptom:** the Deploy workflow was green, but the live page showed "Failed to construct 'URL': Invalid URL".
**Cause:** `VITE_API_URL` had been saved as a **Secret** variable. `vercel pull` cannot read secret values, so the build
baked in an empty string (the live bundle contained neither the API address nor the localhost fallback). The smoke test
only checked the page title, so it passed.
**Fix:** save `VITE_API_URL` as a plain variable; make an empty address a clear runtime error instead of an `Invalid URL`;
add `scripts/check_bundle.sh`, which fails the deploy if the built JavaScript lacks the backend address.
**Lesson:** a smoke test must check the thing that broke. A green run is not proof the site works.

## 8. The chart rendered nothing
**Symptom:** the chart section showed only its caption.
**Cause:** the responsive chart container takes its size from its parent, and the parent had no height.
**Fix:** a wrapper with a fixed height. A screenshot, not a unit test, showed it.
**Related:** Recharts' built-in legend overlapped the lines on a phone, and a peak label was clipped by its narrow band, so
the legend became plain HTML and the label is drawn beside the band. Months are formatted by hand because the locale
formatter printed "Sept".

## 9. The frontend tests need Node 22, not 20
**Symptom (would-be):** CI on Node 20 would fail to start the test runner.
**Cause:** the installed `vitest` declares `^22.12 || ^24 || >=26`.
**Fix:** CI and the deploy workflow use Node 22.

## 10. A deployment's own URL answers 302 to anonymous clients
**Symptom:** testing a fresh deployment's address returned a "Protected by Vercel Authentication" redirect.
**Cause:** Vercel protects each deployment's unique URL; only the production domain is public.
**Fix:** the smoke tests use the public production URLs (`BACKEND_URL`, `FRONTEND_URL`).
