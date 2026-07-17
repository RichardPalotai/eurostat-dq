import eurostat
import pandas as pd
import requests, json
from pathlib import Path
from .config import PROJECT_ROOT, BASE_REQUEST_URL

def fetch_dataset(code: str, *, use_cache: bool = True) -> pd.DataFrame:
    """Fetches dataset with eurostat.get_data_df and if use_cache=True it searches the data/raw folder first before fetching from the web"""
    cache_path = PROJECT_ROOT / "data" / "raw" / f"{code}.parquet"
    if (use_cache and cache_path.exists()):
        print("Code found in cache")
        return pd.read_parquet(cache_path)
    else:
        df = eurostat.get_data_df(code)
        print("DataFrame acquired from the internet")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)
        print("DataFrame saved to cache")
        return df
    
def fetch_dataset_json(code: str, *, use_cache: bool = True, **filters) -> pd.DataFrame:
    """Fetch dataset with custom filtering through EurostatAPI and requests. Returns a pandas DataFrame.

    Filters must be using the EurostatAPI's request structure, but in a dictionary e.g.: {"age":"TOTAL", ...., "geo":"HU11"}
    (format and lang are given)"""
    if filters:
        filters_label = f"_{'_'.join(k for k, v in filters.items())}"
    else:
        filters_label = ""
    
    cache_path = PROJECT_ROOT / "data" / "raw" / f"{code}{filters_label}.json"
    if (use_cache and cache_path.exists()):
        print("Code found in cache")
        return pd.DataFrame(decode_json(cache_path))
    else:
        resp = requests.get(f"{BASE_REQUEST_URL}/{code}",
            params= filters.update({"format":"JSON", "lang":"en"}),
            timeout=30)
        resp.raise_for_status()
        d = resp.json()
        print(json.dumps(d, indent=2))


        # print("DataFrame acquired from the internet")
        # cache_path.parent.mkdir(parents=True, exist_ok=True)
        # df.to_parquet(cache_path, index=False)
        # print("DataFrame saved to cache")
        # return df

def decode_json(cache_path: Path) -> list[dict]:
    """Convert the given Eurostat JSON-stat format to a list[dict] where each dictionary defines one cell and It's labels."""
    pass