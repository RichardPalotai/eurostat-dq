import pytest
import pandas as pd
from pandas.testing import assert_frame_equal

from eurostat_dq.clean import to_tidy, apply_slice
from eurostat_dq.config import DatasetConfig


@pytest.fixture
def wide():
    return pd.DataFrame({
        "unit": ["NR", "NR", "NR"],
        "sex": ["F", "F", "F"],
        "age": ["TOTAL", "TOTAL", "TOTAL"],
        "geo": ["AL", "AL0", "AL01"],
        "1990": [1.0, 2.0, 3.0],
        "2020": [10.0, 20.0, 30.0],
    })


@pytest.fixture
def long():
    return pd.DataFrame([
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL",   "time": 1990, "value": 1.0},
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL0",  "time": 1990, "value": 2.0},
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL01", "time": 1990, "value": 3.0},
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL",   "time": 2020, "value": 10.0},
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL0",  "time": 2020, "value": 20.0},
        {"unit": "NR", "sex": "F", "age": "TOTAL", "geo": "AL01", "time": 2020, "value": 30.0},
    ])


@pytest.fixture
def cfg():
    return DatasetConfig(
        code="test",
        filters={"sex": "F", "age": "TOTAL"},
        valid_geo={"AL01"},                 # only the real NUTS 2 code
        value_range=(0.0, 1000.0),
        geo_level="nuts2",
        staleness_years=1,
    )


def test_wide_to_long(wide, long):
    tidy = to_tidy(wide)
    assert_frame_equal(tidy, long, check_dtype=False)


def test_apply_slice_keeps_only_valid_region(wide, cfg):
    out = apply_slice(to_tidy(wide), cfg)
    # AL (country) and AL0 (NUTS 1) are dropped; only length-4 AL01 survives
    assert set(out["geo"]) == {"AL01"}
    # and it never keeps anything outside valid_geo (the invariant that caught real bugs)
    assert set(out["geo"]) <= set(cfg.valid_geo)
