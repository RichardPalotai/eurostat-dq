import pandas as pd
from .config import DatasetConfig, PROJECT_ROOT

def to_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Reshapes the Eurostat dataset's pandas DataFrame from Wide to Long structure (Year column turns into Time and Value columns).
    
    Expects wide package output; long input is returned unchanged."""
    df = df.rename(columns=lambda c: str(c).split("\\")[0] if str(c).endswith("\\TIME_PERIOD") else str(c))
    year_dims = [dim for dim in df.columns if str(dim).isdigit()]
    if not year_dims:
        return df

    base_dims = [dim for dim in df.columns if not str(dim).isdigit()]
    df_long = (df.melt(id_vars=base_dims, var_name="time", value_name="value").dropna(subset=["value"]))
    df_long["time"] = df_long["time"].astype(int)
    return df_long.sort_values(by=['time', 'geo'], ascending=[True, True])

def apply_slice(df: pd.DataFrame, cfg: DatasetConfig) -> pd.DataFrame:
    """Applies slicing to the Pandas DataFrame after fetch_dataset() and to_tidy()"""
    filters = cfg.filters
    geo_level = cfg.geo_level.lower()

    geo_data = sorted(df["geo"].unique())
    geo_data_leveled = []

    if geo_level == "nuts2":
        geo_data_leveled = sorted({g for g in geo_data if len(g) == 4 and not g.endswith(("ZZ", "XX")) and not g.startswith(("EU", "EA")) and not g.isalpha()})
    elif geo_level == "country":
        geo_data_leveled = sorted(set([g for g in geo_data if len(g) == 2]))

    mask = pd.Series(True, index=df.index)
    mask &= df["geo"].isin(geo_data_leveled)
    for col, val in filters.items():
        mask &= df[col] == val
    df = df[mask]

    cache_path = PROJECT_ROOT / "data" / "processed" / f"{cfg.code}.parquet"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, index=False)

    return df