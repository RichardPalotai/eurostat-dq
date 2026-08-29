import great_expectations as gx
from great_expectations.data_context.types.base import ProgressBarsConfig
import pandas as pd
from .config import DatasetConfig
from datetime import datetime

DIMENSION = {
    "expect_compound_columns_to_be_unique":           "uniqueness",
    "expect_column_values_to_not_be_null":            "completeness",
    "expect_column_values_to_be_in_set":              "consistency",
    "expect_column_unique_value_count_to_be_between": "consistency",
    "expect_column_values_to_be_between":             "accuracy",
}

def run_expectations(df: pd.DataFrame, cfg: DatasetConfig) -> dict:
    """Run the dataset-level quality checks and return a report keyed by quality dimension.

    Builds a great_expectations suite covering uniqueness, completeness, consistency and
    accuracy (all thresholds from the registry), plus a hand-rolled timeliness check
    (great_expectations has no recency expectation). Each expectation is mapped to one of the
    five dimensions via ``DIMENSION``.

    Args:
        df: A cleaned long frame for a single dataset.
        cfg: The dataset's registry entry (supplies ``value_range``, ``valid_geo``,
            ``staleness_years``).

    Returns:
        A dict keyed by dimension → check name → result, where each result holds
        ``passed``/``checked``/``failed``/``failed_pct``/``sample_bad`` (or, for timeliness,
        ``passed``/``latest``/``age``/``threshold``). JSON-serialisable, ready for the report.
    """
    context = gx.get_context()
    context.variables.progress_bars = ProgressBarsConfig(metric_calculations=False)

    batch = (
        context.data_sources.add_pandas("src")
        .add_dataframe_asset("asset")
        .add_batch_definition_whole_dataframe("batch")
        .get_batch(batch_parameters={"dataframe": df})
    )

    lo, hi = cfg.value_range

    suite = gx.ExpectationSuite(name=f"{cfg.code}_quality")
    suite.add_expectation(gx.expectations.ExpectCompoundColumnsToBeUnique(column_list=["geo", "time"]))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="value", mostly=0.90))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeInSet(column="geo", value_set=sorted(cfg.valid_geo)))
    suite.add_expectation(gx.expectations.ExpectColumnUniqueValueCountToBeBetween(column="unit", min_value=1, max_value=1))
    suite.add_expectation(gx.expectations.ExpectColumnValuesToBeBetween(column="value", min_value=lo, max_value=hi))

    results = batch.validate(suite)

    report = {
    "uniqueness":   {},
    "completeness": {},
    "consistency":  {},
    "accuracy":     {},
    "timeliness":   {},
    }

    for r in results.results:
        etype = r.expectation_config.type
        dim = DIMENSION[r.expectation_config.type]
        report[dim][etype] = {
            "passed":     r.success,
            "checked":    r.result.get("element_count"),
            "failed":     r.result.get("unexpected_count"),
            "failed_pct": r.result.get("unexpected_percent"),
            "sample_bad": r.result.get("partial_unexpected_list", [])[:5],
        }

    latest = int(df["time"].max())
    age = datetime.now().year - latest
    report["timeliness"]["staleness"] = {
        "passed": age <= cfg.staleness_years,
        "latest": latest,
        "age": age,
        "threshold": cfg.staleness_years
    }

    return report