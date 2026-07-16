import eurostat
import pandas as pd
from .config import PROJECT_ROOT

def fetch_dataset(code: str, *, use_cache: bool = True) -> pd.DataFrame:
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