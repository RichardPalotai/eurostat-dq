import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

def zscore_flags(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """Flag values that are extreme relative to their own ``geo``'s history (statistical baseline).

    Standardises each value against the mean and standard deviation of *its own* ``geo``
    (per-geo, not global — a global z-score on this right-skewed data would flag large
    regions every year). A geo with too little history (< 2 points or zero variance) has an
    undefined std, so its ``z`` is ``NaN`` and it is left unflagged — never assumed normal.

    Args:
        df: A cleaned long frame with ``geo`` and ``value`` columns.
        threshold: Flag rows whose ``|z| >`` this value. Defaults to 3.0.

    Returns:
        A copy of ``df`` with two added columns: ``z`` (the score, ``NaN`` where unscorable)
        and ``z_anomaly`` (bool).
    """
    df = df.copy()
    grp = df.groupby("geo")["value"]
    df["z"] = (df["value"] - grp.transform("mean")) / grp.transform("std")
    df["z_anomaly"] = df["z"].abs() > threshold
    return df

def isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
    """Flag anomalous year-over-year *changes* with a scikit-learn IsolationForest.

    Fits on each geo's ``pct_change`` (relative change, comparable across regions of very
    different size) rather than the raw level. ``contamination=0.02`` flags roughly the 2%
    most isolated points; ``random_state`` is fixed for reproducibility. A geo's first year
    has no prior value, so its change is ``NaN``: those rows are excluded from the fit and
    left unscored (``if_score`` ``NaN``), mirroring the z-score's insufficient-history rule.

    Args:
        df: A cleaned long frame with ``geo``, ``time`` and ``value`` columns.

    Returns:
        A copy of ``df`` with added columns: ``pct`` (year-over-year change),
        ``if_score`` (anomaly score, lower = more anomalous, ``NaN`` where unscored) and
        ``if_anomaly`` (bool).
    """
    df = df.copy()

    iso_forest = IsolationForest(contamination=0.02, random_state=42)
    df = df.sort_values(["geo", "time"])
    df["pct"] = df.groupby("geo")["value"].pct_change()
    df["pct"] = df["pct"].replace([np.inf, -np.inf], np.nan)
    feat = df.dropna(subset=["pct"])
    scores = iso_forest.fit(feat[["pct"]]).decision_function(feat[["pct"]])

    df.loc[feat.index, "if_score"] = scores
    df["if_anomaly"] = df["if_score"] < 0

    return df