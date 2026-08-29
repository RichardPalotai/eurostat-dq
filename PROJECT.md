# Eurostat Data-Quality Pipeline — Build Guide

> A **guide**, not a solution. It points you in the right direction — the concepts,
> the tools to reach for, the design decisions to make, and the acceptance criteria to
> hit — but it deliberately does **not** hand you finished code. The thinking (and the
> learning) is the point. Where you see a function signature, treat it as a contract to
> fulfil, not code to copy: the body is yours to write.

**How to use this file:** open it in VS Code (`Cmd+Shift+V` for preview). Work milestone
by milestone using [PROJECT_PLAN.md](PROJECT_PLAN.md) for scheduling and issues; use this
file for the *how-to-think* on each piece.

---

## 0. At a glance

This project builds one pipeline that ingests **two** Eurostat datasets, cleans them,
validates them across the five data-quality dimensions MSCI names, flags anomalies, and
produces a report + visualizations.

- **Datasets:** `demo_r_d2jan` (population, regional/NUTS 2) **and** `env_air_gge` (greenhouse-gas emissions, country)
- **Why two:** it forces a **config-driven, generalizable** design — the single most
  valuable engineering lesson here. A pipeline that only handles one hard-coded dataset
  is a script; one that handles two through a shared abstraction is a *system*.
- **Skills exercised:** pandas/numpy, pydantic, great_expectations, scikit-learn,
  geopandas, matplotlib, pytest, Git/CI.

### Progress overview
- [ ] **M1** — Repo, environment, dataset registry, ingestion
- [ ] **M2** — Cleaning (tidy + per-dataset filtering) & EDA
- [ ] **M3** — Validation layer (5 QA dimensions)
- [ ] **M4** — Anomaly detection, visualization, report & CLI
- [ ] **M5** — Tests, CI, docs, release

---

## 1. The two datasets — and the registry idea

You are handling two datasets that look different on the surface but share a core shape
(`geo`, `time`, `value`) once cleaned. The trick is to **describe** their differences as
*data*, not to fork your code for each one.

| | `demo_r_d2jan` | `env_air_gge` |
|---|---|---|
| Meaning | Population on 1 Jan | GHG emissions |
| Geography | NUTS 2 **regions** | **countries** |
| Extra dimensions to collapse | `age`, `sex` | `airpol`, `src_crf` |
| Natural valid range | ≥ 0, no wild jumps | ≥ 0 |
| Timeliness expectation | fairly current | inventories lag ~1–2 years |
| Best visual | **choropleth map** | **trend lines** |

**Design task (do this first, on paper):** what would a small "dataset registry" need to
record so the *same* ingest/clean/validate code can serve both? Think about: the dataset
code, which extra dimensions to filter and to what value, the set of valid `geo` codes,
the plausible value range, the geography level (country vs region), and how stale is "too
stale". You'll likely land on a dict or a small dataclass per dataset. **Don't over-design
it** — start with the two datasets you have.

> Learning pointer: browse each dataset on the Eurostat site (search the code) to see its
> real dimensions and codes before you decide what to filter. The `eurostat` package also
> has helpers to list a dataset's dimensions — find them.

---

## 2. Repo structure & environment

Target layout (you've largely built this already):

```
eurostat-dq/
├── src/eurostat_dq/
│   ├── config.py        # the dataset registry lives here
│   ├── ingest.py        # API → raw DataFrame
│   ├── clean.py         # raw → tidy → per-dataset slice
│   ├── schema.py        # pydantic models (row-level)
│   ├── expectations.py  # dataset-level QA (5 dimensions)
│   ├── anomaly.py       # scikit-learn + statistical flags
│   ├── viz.py           # choropleth + trend plots
│   ├── report.py        # assemble the report
│   └── cli.py           # run the whole thing
├── notebooks/01_eda.ipynb
├── tests/
└── reports/
```

**Environment:** `pyproject.toml` is authoritative; install with `pip install -e ".[dev]"`.
Currently declared: eurostat, pandas, pyarrow, numpy, pydantic, great_expectations,
scikit-learn, matplotlib, geopandas (+ pytest, jupyter, ipykernel as dev extras).

> **Keep declared deps and real imports in sync.** The moment you `import` something new
> in `src/`, add it to `pyproject.toml` in the same commit — otherwise it works on your
> machine and breaks in CI, which installs only what you declared. `pyarrow` (needed by
> `to_parquet`) already caught you out once this way.
>
> Two you'll need later but haven't declared yet: **`requests`** (for the §3 stretch,
> issue #6) and **`scipy`** if you reach for it in §7a.

---

## 3. Ingestion (`ingest.py`, `config.py`)

**Goal:** one function that fetches *any* dataset in your registry and caches it, so you
never hammer the API twice for the same data.

Think about the interface first:

```python
def fetch_dataset(code: str, *, use_cache: bool = True) -> pd.DataFrame:
    """Fetch a Eurostat dataset by code; cache raw pulls under data/raw/."""
    ...
```

Questions to answer as you implement:
- Which `eurostat` function returns a dataframe? (Look it up — there's a direct one.)
- Where does the cache live, and how do you decide "already cached"? (A parquet file
  named after the code is a fine start.)
- What happens when the network is down or the code is wrong — does your function crash,
  or return a clear error? Decide and handle it.

**Acceptance:** `fetch_dataset` returns a non-empty DataFrame for both dataset codes, and
a second call reads from cache (observably faster / no network).

**Where the shape contract lives.** The two fetch paths disagree naturally:
`eurostat.get_data_df()` returns **wide** (years as columns), while JSON-stat decodes to
**long** (one row per cell). That is fine — **`ingest` is the raw layer**, and raw means
*as the source gave it*. If `ingest` reshaped, `data/raw/` would no longer be raw.

The contract belongs one layer down, at **`clean`'s output**: whatever shape arrives, it
leaves as canonical **long** (`…dims…, time, value`). That is what `data/processed/` holds.
Downstream code still cannot tell which fetcher ran — it just finds out at the boundary
that exists for exactly this purpose. So `to_tidy` (§4 Stage A) is the **wide-path
adapter**, not a mandatory stage.

**Stretch (P2):** a `requests`-based fetch against the JSON-stat REST endpoint. Genuinely
educational — the format is a serialized n-dimensional cube (`id`/`size`/`dimension` +
a **sparse** `value` dict keyed by flat index), so you do the unflattening yourself.
Reverse-engineer a real response in the notebook before writing code, and note that
filtering server-side via query params cuts the payload ~60x. Don't block the project on it.

---

## 4. Cleaning (`clean.py`)

Two stages. Keep them separate — they're different concerns.

**Stage A — tidy (generic, shared by both datasets).** Eurostat arrives *wide* (a column
per year). You want it *long*: one row per `(…dimensions…, time, value)`.
- Which pandas function reshapes wide→long? (You've used its inverse before.)
- How will you tell a "year" column from a dimension column, programmatically?
- Eurostat encodes missing values as `:` — what should those become, and which pandas
  function coerces text to numbers while turning junk into `NaN`?

**Stage B — per-dataset filtering (uses the registry).** Each dataset has extra
dimensions you must collapse to get a comparable `geo × time × value` slice — e.g. pick
the *total* age group and *both sexes* for population, the *total* gas and *total* sector
for emissions. Drive this from the registry config, not hard-coded `if dataset == …`.

```python
def to_tidy(df: pd.DataFrame) -> pd.DataFrame: ...
def apply_slice(df: pd.DataFrame, cfg: DatasetConfig) -> pd.DataFrame: ...
```

**Design question:** how do you keep `apply_slice` generic when the two datasets filter on
*different* column names? (Hint: the registry can store `{column: keep_value}` pairs.)

**Acceptance:** both datasets end up as a clean `geo, time, value` frame saved under
`data/processed/`, with the right rows kept and `:` handled.

---

## 5. Row-level validation with pydantic (`schema.py`)

**Concept:** pydantic lets you declare a typed model with *validators* — small functions
that run on assignment and reject bad values. This is your **accuracy** and part of your
**consistency** dimension, checked one record at a time.

Research these pydantic ideas before writing:
- how you declare a model and typed fields,
- the decorator that turns a method into a per-field validator,
- how validation *errors* are represented so you can collect rather than crash on them.

Design decisions that are yours to make:
- What makes a `geo` code valid — and note this **differs per dataset** (NUTS 2 region
  codes vs country codes). How does your model know which set to check against? (The
  registry again.)
- Is a *missing* value (`None`) invalid, or a legitimate known gap? Pick a rule and write
  it down — this choice ripples into your completeness metric later.
- What's a plausible year? A plausible value?

```python
class Record(BaseModel):
    geo: str
    time: int
    value: float | None
    # add validators; decide how the valid-geo set is injected
```

**Then:** a runner that validates a whole frame and returns `(valid, errors)` without
throwing, with errors structured enough to show in the report.

**Acceptance:** valid rows pass; each failure mode (negative, unknown geo, impossible
year) is rejected; missing-value rule behaves as you documented.

---

## 6. Dataset-level QA — the 5 dimensions (`expectations.py`)

This is the heart of the project and the part that mirrors the MSCI role. Map each
dimension to a concrete, runnable check:

| Dimension | What to check (design your own thresholds) |
|---|---|
| **Completeness** | share of non-null `value`; are all expected `geo × year` cells present? |
| **Uniqueness** | no duplicate `(geo, time)` keys |
| **Consistency** | every `geo` in the dataset's valid set; one `unit`; year ordering sane |
| **Accuracy** | `value` numeric and within the registry's plausible range |
| **Timeliness** | latest `time` recent enough — **and note the two datasets have different expectations** (emissions inventories lag) |

**Two ways to implement — your call:**
1. **great_expectations** — stronger CV signal, steeper learning curve. Research: how you
   get a "batch" from a DataFrame and which built-in *expectations* match the checks
   above (there are expectations for uniqueness, non-null, value ranges, value sets).
2. **Plain functions** returning a results dict — full control, trivially testable. A
   perfectly respectable fallback if GX's API fights you.

Whichever you pick, **collect all results into one object** the report can render, and
**document which check maps to which dimension** — that mapping table is the single most
quotable artifact for a data-science cover letter.

> Reality check: GX changes its API across versions. Budget time, and don't be too proud
> to fall back to plain functions — the QA *logic* is what demonstrates your skill.

---

## 7. Anomaly detection (`anomaly.py`)

Do the statistical baseline first (it builds on your Valstat/Nummod foundation), then the
ML method — and compare them.

**7a — statistical.** Flag values that are extreme relative to their own `geo`'s history.
- Which summary statistics define "extreme"? (Think z-score within a group.)
- Which pandas mechanism computes a per-group mean/std and broadcasts it back to rows?

**7b — scikit-learn `IsolationForest`.**
- What features feed it? Raw `value` alone is weak — what derived feature captures a
  *sudden* change? (Think year-over-year.)
- What does `contamination` mean and how does it change results?
- In one paragraph (for the README), *why* does isolating outliers take fewer random
  splits? Explaining this turns a library call into evidence you understand the algorithm.

**Acceptance:** both methods return the frame with a boolean flag column; a deliberately
planted outlier gets caught; you note where the two methods agree/disagree.

---

## 8. EDA notebook (`notebooks/01_eda.ipynb`)

Do this *alongside* cleaning — it's how you discover which QA rules and ranges matter.
Cover **both** datasets. Things worth plotting and writing a sentence about:
- distributions and null counts,
- a time series for a few regions/countries,
- a boxplot by year (reuse your R boxplot instinct, now in Python),
- anything weird — those become your test cases and your accuracy thresholds.

Write short markdown interpretations under each plot. "Communicate results" is literally
in the job description; this is where you practise it.

---

## 9. Visualization (`viz.py`)

You chose datasets that visualize well — lean into it.

**Population → choropleth map (geopandas).** This is the visually strongest output and the
MSCI geospatial "plus".
- You need region geometries (NUTS 2 boundaries) to join your data onto. Where do you get
  them, and on which key do they join to your `geo` codes? (Research Eurostat/GISCO NUTS
  geometry files.)
- What are you colouring — raw population, or something more meaningful like a per-region
  quality/anomaly score?

**Emissions → trend lines.** Simpler but effective: emissions over time for a handful of
countries, ideally annotated with any anomalies your detector flagged.

**Acceptance:** one map and one trend figure saved to `reports/`, each readable on its
own (title, legend, source note).

> Design pointer: read the repo's `dataviz` guidance before choosing colours — a clean,
> consistent palette makes a portfolio piece look professional.

---

## 10. Tests (`tests/`)

Test the *data logic*, not just that code runs. Ideas:
- schema: a valid record, plus each failure mode; the missing-value rule,
- cleaning: wide→long shape, `:`→NaN, per-dataset slice keeps the right rows,
- anomaly: a planted outlier is flagged; clean data isn't.

Think about **fixtures**: build tiny hand-made DataFrames with known answers rather than
hitting the API in tests. Why is that better for a test suite?

**Acceptance:** `pytest` green locally; tests fail loudly if you break a cleaning rule.

---

## 11. Orchestration, report & CLI (`report.py`, `cli.py`)

Tie it together so one command runs the whole thing for a chosen dataset.

```python
# cli: python -m eurostat_dq.cli --dataset demo_r_d2jan
#      python -m eurostat_dq.cli --dataset all
```

Think about:
- the pipeline order (ingest → clean → validate → anomaly → viz → report) and where each
  dataset's config enters,
- what a *non-technical* reader sees first in the report (headline pass/fail per
  dimension, then detail),
- how the report handles two datasets — separate sections, or a combined summary?

**Acceptance:** the command runs end-to-end for each dataset and writes an HTML report +
figures.

---

## 12. README & CV tie-in

- Lead the README with what it does and the **dimension→check mapping table**.
- Show the map and a trend figure.
- Add a "what this demonstrates" paragraph for recruiters.
- When it's working, add the project to your **data-science CV** with the real repo link,
  and only *then* add pandas/scikit-learn/geopandas to your CV skills — now they're real.

---

## 13. Stretch backlog (only if ahead)

- A **third** dataset through the same registry — proves the abstraction generalizes.
- **Dockerfile** for reproducibility.
- **MLflow** to track anomaly-model runs.
- A small per-region **quality score** rendered on the choropleth.

---

## Notes / scratch

_Log decisions, dataset quirks, and blockers here as you build._

-
