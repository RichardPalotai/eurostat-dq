from .ingest import fetch_nuts_geometry
from .anomaly import isolation_forest
from .config import PROJECT_ROOT

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def make_histogram(df: pd.DataFrame, code: str, *, save_png: bool = True) -> dict:
    """Value-distribution histogram for the given dataset (population or emissions).

    Returns a dict of the figure(s) produced for ``code``, or ``{}`` if none apply. Saves a
    PNG to ``reports/`` when ``save_png`` is True.
    """
    figs = {}

    if (code == "demo_r_d2jan"):

        fig, ax = plt.subplots(figsize=(8, 4))
        (df["value"] / 1e6).hist(bins=50, ax=ax)
        ax.set_title("Population per NUTS 2 region")
        ax.set_xlabel("Population (millions of persons)")
        ax.set_ylabel("Number of region-years")
        fig.tight_layout()

        if (save_png):
            _save(fig, "EU_DEMO_hist.png")
        figs["EU_DEMO_hist"] = fig

    if (code == "env_air_gge"):

        fig, ax = plt.subplots(figsize=(8, 4))
        (df["value"] / 1e3).hist(bins=50, ax=ax)
        ax.set_title("GHG emissions per country")
        ax.set_xlabel("Emissions (Mt CO₂-eq)")
        ax.set_ylabel("Number of country-years")
        fig.tight_layout()
        
        if (save_png):
            _save(fig, "EU_ENV_hist.png")
        figs["EU_ENV_hist"] = fig

    return figs

def make_boxplot(df: pd.DataFrame, code: str, *, save_png: bool = True) -> dict:
    """Distribution-by-year boxplots (EU-wide, plus Hungary for the population dataset).

    Returns a dict of the figures produced for ``code``, or ``{}`` if none apply.
    """
    figs = {}

    if (code == "demo_r_d2jan"):
        fig_HU, ax_HU = plt.subplots(figsize=(16, 6))
        demo_hu = df[df.geo.str.startswith("HU")]
        demo_plot_HU = demo_hu.assign(value=demo_hu["value"] / 1e6)
        demo_plot_HU.boxplot(column="value", by="time", ax=ax_HU)
        ax_HU.set_title("Hungarian population yearly (1990-2025)")
        ax_HU.set_ylabel("Population (millions of persons)")
        ax_HU.set_xlabel("Year")
        ax_HU.set_xticklabels(ax_HU.get_xticklabels(), rotation=90)
        fig_HU.suptitle("")
        fig_HU.tight_layout()

        fig_EU, ax_EU = plt.subplots(figsize=(16, 6))
        demo_plot_eu = df.assign(value=df["value"] / 1e6)
        demo_plot_eu.boxplot(column="value", by="time", ax=ax_EU)
        ax_EU.set_title("Demographics of the EU")
        ax_EU.set_ylabel("Population (millions of persons)")
        ax_EU.set_xlabel("Year")
        ax_EU.set_xticklabels(ax_EU.get_xticklabels(), rotation=90)
        fig_EU.suptitle("")
        fig_EU.tight_layout()

        if (save_png):
            _save(fig_HU, "HUN_DEMO_boxplot.png")
            _save(fig_EU, "EU_DEMO_boxplot.png")
        figs["HUN_DEMO_boxplot"] = fig_HU
        figs["EU_DEMO_boxplot"] = fig_EU

    if (code == "env_air_gge"):
        fig_EU, ax_EU = plt.subplots(figsize=(16, 6))
        env_plot_eu = df.assign(value=df["value"] / 1e3)
        env_plot_eu.boxplot(column="value", by="time", ax=ax_EU)
        ax_EU.set_title("GHG emissions of the EU")
        ax_EU.set_ylabel("Emissions (Mt CO₂-eq)")
        ax_EU.set_xlabel("Year")
        ax_EU.set_xticklabels(ax_EU.get_xticklabels(), rotation=90)
        fig_EU.suptitle("")
        fig_EU.tight_layout()

        if (save_png):
            _save(fig_EU, "EU_ENV_boxplot.png")
        figs["EU_ENV_boxplot"] = fig_EU

    return figs

def make_hun_line_diagram(df: pd.DataFrame, code: str, *, save_png: bool = True) -> dict:
    """Hungary time-series: population per NUTS 2 region, or national emissions.

    Returns a dict of the figure produced for ``code``, or ``{}`` if none apply.
    """
    figs = {}

    if (code == "demo_r_d2jan"):
        demo_hu = df[df.geo.str.startswith("HU")]

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
        figs["HUN_DEMO_line_diagram"] = fig

    if (code == "env_air_gge"):
        env = df[df.geo == "HU"].sort_values("time")

        fig, ax = plt.subplots(figsize=(11, 6))
        ax.plot(env["time"], env["value"], marker="o")
        ax.set_title("GHG emissions of Hungary")
        ax.set_xlabel("Year"); ax.set_ylabel("Emissions (kt CO₂-eq)")
        fig.tight_layout()

        if save_png:
            _save(fig, "HUN_ENV_line_diagram.png")
        figs["HUN_ENV_line_diagram"] = fig

    return figs

def make_choropleth_demo(df: pd.DataFrame, nuts_geo_df: gpd.GeoDataFrame, code: str, *, year: str, save_png: bool = True) -> dict:
    """Choropleth of population by NUTS 2 region for one year.

    Applies to ``demo_r_d2jan`` only; returns ``{}`` for any other dataset. Regions with no
    matching data are drawn grey.

    Important:
        ``nuts_geo_df`` must be the geometry for the **same** ``year`` (from
        :func:`~eurostat_dq.ingest.fetch_nuts_geometry`) — NUTS boundaries are re-classified
        over time, so a mismatched version leaves regions unmatched.

    Returns:
        ``{"demo_choropleth_{year}": Figure}`` for the population dataset, else ``{}``.
    """
    if (code != "demo_r_d2jan"):
        return {}

    year_df = df[df["time"] == int(year)]
    gdf = nuts_geo_df.merge(year_df, left_on="NUTS_ID", right_on="geo", how="left")

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

    ax.set_title(f"Population by NUTS 2 region, {year}")
    fig.text(0.5, 0.02, "Source: Eurostat (demo_r_d2jan); boundaries © EuroGeographics (GISCO).", ha="center", va="bottom")
    ax.set_xlim(2.4e6, 6.0e6)
    ax.set_ylim(1.3e6, 5.5e6)
    ax.set_axis_off()                   # drop the 1e6 axis ticks — noise on a map

    if (save_png):
        _save(fig, f"demo_choropleth_{year}.png")

    return {f"demo_choropleth_{year}" : fig}

def make_trend_lines_env(df: pd.DataFrame, code: str, *, save_png: bool = True) -> dict:
    """Emissions indexed to 1990 = 100%, with IsolationForest anomalies annotated.

    Applies to ``env_air_gge`` only; returns ``{}`` for any other dataset.
    """
    if (code != "env_air_gge"):
        return {}
    
    env_anomaly_iso = isolation_forest(df)

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

    return {"env_trend_lines" : fig}

def _save(fig, filename):
    path = PROJECT_ROOT / "reports" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")

def generate_visuals(df: pd.DataFrame, code: str, *, use_cache: bool, choropleth_year: str = "2024") -> dict:
    """Build and save every figure applicable to ``code``, returning them keyed by name.

    Runs all ``make_*`` functions and merges their results; each function produces figures
    only for the dataset it applies to (the others contribute nothing), so the same call
    works for any dataset. Figures are saved to ``reports/`` as a side effect.

    Args:
        df: The cleaned long frame for ``code``.
        code: The dataset code, used to select which figures apply.
        use_cache: Passed to :func:`~eurostat_dq.ingest.fetch_nuts_geometry` for the map.
        choropleth_year: Year to map, and the matching NUTS geometry version. Defaults to "2024".

    Returns:
        A dict of ``{figure_name: matplotlib Figure}`` for every figure produced.
    """
    geo_df = fetch_nuts_geometry(year=choropleth_year, use_cache=use_cache)
    return make_histogram(df, code) | make_boxplot(df, code) | make_hun_line_diagram(df, code) | make_choropleth_demo(df, geo_df, code, year=choropleth_year) | make_trend_lines_env(df, code)