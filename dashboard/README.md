# CS-44 BIS Evidence Dashboard

[Open the public dashboard](https://cs44-bis-evidence-dashboard.chenhomie0208.chatgpt.site/) — no login required.

## Run locally

Open `index.html` in a browser. Keep the five dashboard assets in the same folder. No software installation, build step, dependencies, or database connection is required.

Alternatively, from the repository root run `python -m http.server 8765 --directory dashboard` and open http://localhost:8765.

## Features

- Filter the overview and unit list by All, UG, or PG.
- Switch category counts between units and percentages.
- Click a category chart or select a category to filter the unit list.
- Search by unit code or title; inspect category scores and review-item counts.
- Follow official outline links and distinguish unavailable units from no-match outcomes.
- Responsive layout for desktop and mobile.

## Data provenance

Source repository: ruochentang2-code/infs6600-taxonomy-pilot  
Source commit: a3475d9cce9b54d48329daadbf974e9f174cbc28  
Capture: 11 September 2026, batch 3, prefer_s2 policy.

Inputs:
- `database/reports/batch-3/v_selected_course_category.json`
- `database/reports/batch-3/v_ug_pg_analysis.json`
- `database/reports/batch-3/v_failures.json`
- `database/data/seed.json` for titles and category definitions

`data.js` bundles a read-only snapshot. Reloading the page does not refresh GitHub data. Updating repository files does not automatically update the hosted website.

## Interpretation and limitations

27 scoped units; 26 evaluated (UG 11 of 12, PG 15 of 15). INFS3080 is unavailable, not a zero result. Categories overlap. Category counts refer to units with at least one positive item; percentages exclude unavailable units and do not sum to 100%.

Review-only evidence stays separate from positive matches. No human review is recorded in this snapshot. Review totals count item-category records because the same evidence item may occur in several categories.

The interface includes eight categories and selected 2026 offerings. It does not include the proposed 2025 fallback or SIE units, evidence-text review editing, or a live database connection. Original outline links may display later website updates.

The UG/PG comparison always shows both complete evaluated cohorts, independently of the unit-list filter. Batch-3 INFS6600 results use expanded input and can differ from the older pilot results in the root README.

## Updating the snapshot

Regenerate the bundled data from the selected analysis reports, preserving source date, selection policy, unit availability and category definitions. Verify the 16 cohort/category aggregates against `v_ug_pg_analysis.json`, and recheck missing-unit handling and denominators before publishing a new website version.

## Initial verification

The initial build was checked in Edge with automated browser checks for search, cohort/category filters, reset and empty states, unit details, original-outline links, and no-match versus unavailable handling. All 16 cohort/category aggregates matched the saved reports. Desktop, 390px mobile and 760px tablet layouts were checked; no JavaScript errors were observed.

## Files

- `index.html`: page structure
- `styles.css`: responsive presentation
- `app.js`: rendering and interactions
- `data.js`: saved data snapshot
- `favicon.svg`: icon
