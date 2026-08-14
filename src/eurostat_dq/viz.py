from .ingest import fetch_dataset, fetch_nuts_geometry
from .clean import to_tidy, apply_slice
from .anomaly import isolation_forest
from .config import DATASETS, PROJECT_ROOT

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def make_histogram(*, ENV: bool = True, DEMO: bool = True, save_png: bool = True, use_cache: bool = True) -> dict: #filterable for GHG or/and Population
    if (not ENV and not DEMO):
        return None

    figs = {}

    if (DEMO):
        raw   = fetch_dataset("demo_r_d2jan", use_cache=use_cache)
        tidy  = to_tidy(raw)
        demo = apply_slice(tidy, DATASETS["demo_r_d2jan"])

        fig, ax = plt.subplots(figsize=(8, 4))
        (demo["value"] / 1e6).hist(bins=50, ax=ax)
        ax.set_title("Population per NUTS 2 region")
        ax.set_xlabel("Population (millions of persons)")
        ax.set_ylabel("Number of region-years")
        fig.tight_layout()

        if (save_png):
            _save(fig, "EU_DEMO_hist.png")
        figs["DEMO"] = fig

    if (ENV):
        raw   = fetch_dataset("env_air_gge", use_cache=use_cache)
        tidy  = to_tidy(raw)
        env = apply_slice(tidy, DATASETS["env_air_gge"])

        fig, ax = plt.subplots(figsize=(8, 4))
        (env["value"] / 1e3).hist(bins=50, ax=ax)
        ax.set_title("GHG emissions per country")
        ax.set_xlabel("Emissions (Mt CO₂-eq)")
        ax.set_ylabel("Number of country-years")
        fig.tight_layout()
        
        if (save_png):
            _save(fig, "EU_ENV_hist.png")
        figs["ENV"] = fig

    return figs


def make_boxplot(HU: bool, *, EU_ENV: bool = True, EU_DEMO: bool = True, save_png: bool = True, use_cache: bool = True) -> dict: # filterable for the whole EU or only HU
    figs = {}

    if (HU):
        raw   = fetch_dataset("demo_r_d2jan", use_cache=use_cache)
        tidy  = to_tidy(raw)
        clean = apply_slice(tidy, DATASETS["demo_r_d2jan"])

        fig, ax = plt.subplots(figsize=(16, 6))
        demo_hu = clean[clean.geo.str.startswith("HU")]
        demo_plot = demo_hu.assign(value=demo_hu["value"] / 1e6)
        demo_plot.boxplot(column="value", by="time", ax=ax)
        ax.set_title("Hungarian population yearly (1990-2025)")
        ax.set_ylabel("Population (millions of persons)")
        ax.set_xlabel("Year")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
        fig.suptitle("")
        fig.tight_layout()

        if (save_png):
            _save(fig, "HUN_DEMO_boxplot.png")
        figs["HU_DEMO"] = fig
    else:
        if (not EU_ENV and not EU_DEMO):
            return None

        if (EU_DEMO):
            raw   = fetch_dataset("demo_r_d2jan", use_cache=use_cache)
            tidy  = to_tidy(raw)
            demo = apply_slice(tidy, DATASETS["demo_r_d2jan"])

            fig, ax = plt.subplots(figsize=(16, 6))
            demo_plot_eu = demo.assign(value=demo["value"] / 1e6)
            demo_plot_eu.boxplot(column="value", by="time", ax=ax)
            ax.set_title("Demographics of the EU")
            ax.set_ylabel("Population (millions of persons)")
            ax.set_xlabel("Year")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            fig.suptitle("")
            fig.tight_layout()

            if (save_png):
                _save(fig, "EU_DEMO_boxplot.png")
            figs["EU_DEMO"] = fig

        if (EU_ENV):
            raw   = fetch_dataset("env_air_gge", use_cache=use_cache)
            tidy  = to_tidy(raw)
            env = apply_slice(tidy, DATASETS["env_air_gge"])

            fig, ax = plt.subplots(figsize=(16, 6))
            env_plot_eu = env.assign(value=env["value"] / 1e3)
            env_plot_eu.boxplot(column="value", by="time", ax=ax)
            ax.set_title("GHG emissions of the EU")
            ax.set_ylabel("Emissions (Mt CO₂-eq)")
            ax.set_xlabel("Year")
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
            fig.suptitle("")
            fig.tight_layout()

            if (save_png):
                _save(fig, "EU_ENV_boxplot.png")
            figs["EU_ENV"] = fig

    return figs

def make_hun_line_diagram(*, ENV: bool = True, DEMO: bool = True, use_cache: bool = True, save_png: bool = True) -> dict:
    figs = {}

    if DEMO:
        raw = fetch_dataset("demo_r_d2jan", use_cache=use_cache)
        demo_hu = apply_slice(to_tidy(raw), DATASETS["demo_r_d2jan"])
        demo_hu = demo_hu[demo_hu.geo.str.startswith("HU")]

        fig, ax = plt.subplots(figsize=(11, 6))
        wide = demo_hu.pivot(index="time", columns="geo", values="value") / 1e6
        wide.plot(ax=ax, marker="o", markersize=3)
        ax.set_title("Hungarian NUTS 2 regions: population 1990-2025")
        ax.set_xlabel("Year"); ax.set_ylabel("Population (millions of persons)")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
        ax.grid(which="minor", alpha=0.3)
        ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc="upper left")
        fig.tight_layout()

        if save_png:
            _save(fig, "HUN_DEMO_line_diagram.png")
        figs["DEMO"] = fig

    if ENV:
        raw = fetch_dataset("env_air_gge", use_cache=use_cache)
        env = apply_slice(to_tidy(raw), DATASETS["env_air_gge"])
        env = env[env.geo == "HU"].sort_values("time")

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(env["time"], env["value"], marker="o")
        ax.set_title("GHG emissions of Hungary")
        ax.set_xlabel("Year"); ax.set_ylabel("Emissions (kt CO₂-eq)")
        fig.tight_layout()

        if save_png:
            _save(fig, "HUN_ENV_line_diagram.png")
        figs["ENV"] = fig

    return figs

def make_choropleth_demo(*, year: str = "2024", save_png: bool = True, use_cache: bool = True):
    nuts = fetch_nuts_geometry(year=year, use_cache=use_cache)

    print("FETCH:")
    raw   = fetch_dataset("demo_r_d2jan", use_cache=use_cache)
    clean = apply_slice(to_tidy(raw), DATASETS["demo_r_d2jan"])

    year_df = clean[clean["time"] == int(year)]
    gdf = nuts.merge(year_df, left_on="NUTS_ID", right_on="geo", how="left")

    gdf["pop_m"] = gdf["value"] / 1e6

    fig, ax = plt.subplots(figsize=(12, 6))

    gdf.plot(
        column="pop_m",
        scheme="user_defined", classification_kwds={"bins": [1, 2, 3, 5, 10, 16]},
        legend=True, legend_kwds={
        "title": "Population (millions)",
        "fmt": "{:.1f}",
        "loc": "upper left",
        "bbox_to_anchor": (1.02, 1),   # outside, to the right
        "interval": True,               # "[0.5, 1.2)" style
        },
        cmap="viridis",
        missing_kwds={"color": "lightgrey", "label": "no data"},
        ax = ax
    )

    ax.set_title("Population by NUTS 2 region, 2024")
    fig.text(0.5, 0.02, "Source: Eurostat (demo_r_d2jan); boundaries © EuroGeographics (GISCO).", ha="center", va="bottom")
    ax.set_xlim(2.4e6, 6.0e6)
    ax.set_ylim(1.3e6, 5.5e6)
    ax.set_axis_off()                   # drop the 1e6 axis ticks — noise on a map

    if (save_png):
        _save(fig, f"demo_choropleth_{year}.png")

    return fig

def make_trend_lines_env(*, save_png: bool = True, use_cache: bool = True):
    print("FETCH:")
    raw   = fetch_dataset("env_air_gge", use_cache=use_cache)
    clean = apply_slice(to_tidy(raw), DATASETS["env_air_gge"])
    env_anomaly_iso = isolation_forest(clean)

    w = env_anomaly_iso.pivot(index="time", columns="geo", values="value")
    idx = w / w.iloc[0] * 100 # Normalize data so the first row becomes 100% and all the other rows show relative percentage changes.

    fig, ax = plt.subplots(figsize=(12, 6))

    for c in idx.columns:
        ax.plot(idx.index, idx[c], color="lightgrey", lw=0.8, zorder=1)
    for c in ["EE", "BG", "DK", "FI", "HR", "IS", "LT", "LU", "LV", "MT", "RO"]:               # cutters, risers, biggest, home
        ax.plot(idx.index, idx[c], lw=2.5, label=c, zorder=2)
    ax.axhline(100, color="black", ls="--", lw=0.8)  # the 1990 baseline

    flagged = env_anomaly_iso[env_anomaly_iso["if_anomaly"]]
    ano = flagged.pivot(index="time", columns="geo", values="if_anomaly")
    result = idx[ano]
    first = True
    for c in ["EE", "BG", "DK", "FI", "HR", "IS", "LT", "LU", "LV", "MT", "RO"]:
        ax.scatter(result.index, result[c], color="red", marker="o", zorder=3, label="anomaly" if first else None)
        first = False

    ax.set_title("Relative change of GHG emissions to 1990 over the years", fontweight='bold')
    ax.set_xlabel("Year", fontweight='bold')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: f"{int(x)}%"))
    fig.text(1, 0.01, "Source: Eurostat (env_air_gge).", ha="center", va="bottom")
    ax.legend(loc="upper left", bbox_to_anchor=(1,1))

    if (save_png):
        _save(fig, "env_trend_lines.png")

    return fig

def _save(fig, filename):
    path = PROJECT_ROOT / "reports" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")