import pandas as pd
from .config import DatasetConfig, PROJECT_ROOT

def to_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Reshape a Eurostat frame from wide (one column per year) to long (one row per observation).

    Detects year columns programmatically, melts them into ``time`` and ``value`` columns,
    drops the resulting missing values, and coerces ``time`` to ``int``. The
    ``geo\\TIME_PERIOD`` marker column produced by the ``eurostat`` package is renamed to
    ``geo``. This is the wide-path adapter: input that is already long (no year columns) is
    returned unchanged, so callers need not know which fetcher produced ``df``.

    Args:
        df: A Eurostat dataset, wide (from ``fetch_dataset``) or already long.

    Returns:
        A long DataFrame with columns ``[…dimensions…, geo, time, value]``, sorted by
        ``(time, geo)``.
    """
    df = df.rename(columns=lambda c: str(c).split("\\")[0] if str(c).endswith("\\TIME_PERIOD") else str(c))
    year_dims = [dim for dim in df.columns if str(dim).isdigit()]
    if not year_dims:
        return df

    base_dims = [dim for dim in df.columns if not str(dim).isdigit()]
    df_long = (df.melt(id_vars=base_dims, var_name="time", value_name="value").dropna(subset=["value"]))
    df_long["time"] = df_long["time"].astype(int)
    return df_long.sort_values(by=['time', 'geo'], ascending=[True, True])

def apply_slice(df: pd.DataFrame, cfg: DatasetConfig) -> pd.DataFrame:
    """Reduce a tidy frame to the one comparable ``geo × time × value`` slice for a dataset.

    Runs after ``to_tidy``. Two filters, both driven by the registry:

    1. **Dimension collapse** — keep only rows matching every ``cfg.filters`` pair
       (e.g. ``age=TOTAL, sex=T``), removing the extra dimensions.
    2. **Geo by structure** — keep only codes of the right *shape* for ``cfg.geo_level``
       (length-4 NUTS 2 codes, excluding aggregates/residuals; or length-2 country codes).
       This is deliberately a *structural* rule, not a ``valid_geo`` membership test — that
       stays in validation so the consistency check is not tautological.

    The result is cached to ``data/processed/{code}.parquet``.

    Args:
        df: A tidy (long) frame from ``to_tidy``.
        cfg: The dataset's registry entry (supplies ``filters`` and ``geo_level``).

    Returns:
        The sliced DataFrame (also written to ``data/processed/``).
    """
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