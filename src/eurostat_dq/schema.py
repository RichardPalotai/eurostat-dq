from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ValidationInfo
from .config import DatasetConfig
from datetime import datetime

class Record(BaseModel):
    geo: str
    time: int
    value: float | None

    @field_validator("value")
    @classmethod
    def value_in_range(cls, v: float, info: ValidationInfo) -> float:
        cfg = info.context
        if v is not None and (v < cfg.value_range[0] or v > cfg.value_range[1]):
            raise ValueError(f"value {v} is not in range {info.value_range[0]}-{info.value_range[1]}")
        return v

    @field_validator("time")
    @classmethod
    def year_in_bounds(cls, v: int, info: ValidationInfo) -> int:
        if v < 1990 or v > datetime.now().year:
            raise ValueError(f"year {v} is in not in range {1990}-{datetime.now().year}")
        return v

    @field_validator("geo")
    @classmethod
    def geo_is_valid(cls, v: str, info: ValidationInfo) -> str:
        cfg = info.context
        if v not in cfg.valid_geo:
            raise ValueError(f"geo {v} is not valid")
        return v