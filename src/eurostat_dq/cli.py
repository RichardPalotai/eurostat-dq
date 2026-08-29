import argparse

from .config import DATASETS
from .ingest import fetch_dataset
from .clean import to_tidy, apply_slice
from .viz import generate_visuals
from .report import write_report


def run_pipeline(dataset: str, *, use_cache: bool) -> None:
    """Run ingest → clean → figures → report for one dataset or all of them."""
    codes = list(DATASETS) if dataset == "all" else [dataset]

    cleaned = {}
    for code in codes:
        clean = apply_slice(to_tidy(fetch_dataset(code, use_cache=use_cache)), DATASETS[code])
        generate_visuals(clean, code, use_cache=use_cache)
        cleaned[code] = clean

    write_report(cleaned)
    print(f"Done → reports/quality_report.html ({len(codes)} dataset(s))")


def main() -> None:
    """Command-line entry point: parse ``--dataset``/``--no-cache`` and run the pipeline.

    Installed as the ``eurostat-dq`` console script (see ``[project.scripts]``); also runnable
    as ``python -m eurostat_dq.cli``. Errors from the pipeline are reported as a clean message
    with a non-zero exit code rather than a traceback.
    """
    parser = argparse.ArgumentParser(
        prog="eurostat-dq",
        description="Eurostat data-quality pipeline: ingest, validate, flag anomalies, report.",
    )
    parser.add_argument(
        "--dataset",
        choices=[*DATASETS, "all"],
        default="all",
        help="dataset to process (default: all)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="force a fresh fetch from the API instead of using the local cache",
    )
    args = parser.parse_args()

    try:
        run_pipeline(args.dataset, use_cache=not args.no_cache)
    except Exception as e:
        # library layer raises; the CLI is where errors become a clean message
        parser.exit(1, f"error: {e}\n")


if __name__ == "__main__":
    main()
