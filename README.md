# Eurostat data project
I dedicated this project to learn new Data Science skills and further my knowledge in this field via applying my theoretical insights to Statistics.

## Overwiev

**Core data wrangling**
> Packages: Pandas, NumPy

**Data ingestion**
> Packages: eurostat, requests

**Data validation / quality**
> Packages: pydantic, great_expectations

**Anomaly detection / ML**
> Packages: scikit-learn, scipy, statsmodels

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
| Valid `geo` | NUTS 2 codes (length 4, `…ZZ` dropped) | countries + `EU27_2020` aggregate |
| Value range (approx.) | `0 to 15,000,000` (persons) | `0 to 1,500,000` (kt CO₂-eq) |
| Timeliness threshold | ~2 years | ~3 years (inventories lag) |

**Key decisions & data quirks (noted while inspecting the data):**

- **`src_crf = TOTX4_MEMO`** = total GHG **excluding LULUCF** (land use / forestry) and
  memo items, the standard headline figure. LULUCF is volatile and can be negative, so
  it is excluded to keep the value range and anomaly detection clean.
- **NUTS country codes are not ISO:** Greece is `EL` (not `GR`) and the UK is `UK`
  (not `GB`). The country list uses these.
- **Regional datasets mix geography levels:** `demo_r_d2jan` contains country, NUTS 1,
  NUTS 2 and NUTS 3 rows together, so the pipeline filters to length-4 codes for true
  NUTS 2, and drops the `…ZZ` "extra-regio" (unassigned) codes.
- **Aggregates are excluded from anomaly detection:** `EU27_2020` (and similar) dwarf any
  single country, so they are kept for validation/trend context but filtered out before
  outlier detection.
- **Open question:** a population value of `0` appeared during exploration, flagged as a
  candidate data-quality issue / test case for the accuracy checks.

---

## Components
### Setup
N/A
### Usage
N/A
### Quality dimensions
N/A
### Results
N/A

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
