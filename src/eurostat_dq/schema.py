from pydantic import BaseModel, field_validator, ValidationError, ValidationInfo
from pandas import DataFrame
from .config import DatasetConfig
from datetime import datetime
from collections import Counter

MIN_YEAR = 1990

class Record(BaseModel):
    """One validated Eurostat observation — the row-level half of the quality layer.

    Enforces per-row accuracy and consistency: ``value`` within the dataset's range,
    ``time`` a plausible year, and ``geo`` in the dataset's valid set. A ``None`` value is
    allowed (a known gap, not a failure). The dataset-specific bounds are injected at call
    time via validation context — pass the config as ``context``::

        Record.model_validate(row, context=cfg)

    so the same model validates any dataset. Use :func:`validate_rows` to run it over a frame.
    """

    geo: str
    time: int
    value: float | None

    @field_validator("value")
    @classmethod
    def value_in_range(cls, v: float, info: ValidationInfo) -> float | None:
        cfg = info.context
        if v is not None and (v < cfg.value_range[0] or v > cfg.value_range[1]):
            raise ValueError(f"value {v} is not in range {cfg.value_range[0]}-{cfg.value_range[1]}")
        return v

    @field_validator("time")
    @classmethod
    def year_in_bounds(cls, v: int, info: ValidationInfo) -> int:
        if v < MIN_YEAR or v > datetime.now().year:
            raise ValueError(f"year {v} is not in range {MIN_YEAR}-{datetime.now().year}")
        return v

    @field_validator("geo")
    @classmethod
    def geo_is_valid(cls, v: str, info: ValidationInfo) -> str:
        cfg = info.context
        if v not in cfg.valid_geo:
            raise ValueError(f"geo {v} is not valid")
        return v

def validate_rows(df: DataFrame, cfg: DatasetConfig) -> tuple[list, list, dict]:
    """Validate every row of a frame against :class:`Record`, collecting failures instead of raising.

    Each row is checked with the dataset's config injected as context. Rows that fail are
    recorded (with their structured errors) rather than aborting the run.

    Args:
        df: A cleaned long frame with ``geo``, ``time`` and ``value`` columns.
        cfg: The dataset's registry entry, passed to each ``Record`` as validation context.

    Returns:
        A ``(valid, errors, summary)`` tuple:

        * ``valid`` — list of validated ``Record`` objects.
        * ``errors`` — list of ``{"row": index, "errors": [...]}`` for each failing row.
        * ``summary`` — ``{"total", "passed", "failed", "by_field"}``, where ``by_field``
          counts failures per field (e.g. ``{"geo": 3, "value": 1}``).
    """
    valid, errors = [], []
    for i, row in enumerate(df.to_dict("records")):
        try:
            valid.append(Record.model_validate(row, context=cfg))
        except ValidationError as e:
            errors.append({"row": i, "errors": e.errors()})

    by_field = Counter(
        err["loc"][0]
        for e in errors
        for err in e["errors"]
    )
    summary = {
        "total": len(df),
        "passed": len(valid),
        "failed": len(errors),
        "by_field": dict(by_field)
    }

    return valid, errors, summary