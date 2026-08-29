# Eurostat Data-Quality Pipeline — Project Plan

Project-management plan for the Eurostat DQ pipeline: milestones, issues, a label
system, and deadlines. Companion to the build guide in [PROJECT.md](PROJECT.md).

- **Start date:** 2026-07-13 (Mon)
- **Target completion:** 2026-08-23 (Sun) — **6 weeks**, part-time over the summer
- **Datasets:** `demo_r_d2jan` (population, NUTS 2) **and** `env_air_gge` (GHG emissions, country)
- **Repo:** `eurostat-dq`

> Scope note: the pipeline handles **two** datasets through a shared, config-driven design
> (a "dataset registry"). This adds a per-dataset filtering step and a visualization step
> versus a single-dataset build — see PROJECT.md §1, §4, §9.

> Timing note: assumes ~8–12 h/week over the summer break. The validation layer (M3) gets
> 2 weeks because great_expectations / pydantic are new tooling. M4 is the busiest week
> (anomaly + viz + report + CLI); if a week slips, protect M3 and let `prio: P2` slide.

> The issues below are intentionally written as **goals + acceptance criteria**, not code.
> The "how to think about it" for each lives in PROJECT.md. A `gh` script at the bottom
> (§5) upserts all labels, milestones and the M1 issues.

---

## 1. Label system (categorization)

Five orthogonal label groups. Every issue gets **one `type`**, **one `area`**, **one
`prio`**, **one `size`**, and — where relevant — **one or more `qa` labels**.

### `type:` — what kind of work
| Label | Color | Meaning |
|---|---|---|
| `type: feature` | `#1D76DB` (blue) | New capability / code |
| `type: infra` | `#5319E7` (purple) | Setup, tooling, packaging, CI |
| `type: test` | `#0E8A16` (green) | Tests and test data |
| `type: docs` | `#C2E0C6` (light green) | README, docstrings, notebooks-as-docs |
| `type: research` | `#FBCA04` (yellow) | Investigate / learn before coding |
| `type: bug` | `#D73A4A` (red) | Something is broken |
| `type: refactor` | `#BFDADC` (grey-blue) | Improve code without changing behaviour |

### `area:` — which part of the pipeline
| Label | Color | Component |
|---|---|---|
| `area: repo` | `#EDEDED` | Repo structure, env, packaging |
| `area: ingestion` | `#006B75` | Registry + Eurostat API → raw data |
| `area: cleaning` | `#0052CC` | Raw → tidy → per-dataset slice |
| `area: validation` | `#B60205` | pydantic + great_expectations |
| `area: anomaly` | `#E99695` | scikit-learn outlier detection |
| `area: reporting` | `#FEF2C0` | Visualization, report + CLI |
| `area: ci-cd` | `#5319E7` | GitHub Actions, automation |

### `prio:` — priority
| Label | Color | Meaning |
|---|---|---|
| `prio: P0` | `#B60205` (dark red) | Blocker — nothing works without it |
| `prio: P1` | `#D93F0B` (orange) | Core deliverable |
| `prio: P2` | `#FBCA04` (yellow) | Nice-to-have / stretch |

### `size:` — rough effort
| Label | Color | Estimate |
|---|---|---|
| `size: S` | `#C2E0C6` | < 2 hours |
| `size: M` | `#FEF2C0` | half a day |
| `size: L` | `#F9D0C4` | a full day or more |

### `qa:` — which data-quality dimension it validates (project-specific)
| Label | Color | Dimension |
|---|---|---|
| `qa: completeness` | `#BFD4F2` | No missing required values |
| `qa: uniqueness` | `#BFD4F2` | No duplicate keys |
| `qa: consistency` | `#BFD4F2` | Values match expected sets/rules |
| `qa: accuracy` | `#BFD4F2` | Values within valid ranges/types |
| `qa: timeliness` | `#BFD4F2` | Data is recent / up to date |

---

## 2. Milestones & timeline (6 weeks)

| # | Milestone | Window | **Due** | Load |
|---|---|---|---|---|
| M1 | Setup, registry & ingestion | Jul 13 – Jul 19 | **2026-07-19** | Light |
| M2 | Cleaning & EDA | Jul 20 – Jul 26 | **2026-07-26** | Medium |
| M3 | Validation layer (5 QA dimensions) | Jul 27 – Aug 09 | **2026-08-09** | **Heavy (2 wks)** |
| M4 | Anomaly, visualization, report & CLI | Aug 10 – Aug 16 | **2026-08-16** | Heavy |
| M5 | Testing, CI/CD, docs & release | Aug 17 – Aug 23 | **2026-08-23** | Heavy |

Everything lands before September — before the semester / any internship starts.

---

## 3. Issues

Each issue lists **labels**, **milestone**, a **target date**, the goal, and acceptance
criteria (the checklist you tick to call it "done"). The *how* is in PROJECT.md.

### M1 — Setup, registry & ingestion · due 2026-07-19

---

#### #1 Create repository skeleton and `.gitignore`
`type: infra` · `area: repo` · `prio: P0` · `size: S` · **M1** · target 2026-07-13

- [ ] `src/eurostat_dq/` package with module stubs (`config`, `ingest`, `clean`, `schema`, `expectations`, `anomaly`, `viz`, `report`, `cli`)
- [ ] `data/raw/`, `data/processed/`, `notebooks/`, `tests/`, `reports/` folders
- [ ] `.gitignore` excludes `data/raw/`, `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`
- [ ] Initial commit pushed to GitHub

#### #2 Set up virtual environment and dependencies
`type: infra` · `area: repo` · `prio: P0` · `size: S` · **M1** · target 2026-07-14

- [ ] `python -m venv .venv` and activate
- [ ] Install: pandas, numpy, scipy, eurostat, requests, pydantic, great_expectations, scikit-learn, matplotlib, **geopandas**, jupyter, pytest, statsmodels
- [ ] `pip freeze > requirements.txt` (or keep `pyproject.toml` authoritative)
- [ ] Confirm `geopandas` imports (it has heavy geo deps — see PROJECT.md §2)

#### #3 Add project README stub and license
`type: docs` · `area: repo` · `prio: P1` · `size: S` · **M1** · target 2026-07-15

- [ ] One-paragraph project description (mentions both datasets)
- [ ] Placeholder sections: Setup, Usage, Quality dimensions, Results
- [ ] MIT license file present and referenced from the README

#### #4 Design the dataset registry (both datasets)
`type: research` · `area: ingestion` · `prio: P0` · `size: M` · **M1** · target 2026-07-16

Define `config.py` so one pipeline can serve both datasets (see PROJECT.md §1).
- [ ] Inspect `demo_r_d2jan` and `env_air_gge`: real dimensions, codes, units
- [ ] For each, record: code, dimension filters (`{column: keep_value}`), valid `geo` set, plausible value range, geography level (country/NUTS 2), timeliness threshold
- [ ] Capture this as a small config structure (dict or dataclass per dataset)
- [ ] Note the differences (regional vs country geo; inventory lag) in the README

#### #5 Implement generic `fetch_dataset()` + caching
`type: feature` · `area: ingestion` · `prio: P0` · `size: M` · **M1** · target 2026-07-19

- [ ] `ingest.fetch_dataset(code)` returns a non-empty DataFrame for **both** codes
- [ ] Raw pulls cached under `data/raw/{code}.parquet`; second call skips the network
- [ ] Network / bad-code errors handled with a clear message (no raw traceback)
- [ ] Smoke test prints shape + head for each dataset

#### #6 Add raw REST/JSON-stat fetch as an alternative
`type: feature` · `area: ingestion` · `prio: P2` · `size: L` · **M1** · target 2026-07-19

Bonus REST signal — slip this first if the week is tight.
- [ ] `fetch_dataset_json(code, **filters)` hits the REST API with `requests`
- [ ] Parses JSON-stat into the same tidy shape as `fetch_dataset()`
- [ ] README note on the two paths

---

### M2 — Cleaning & EDA · due 2026-07-26

---

#### #7 Wide→long tidy transformation (generic)
`type: feature` · `area: cleaning` · `prio: P0` · `size: M` · **M2** · target 2026-07-22

- [ ] `clean.to_tidy(df)` reshapes year columns into `(…dims…, time, value)` rows
- [ ] Detects year vs dimension columns programmatically
- [ ] Coerces `value` to numeric; Eurostat `:` → `NaN`; standardises `geo`/`time`

#### #8 Per-dataset filtering via the registry
`type: feature` · `area: cleaning` · `prio: P0` · `size: M` · **M2** · target 2026-07-24

Collapse each dataset's extra dimensions to a comparable `geo × time × value` slice.
- [ ] `clean.apply_slice(df, cfg)` keeps only the configured `{column: keep_value}` rows
- [ ] Works for **both** datasets without dataset-specific branching
- [ ] Cleaned output saved to `data/processed/{code}.parquet`

#### #9 Exploratory data analysis notebook (both datasets)
`type: docs` · `area: cleaning` · `prio: P1` · `size: L` · **M2** · target 2026-07-26

- [ ] `describe()`, null counts, distributions for each dataset
- [ ] Time series (a few regions/countries) + boxplot by year
- [ ] Markdown interpretations; flag weird values → future test cases & accuracy ranges

---

### M3 — Validation layer (5 QA dimensions) · due 2026-08-09 · **2 weeks**

---

#### #10 pydantic record model (per-dataset accuracy/consistency)
`type: feature` · `area: validation` · `prio: P0` · `size: M` · `qa: accuracy` · `qa: consistency` · **M3** · target 2026-07-30

- [ ] `schema.Record` with typed `geo`, `time`, `value: float | None`
- [ ] Validators for geo/year/value; **valid-geo set comes from the dataset config** (region vs country)
- [ ] Missing-value rule decided and documented

#### #11 Row-level validation runner
`type: feature` · `area: validation` · `prio: P0` · `size: M` · `qa: accuracy` · **M3** · target 2026-08-01

- [ ] `validate_rows(df, cfg)` returns `(valid, errors)` without crashing
- [ ] Errors structured for the report; pass/fail counts summarised

#### #12 Dataset-level checks with great_expectations
`type: feature` · `area: validation` · `prio: P1` · `size: L` · `qa: completeness` · `qa: uniqueness` · `qa: consistency` · **M3** · target 2026-08-06

Budget extra time — GX is the steepest curve. Plain-function fallback is fine (PROJECT.md §6).
- [ ] Uniqueness (no duplicate `(geo, time)`), completeness (non-null threshold)
- [ ] Consistency (geo in valid set, single unit), accuracy (value in range)
- [ ] Results collected into one object for the report, per dataset

#### #13 Timeliness check (per-dataset thresholds)
`type: feature` · `area: validation` · `prio: P1` · `size: S` · `qa: timeliness` · **M3** · target 2026-08-07

- [ ] Latest `time` compared against the dataset's own staleness threshold (emissions lag!)
- [ ] Recent-year gaps detected; result added to the QA object

#### #14 Map each check to the 5 MSCI dimensions in the README
`type: docs` · `area: validation` · `prio: P1` · `size: S` · **M3** · target 2026-08-09

- [ ] Table: dimension → concrete check(s) → code location
- [ ] The headline artifact for a data-science cover letter

---

### M4 — Anomaly, visualization, report & CLI · due 2026-08-16

---

#### #15 Statistical z-score anomaly flags
`type: feature` · `area: anomaly` · `prio: P1` · `size: M` · `qa: accuracy` · **M4** · target 2026-08-11

- [ ] Per-`geo` z-score flags a `z_anomaly` column
- [ ] Works on both datasets; a planted outlier is caught

#### #16 scikit-learn IsolationForest detector
`type: feature` · `area: anomaly` · `prio: P1` · `size: M` · **M4** · target 2026-08-12

- [ ] Feature includes year-over-year change; `if_anomaly` column produced
- [ ] README paragraph on *why* IsolationForest works (ties to ML course)
- [ ] Note where z-score and IsolationForest agree/disagree

#### #17 Visualizations: choropleth map + emission trends
`type: feature` · `area: reporting` · `prio: P1` · `size: L` · **M4** · target 2026-08-14

- [ ] `viz` builds a **geopandas choropleth** for `demo_r_d2jan` (NUTS 2 geometries joined on `geo`)
- [ ] Trend-line figure for `env_air_gge`, anomalies annotated
- [ ] Figures saved to `reports/`, each self-explanatory (title, legend, source)

#### #18 HTML/markdown quality report (both datasets)
`type: feature` · `area: reporting` · `prio: P0` · `size: L` · **M4** · target 2026-08-15

- [ ] Assembles per-dimension pass/fail, flagged rows, and the figures
- [ ] Headline result readable by a non-technical viewer
- [ ] Separate section per dataset (or a combined summary)

#### #19 CLI entry point
`type: feature` · `area: reporting` · `prio: P0` · `size: M` · **M4** · target 2026-08-16

- [ ] `python -m eurostat_dq.cli --dataset <code>` runs the full pipeline
- [ ] `--dataset all` runs both; sensible default
- [ ] One-line summary printed on completion

---

### M5 — Testing, CI/CD, docs & release · due 2026-08-23

---

#### #20 Unit tests for schema and cleaning
`type: test` · `area: validation` · `prio: P0` · `size: M` · **M5** · target 2026-08-19

- [ ] `test_schema.py`: valid record + each failure mode + missing-value rule
- [ ] `test_clean.py`: wide→long shape, `:`→NaN, `apply_slice` keeps the right rows
- [ ] Uses small hand-made fixtures (no API calls); `pytest` green

#### #21 Tests for anomaly detection
`type: test` · `area: anomaly` · `prio: P1` · `size: S` · **M5** · target 2026-08-20

- [ ] Planted outlier flagged by both detectors; clean data not flagged

#### #22 GitHub Actions CI running pytest
`type: infra` · `area: ci-cd` · `prio: P1` · `size: M` · **M5** · target 2026-08-21

- [ ] Workflow installs deps and runs `pytest` on push + PR
- [ ] Green build badge in the README

#### #23 Complete the README
`type: docs` · `area: repo` · `prio: P0` · `size: M` · **M5** · target 2026-08-22

- [ ] Description, setup, usage, quality-dimension table
- [ ] The choropleth + a trend figure embedded
- [ ] Tech list + "what this demonstrates" paragraph for recruiters

#### #24 Docstrings & type hints pass
`type: docs` · `area: repo` · `prio: P2` · `size: S` · **M5** · target 2026-08-22

- [ ] Public functions documented + type-hinted; dead code/debug prints removed

#### #25 Tag v1.0 release and update CV
`type: docs` · `area: repo` · `prio: P1` · `size: S` · **M5** · target 2026-08-23

- [ ] Git tag `v1.0.0` + GitHub release notes
- [ ] Add project to the data-science CV with the real link
- [ ] Add pandas/scikit-learn/geopandas to CV skills — now they're real

---

## 4. Stretch backlog (only if ahead of schedule)

- `type: feature` `area: ingestion` `prio: P2` — A **third** dataset through the same registry (proves the abstraction generalizes)
- `type: infra` `prio: P2` — **Dockerfile** for reproducibility
- `type: feature` `area: anomaly` `prio: P2` — Track anomaly runs with **MLflow**
- `type: feature` `area: reporting` `prio: P2` — Per-region **quality score** rendered on the choropleth

---

## 5. `gh` upsert script

Run from inside the cloned `eurostat-dq` repo (needs the GitHub CLI, `gh auth login`).
This version is **idempotent**: labels use `--force`, milestones and issues are matched by
title and **updated if they exist, created if not** — so you can re-run it after plan
changes. Only the M1 issues are included for now (ask to add M2–M5 when ready).

```bash
#!/usr/bin/env bash
set -euo pipefail

# ---------- Labels (idempotent via --force) ----------
create_label () { gh label create "$1" --color "$2" --description "$3" --force; }

create_label "type: feature"      "1D76DB" "New capability / code"
create_label "type: infra"        "5319E7" "Setup, tooling, packaging, CI"
create_label "type: test"         "0E8A16" "Tests and test data"
create_label "type: docs"         "C2E0C6" "Documentation"
create_label "type: research"     "FBCA04" "Investigate before coding"
create_label "type: bug"          "D73A4A" "Something is broken"
create_label "type: refactor"     "BFDADC" "Improve code, same behaviour"

create_label "area: repo"         "EDEDED" "Repo structure, env, packaging"
create_label "area: ingestion"    "006B75" "Registry + Eurostat API to raw data"
create_label "area: cleaning"     "0052CC" "Raw to tidy to per-dataset slice"
create_label "area: validation"   "B60205" "pydantic + great_expectations"
create_label "area: anomaly"      "E99695" "scikit-learn outlier detection"
create_label "area: reporting"    "FEF2C0" "Visualization, report + CLI"
create_label "area: ci-cd"        "5319E7" "GitHub Actions, automation"

create_label "prio: P0"           "B60205" "Blocker"
create_label "prio: P1"           "D93F0B" "Core deliverable"
create_label "prio: P2"           "FBCA04" "Nice-to-have"

create_label "size: S"            "C2E0C6" "< 2 hours"
create_label "size: M"            "FEF2C0" "half a day"
create_label "size: L"            "F9D0C4" "a full day or more"

for dim in completeness uniqueness consistency accuracy timeliness; do
  create_label "qa: ${dim}" "BFD4F2" "QA dimension: ${dim}"
done

# ---------- Milestones (upsert: update if title exists, else create) ----------
upsert_ms () {
  local title="$1" due="$2" desc="$3" num
  num=$(gh api "repos/{owner}/{repo}/milestones?state=all" \
        --jq "map(select(.title==\"$title\")) | .[0].number // empty")
  if [ -n "$num" ]; then
    gh api -X PATCH "repos/{owner}/{repo}/milestones/$num" \
      -f title="$title" -f due_on="$due" -f description="$desc" >/dev/null
    echo "updated milestone: $title"
  else
    gh api -X POST "repos/{owner}/{repo}/milestones" \
      -f title="$title" -f due_on="$due" -f description="$desc" >/dev/null
    echo "created milestone: $title"
  fi
}

upsert_ms "M1 Setup, registry & ingestion"        "2026-07-19T23:59:59Z" "Repo, env, dataset registry, generic fetch"
upsert_ms "M2 Cleaning & EDA"                     "2026-07-26T23:59:59Z" "Tidy + per-dataset slice + EDA notebook"
upsert_ms "M3 Validation layer"                   "2026-08-09T23:59:59Z" "pydantic + GX across 5 QA dimensions (2 weeks)"
upsert_ms "M4 Anomaly, visualization, report & CLI" "2026-08-16T23:59:59Z" "z-score + IsolationForest, choropleth + trends, report, CLI"
upsert_ms "M5 Testing, CI/CD, docs & release"     "2026-08-23T23:59:59Z" "pytest, GitHub Actions, README, v1.0 tag"

# ---------- Issues (upsert; GitHub issues have no due field -> Target in body) ----------
upsert_issue () {
  # usage: upsert_issue "title" "body" "milestone" label1 label2 ...
  local title="$1" body="$2" milestone="$3"; shift 3
  local create_labels=() edit_labels=()
  for l in "$@"; do create_labels+=(--label "$l"); edit_labels+=(--add-label "$l"); done
  local num
  num=$(gh issue list --search "in:title \"$title\"" --state all --json number,title \
        --jq "map(select(.title==\"$title\")) | .[0].number // empty")
  if [ -n "$num" ]; then
    gh issue edit "$num" --body "$body" --milestone "$milestone" "${edit_labels[@]}" >/dev/null
    echo "updated issue #$num: $title"
  else
    gh issue create --title "$title" --body "$body" --milestone "$milestone" "${create_labels[@]}" >/dev/null
    echo "created issue: $title"
  fi
}

M1="M1 Setup, registry & ingestion"

upsert_issue "Create repository skeleton and .gitignore" \
$'**Target:** 2026-07-13\n\nSet up the repo per PROJECT.md §2.\n\n- [ ] `src/eurostat_dq/` module stubs (`config`, `ingest`, `clean`, `schema`, `expectations`, `anomaly`, `viz`, `report`, `cli`)\n- [ ] `data/raw/`, `data/processed/`, `notebooks/`, `tests/`, `reports/` folders\n- [ ] `.gitignore` excludes `data/raw/`, `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`\n- [ ] Initial commit pushed to GitHub' \
"$M1" "type: infra" "area: repo" "prio: P0" "size: S"

upsert_issue "Set up virtual environment and dependencies" \
$'**Target:** 2026-07-14\n\n- [ ] `python -m venv .venv` and activate\n- [ ] Install: pandas, numpy, scipy, eurostat, requests, pydantic, great_expectations, scikit-learn, matplotlib, geopandas, jupyter, pytest, statsmodels\n- [ ] `pip freeze > requirements.txt` (or keep pyproject.toml authoritative)\n- [ ] Confirm geopandas imports (heavy geo deps — see PROJECT.md §2)' \
"$M1" "type: infra" "area: repo" "prio: P0" "size: S"

upsert_issue "Add project README stub and license" \
$'**Target:** 2026-07-15\n\n- [ ] One-paragraph description (mentions both datasets)\n- [ ] Placeholder sections: Setup, Usage, Quality dimensions, Results\n- [ ] MIT license present and referenced' \
"$M1" "type: docs" "area: repo" "prio: P1" "size: S"

upsert_issue "Design the dataset registry (both datasets)" \
$'**Target:** 2026-07-16\n\nDefine `config.py` so one pipeline serves both datasets (PROJECT.md §1).\n\n- [ ] Inspect `demo_r_d2jan` and `env_air_gge`: dimensions, codes, units\n- [ ] Per dataset record: code, dimension filters `{column: keep_value}`, valid geo set, value range, geography level, timeliness threshold\n- [ ] Capture as a dict/dataclass per dataset\n- [ ] Note regional-vs-country and inventory-lag differences in the README' \
"$M1" "type: research" "area: ingestion" "prio: P0" "size: M"

upsert_issue "Implement generic fetch_dataset() + caching" \
$'**Target:** 2026-07-19\n\n- [ ] `ingest.fetch_dataset(code)` returns a non-empty DataFrame for both codes\n- [ ] Raw pulls cached under `data/raw/{code}.parquet`; second call skips network\n- [ ] Network / bad-code errors handled cleanly (no raw traceback)\n- [ ] Smoke test prints shape + head for each dataset' \
"$M1" "type: feature" "area: ingestion" "prio: P0" "size: M"

upsert_issue "Add raw REST/JSON-stat fetch as an alternative" \
$'**Target:** 2026-07-19 (P2 — slip first if the week is tight)\n\n- [ ] `fetch_dataset_json(code, **filters)` hits the REST API with `requests`\n- [ ] Parses JSON-stat into the same tidy shape as fetch_dataset()\n- [ ] README note on the two paths' \
"$M1" "type: feature" "area: ingestion" "prio: P2" "size: L"

echo "Done. Labels, milestones, and M1 issues are up to date (M2-M5 issues: add when ready)."
```
