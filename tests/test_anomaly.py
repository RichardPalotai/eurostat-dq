import pandas as pd
import pytest

from eurostat_dq.anomaly import zscore_flags, isolation_forest


@pytest.fixture
def spike():
    # one geo, a long stable history + a single obvious spike.
    # (Need enough points: with few, an outlier inflates its own std and
    #  can't reach |z| > 3 — max |z| = (n-1)/sqrt(n).)
    years = list(range(1990, 2015))          # 25 years
    values = [100.0] * 24 + [1000.0]         # last year spikes
    return pd.DataFrame({"geo": "A", "time": years, "value": values})


@pytest.fixture
def calm():
    # one geo, mild noise, no outlier
    years = list(range(1990, 2015))
    values = [100.0 + (i % 3) for i in range(25)]   # 100/101/102 repeating
    return pd.DataFrame({"geo": "A", "time": years, "value": values})


@pytest.fixture
def jump():
    # steady ~2%/yr growth with one sudden doubling — an anomalous *change*
    years = list(range(1990, 2021))          # 31 years
    values = [1000.0 * (1.02 ** i) for i in range(31)]
    values[15] *= 2                          # year 2005: sudden jump
    return pd.DataFrame({"geo": "G", "time": years, "value": values})


# ---- z-score ----

def test_zscore_flags_planted_spike(spike):
    out = zscore_flags(spike)
    spike_row = out[out["time"] == 2014]
    assert spike_row["z_anomaly"].item() is True          # the spike is caught
    assert out[out["time"] < 2014]["z_anomaly"].sum() == 0  # nothing else


def test_zscore_no_false_positives_on_calm(calm):
    out = zscore_flags(calm)
    assert out["z_anomaly"].sum() == 0                    # threshold-based -> can be zero


# ---- IsolationForest ----

def test_isolation_forest_flags_planted_jump(jump):
    out = isolation_forest(jump)
    # the sudden doubling in 2005 should be among the flagged rows
    assert out[out["time"] == 2005]["if_anomaly"].item() is True
    # first year has no pct_change -> unscored (NaN), not flagged
    assert pd.isna(out[out["time"] == 1990]["if_score"].item())
