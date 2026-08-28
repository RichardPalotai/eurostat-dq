import sys
from .config import DATASETS
from .ingest import fetch_dataset
from .clean import to_tidy, apply_slice
from .viz import generate_visuals
from .report import write_report

def run_pipeline(dataset: str = "", *, use_cache: bool) -> None:
    if dataset == "all":
        clean_DEMO = apply_slice(to_tidy(fetch_dataset("demo_r_d2jan", use_cache=use_cache)), DATASETS["demo_r_d2jan"])
        clean_ENV = apply_slice(to_tidy(fetch_dataset("env_air_gge", use_cache=use_cache)), DATASETS["env_air_gge"])
        generate_visuals(clean_DEMO, "demo_r_d2jan", use_cache=use_cache)
        generate_visuals(clean_ENV, "env_air_gge", use_cache=use_cache)
        write_report({"demo_r_d2jan" : clean_DEMO, "env_air_gge" : clean_ENV})
    else:
        clean = apply_slice(to_tidy(fetch_dataset(dataset, use_cache=use_cache)), DATASETS[dataset])
        generate_visuals(clean, dataset, use_cache=use_cache)
        write_report({dataset : clean})

if len(sys.argv) == 3:
    command, dataset = sys.argv[1:3]
    cache = ""
elif len(sys.argv) == 4:
    command, dataset, cache = sys.argv[1:4]

if command == "--dataset":
    if dataset.lower() in ["demo_r_d2jan", "env_air_gge", "all"]:
        if cache == "use_cache":
            run_pipeline(dataset.lower(), use_cache=True)
        elif cache == "":
            run_pipeline(dataset.lower(), use_cache=False)
        else:
            print("Wrong cache choice!")
    else:
        print("No such dataset!")
else:
    print("No such command!")