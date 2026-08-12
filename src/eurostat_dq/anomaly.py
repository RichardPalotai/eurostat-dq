import pandas as pd
from sklearn.ensemble import IsolationForest
import numpy as np

def zscore_flags(df: pd.DataFrame, threshold=3.0) -> pd.DataFrame:
    df = df.copy()
    grp = df.groupby("geo")["value"]
    df["z"] = (df["value"] - grp.transform("mean")) / grp.transform("std")
    df["z_anomaly"] = df["z"].abs() > threshold
    return df

def isolation_forest(df: pd.DataFrame) -> pd.DataFrame:
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