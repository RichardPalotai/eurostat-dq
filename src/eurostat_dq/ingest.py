import eurostat
import pandas as pd
import numpy as np
import geopandas as gpd
import requests
from .config import PROJECT_ROOT, BASE_REQUEST_URL, GISCO_NUTS_URL

def fetch_nuts_geometry(year: str = "2024", *, use_cache: bool = True) -> gpd.GeoDataFrame:
    """Fetch NUTS 2 region geometry (GISCO) as a GeoDataFrame, cached under data/reference/.

    Reference data — versioned and stable — so the cached file is meant to be committed,
    unlike the gitignored data/raw/ dataset cache. Mirrors fetch_dataset's use_cache pattern.
    """
    cache_path = PROJECT_ROOT / "data" / "reference" / f"nuts2_{year}_3035.parquet"
    if use_cache and cache_path.exists():
        print("NUTS geometry found in cache")
        return gpd.read_parquet(cache_path)

    resp = requests.get(GISCO_NUTS_URL.format(year=year), timeout=60)
    resp.raise_for_status()
    print("NUTS geometry acquired from the internet")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(resp.content)
    print("NUTS geometry saved to cache")
    return gpd.read_parquet(cache_path)

def fetch_dataset(code: str, *, use_cache: bool = True) -> pd.DataFrame:
    """Fetches dataset with eurostat.get_data_df and if use_cache=True it searches the data/raw folder first before fetching from the web"""
    cache_path = PROJECT_ROOT / "data" / "raw" / f"{code}.parquet"
    if (use_cache and cache_path.exists()):
        print("DataFrame found in cache")
        return pd.read_parquet(cache_path)
    else:
        df = eurostat.get_data_df(code)
        print("DataFrame acquired from the internet")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)
        print("DataFrame saved to cache")
        return df
    
def fetch_dataset_json(code: str, *, use_cache: bool = True, **filters) -> pd.DataFrame:
    """Fetches dataset with JSON-stat to flat dataset converter and if use_cache=True it searches the data/raw folder first before fetching from the web.

    Pass filters as keyword arguments, e.g. fetch_dataset_json("demo_r_d2jan", age="TOTAL", geo="HU11").
    (format and lang are given)"""

    def _fmt(v):
        return "+".join(map(str, v)) if isinstance(v, (list, tuple)) else str(v)
    filters_label = "".join(f"_{k}={_fmt(filters[k])}" for k in sorted(filters))

    # Update "filters" with mandatory request params (not part of the cache key)
    filters.update({"format": "JSON", "lang": "en"})

    cache_path = PROJECT_ROOT / "data" / "raw" / f"{code}_json{filters_label}.parquet"
    if (use_cache and cache_path.exists()):
        print("DataFrame found in cache")
        return pd.read_parquet(cache_path)
    else:
        resp = requests.get(f"{BASE_REQUEST_URL}/{code}",
            params=filters,
            timeout=30)
        resp.raise_for_status()
        d = resp.json()

        keys = np.array([int(k) for k in d["value"].keys()])
        inds = np.unravel_index(keys, d["size"])

        cols = {}
        for name, ind in zip(d["id"], inds):
            inv = {int(v): k for k, v in d["dimension"][name]["category"]["index"].items()}
            cols[name] = [inv[i] for i in ind]
        cols["value"] = [float(v) for v in d["value"].values()]
        df = pd.DataFrame(cols).sort_values(by=['time', 'geo'], ascending=[True, True])

        print("DataFrame acquired from the internet")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)
        print("DataFrame saved to cache")
        return df