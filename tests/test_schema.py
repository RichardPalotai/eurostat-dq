import pytest
import pandas as pd
from pydantic import ValidationError

from eurostat_dq.config import DatasetConfig
from eurostat_dq.schema import Record, validate_rows


# A fixture: a small, self-contained config so tests don't depend on the real
# registry (which can change). pytest injects it into any test that names `cfg`.
@pytest.fixture
def cfg():
    return DatasetConfig(
        code="test",
        filters={},
        valid_geo={"HU11", "HU12"},
        value_range=(0.0, 1_000_000.0),
        geo_level="nuts2",
        staleness_years=1,
    )


# ---- Record: the happy path ----

def test_valid_record_passes(cfg):
    r = Record.model_validate({"geo": "HU11", "time": 2020, "value": 500.0}, context=cfg)
    assert r.geo == "HU11" and r.time == 2020 and r.value == 500.0


def test_none_value_allowed(cfg):
    # a missing value is a known gap, not a failure
    r = Record.model_validate({"geo": "HU11", "time": 2020, "value": None}, context=cfg)
    assert r.value is None


# ---- Record: each failure mode raises ValidationError ----

def test_negative_value_rejected(cfg):
    with pytest.raises(ValidationError):
        Record.model_validate({"geo": "HU11", "time": 2020, "value": -5.0}, context=cfg)


def test_value_above_range_rejected(cfg):
    with pytest.raises(ValidationError):
        Record.model_validate({"geo": "HU11", "time": 2020, "value": 9_999_999.0}, context=cfg)


def test_unknown_geo_rejected(cfg):
    with pytest.raises(ValidationError):
        Record.model_validate({"geo": "ZZ99", "time": 2020, "value": 5.0}, context=cfg)


def test_year_too_early_rejected(cfg):
    with pytest.raises(ValidationError):
        Record.model_validate({"geo": "HU11", "time": 1800, "value": 5.0}, context=cfg)


def test_year_in_future_rejected(cfg):
    with pytest.raises(ValidationError):
        Record.model_validate({"geo": "HU11", "time": 3000, "value": 5.0}, context=cfg)


# ---- validate_rows: collects failures instead of crashing ----

def test_validate_rows_counts_and_by_field(cfg):
    df = pd.DataFrame([
        {"geo": "HU11", "time": 2020, "value": 500.0},      # ok
        {"geo": "HU12", "time": 2021, "value": 600.0},      # ok
        {"geo": "ZZ99", "time": 2021, "value": 600.0},      # bad geo
        {"geo": "HU11", "time": 2021, "value": -1.0},       # bad value
    ])
    valid, errors, summary = validate_rows(df, cfg)

    assert summary["total"] == 4
    assert summary["passed"] == 2
    assert summary["failed"] == 2
    assert len(valid) == 2 and len(errors) == 2
    # the failures are attributed to the right fields
    assert summary["by_field"] == {"geo": 1, "value": 1}
