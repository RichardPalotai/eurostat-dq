# Eurostat data project

I dedicated this project to learn new Data Science skills and further my knowledge in this field via applying my theoretical insights to Statistics.

The pipeline ingests two Eurostat datasets, cleans them, validates them across five data-quality
dimensions (accuracy, completeness, consistency, uniqueness, timeliness), flags anomalies, and
produces a report.

## Overview

**Core data wrangling**
> Packages: pandas, NumPy

**Data ingestion**
> Packages: eurostat, requests

**Data validation / quality**
> Packages: pydantic, great_expectations

**Anomaly detection / ML**
> Packages: scikit-learn

**Exploration and reporting**
> Packages: Jupyter, matplotlib, geopandas

---

## Datasets

The pipeline handles **two** Eurostat datasets through a shared, config-driven design
(a "dataset registry" in `config.py`), so the same ingest/clean/validate code serves both.

| | `demo_r_d2jan` | `env_air_gge` |
|---|---|---|
| Meaning | Population on 1 January | Greenhouse-gas emissions |
| Geography | **NUTS 2 regions** (e.g. `HU11`) | **countries** (e.g. `HU`) |
| Dimension filters | `age = TOTAL`, `sex = T` | `airpol = GHG`, `src_crf = TOTX4_MEMO` |
| Valid `geo` | 346 NUTS 2 codes (length 4) | 31 country codes (length 2) |
| Value range | `0` to `15,907,951` (persons) | `1.84` to `1,253,128` (kt CO₂-eq) |
| Timeliness threshold | 2 years | 3 years (inventories lag) |

**Key decisions & data quirks (noted while inspecting the data):**

- **`src_crf = TOTX4_MEMO`** = total GHG **excluding LULUCF** (land use / forestry) and
  memo items, the standard headline figure. LULUCF is volatile and can be negative, so
  it is excluded to keep the value range and anomaly detection clean.
- **NUTS country codes are not ISO:** Greece is `EL` (not `GR`) and the UK is `UK`
  (not `GB`). The country list uses these.
- **Regional datasets mix geography levels:** `demo_r_d2jan` contains country, NUTS 1,
  NUTS 2 and NUTS 3 rows together, so the pipeline filters to length-4 codes for true
  NUTS 2.
- **Aggregates and unallocated residuals are excluded from `valid_geo`.** The unit of
  analysis is "one row = one NUTS 2 region", and these rows break that:
  - **Aggregates** (`EU28`, `EFTA`) are correct data at a *different level of
    aggregation*. Keeping them would double-count in any sum and stretch the accuracy
    range by ~30x (the EU28 total is ~514 million, versus ~15.9 million for the largest
    single region).
  - **`XX` residuals** (`ALXX`, `FRXX`, `HUXX`, `MKXX`) are population that could not be
    assigned to a specific region — legitimate, but not a region.

  Both are dropped during cleaning, *upstream* of validation, so `valid_geo` describes
  what survives cleaning rather than what Eurostat ships. This keeps the config internally
  consistent: if aggregates were valid geos but the value range only admitted a real
  region's population, an `EU28` row would pass the consistency check and fail the accuracy
  check — a false positive on perfectly correct data.
- **Open question:** a population value of `0` appeared during exploration, flagged as a
  candidate data-quality issue / test case for the accuracy checks.
- **Possible future metric:** the `XX` share per country measures how well a country's data
  is regionalized — a completeness signal worth reporting rather than silently dropping.

---

## Ingestion — two paths

`ingest.py` offers two ways to fetch a dataset. Both cache to `data/raw/` as Parquet and
skip the network on a cache hit (unless `use_cache=False`).

| | `fetch_dataset(code)` | `fetch_dataset_json(code, **filters)` |
|---|---|---|
| Source | `eurostat` package (`get_data_df`) | raw REST API + JSON-stat, parsed by hand |
| Shape returned | **wide** (one column per year) | **long** (one row per observation) |
| Filtering | none (whole dataset) | **server-side** via query params (`age="TOTAL"`, `geo="HU11"`, …) |
| Cache file | `{code}.parquet` | `{code}_json{_dim=value…}.parquet` |

```python
from eurostat_dq.ingest import fetch_dataset, fetch_dataset_json

wide = fetch_dataset("demo_r_d2jan")
long = fetch_dataset_json("demo_r_d2jan", age="TOTAL", sex="T", geo="HU11")
```

**Why a hand-written JSON-stat parser?** The REST response is a serialized n-dimensional
cube (`id` / `size` / `dimension` + a sparse `value` dict keyed by flat index), not rows.
The parser is dataset-agnostic: it reads the dimension order from `id` and decodes each
flat index with `numpy.unravel_index`, so the same code serves both datasets. Filtering
server-side keeps the payload small — an unfiltered `demo_r_d2jan` is megabytes, while the
sliced request is a fraction of that (and Eurostat rejects overly large queries with HTTP
413, so filtering is required for wide dimensions).

**Note:** `fetch_dataset_json` caches the *decoded* DataFrame (Parquet), so the raw
JSON-stat metadata — publication timestamp (`updated`) and per-cell status flags
(`b` break, `p` provisional, `e` estimated) — is not retained. Those would be useful for
the timeliness and anomaly steps later; capturing them is a possible future change
(cache the raw JSON instead).

## Components

### Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Usage

_Not implemented yet — the CLI arrives with the reporting milestone._

```bash
# planned:
python -m eurostat_dq.cli --dataset demo_r_d2jan
python -m eurostat_dq.cli --dataset all
```

### Quality dimensions

_Not implemented yet._ Each of the five dimensions maps to concrete checks:

| Dimension | Planned check |
|---|---|
| Completeness | share of non-null `value`; expected `geo × year` cells present |
| Uniqueness | no duplicate `(geo, time)` keys |
| Consistency | every `geo` in the dataset's `valid_geo`; single `unit` |
| Accuracy | `value` numeric and within the registry's `value_range` |
| Timeliness | latest `time` within the dataset's `staleness_years` |

### Results

_Not implemented yet._

---

## Status

| Component | State |
|---|---|
| `config.py` — dataset registry | ✅ done |
| `ingest.py` — `fetch_dataset` (package, wide) + parquet cache | ✅ done |
| `ingest.py` — `fetch_dataset_json` (REST + JSON-stat, long) | ✅ done |
| `clean.py` — tidy + per-dataset slice | ⬜ next |
| `schema.py` — pydantic row validation | ⬜ |
| `expectations.py` — 5 QA dimensions | ⬜ |
| `anomaly.py` — z-score + IsolationForest | ⬜ |
| `viz.py` — map + trend figures | ⬜ |
| `report.py` / `cli.py` | ⬜ |

See [PROJECT.md](PROJECT.md) for the build guide and [PROJECT_PLAN.md](PROJECT_PLAN.md) for
milestones and issues.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
