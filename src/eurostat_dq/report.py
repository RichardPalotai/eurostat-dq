import base64
import pandas as pd
from datetime import datetime
from .schema import validate_rows
from .expectations import run_expectations
from .anomaly import zscore_flags, isolation_forest
from .config import DATASETS, PROJECT_ROOT

CSS = """
:root { --ink:#1f2933; --muted:#617080; --line:#e4e9f0; --bg:#f7f9fc;
        --pass:#1a7f47; --pass-bg:#e4f5ea; --fail:#b42318; --fail-bg:#fdecea; --accent:#2a4d69; }
* { box-sizing:border-box; }
body { font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
       color:var(--ink); background:var(--bg); margin:0; padding:2rem 1rem; line-height:1.5; }
main { max-width:1000px; margin:0 auto; background:#fff; padding:2rem 2.5rem;
       border:1px solid var(--line); border-radius:12px; }
header { border-bottom:2px solid var(--accent); padding-bottom:1rem; margin-bottom:1.5rem; }
h1 { margin:0 0 .25rem; font-size:1.7rem; color:var(--accent); }
h2 { font-size:1.25rem; margin:2rem 0 .5rem; border-bottom:1px solid var(--line); padding-bottom:.3rem; }
h3 { font-size:1rem; margin:1.2rem 0 .4rem; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
.meta { color:var(--muted); font-size:.9rem; margin:0; }
.legend { color:var(--muted); font-size:.85rem; background:var(--bg); border-left:3px solid var(--line);
          padding:.5rem .8rem; border-radius:4px; margin:1rem 0; }
table.dq { border-collapse:collapse; width:100%; font-size:.88rem; margin:.3rem 0 1rem; }
table.dq th { background:var(--accent); color:#fff; text-align:left; padding:.45rem .7rem; font-weight:600; }
table.dq td { padding:.4rem .7rem; border-bottom:1px solid var(--line); }
table.dq tr:nth-child(even) td { background:#fafcff; }
.badge { display:inline-block; padding:.1rem .55rem; border-radius:999px; font-size:.78rem; font-weight:700; }
.badge.pass { color:var(--pass); background:var(--pass-bg); }
.badge.fail { color:var(--fail); background:var(--fail-bg); }
.count { display:inline-block; background:var(--fail-bg); color:var(--fail); border-radius:999px;
         padding:.05rem .5rem; font-size:.8rem; font-weight:700; }
.scroll { max-height:340px; overflow:auto; border:1px solid var(--line); border-radius:6px; }
.dataset { font-size:1.35rem; color:var(--accent); }
figure { margin:1.8rem 0; }
figure img { max-width:100%; height:auto; border:1px solid var(--line); border-radius:8px;
             box-shadow:0 1px 4px rgba(0,0,0,.06); }
figcaption { font-weight:700; color:var(--accent); margin-top:.6rem; font-size:1rem; }
.commentary { margin:.4rem 0 0; }
"""

FIGURES = [
    {
        "file": "EU_DEMO_hist.png",
        "code": "demo_r_d2jan",
        "title": "Population distribution across NUTS 2 regions",
        "commentary": (
            "The distribution is strongly right-skewed — most regions cluster at 1-2 "
            "million, with a long thin tail of larger regions."
        ),
    },
    {
        "file": "EU_ENV_hist.png",
        "code": "env_air_gge",
        "title": "GHG emissions distribution across countries",
        "commentary": (
            "Emissions span a ~600× range (Malta to Germany), so the distribution is "
            "heavily right-skewed and lumpy — each cluster is roughly one country's series. "
        ),
    },
    {
        "file": "EU_DEMO_boxplot.png",
        "code": "demo_r_d2jan",
        "title": "Population distribution by year (EU)",
        "commentary": (
            "The box (typical region) stays stable while the upper tail rises — growth is "
            "concentrated in already-large regions."
        ),
    },
    {
        "file": "EU_ENV_boxplot.png",
        "code": "env_air_gge",
        "title": "GHG emissions distribution by year (EU)",
        "commentary": (
            "The whole distribution drifts downward over time — a broad EU-wide decline in "
            "emissions."
        ),
    },
    {
        "file": "demo_choropleth_2024.png",
        "code": "demo_r_d2jan",
        "title": "Population by NUTS 2 region (2024)",
        "commentary": (
            "Population is strongly concentrated: most NUTS 2 regions hold 1-2 million "
            "people, while a handful (Île-de-France, Istanbul, Madrid, Lombardy) exceed "
            "5 million. Grey regions had no matching data for 2024. "
        ),
    },
    {
        "file": "env_trend_lines.png",
        "code": "env_air_gge",
        "title": "GHG emissions relative to 1990",
        "commentary": (
            "Indexed to 1990 = 100%, most countries have cut emissions substantially "
            "(Estonia -75%, Latvia -63%), while a few rose (Turkey +155%). Red markers "
            "flag year-over-year anomalies from the IsolationForest detector. "
        ),
    },
    {
        "file": "HUN_DEMO_boxplot.png",
        "code": "demo_r_d2jan",
        "title": "Hungarian population distribution by year",
        "commentary": (
            "Across Hungary's 8 NUTS 2 regions, the spread widens over time as Budapest "
            "detaches from the rest."
        ),
    },
    {
        "file": "HUN_DEMO_line_diagram.png",
        "code": "demo_r_d2jan",
        "title": "Hungarian regions: population over time",
        "commentary": (
            "Only Pest (HU12) grows (+25%); Budapest is roughly flat and the other regions "
            "decline — a suburbanisation pattern. Line breaks mark the 2001 NUTS split. "
        ),
    },
    {
        "file": "HUN_ENV_line_diagram.png",
        "code": "env_air_gge",
        "title": "Hungary: GHG emissions over time",
        "commentary": (
            "Hungary's emissions fell ~43% from 1990, with visible steps around 2009 and "
            "2020."
        ),
    },
]


def _img_data_uri(filename: str) -> str | None:
    """Read a PNG from reports/ and inline it as a base64 data URI (self-contained)."""
    path = PROJECT_ROOT / "reports" / filename
    if not path.exists():
        return None
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{b64}"


def _figures_section(codes: list[str]) -> str:
    blocks = []
    for f in FIGURES:
        if f["code"] in codes:
            uri = _img_data_uri(f["file"])
            img = (f'<img src="{uri}" alt="{f["title"]}">' if uri
                else f'<p class="commentary"><i>{f["file"]} not generated yet — run the viz step.</i></p>')
            blocks.append(f"""
        <figure>
            {img}
            <figcaption>{f['title']}</figcaption>
            <p class="commentary">{f['commentary']}</p>
        </figure>""")
    return f"""
    <section>
      <h2>Visualizations</h2>{"".join(blocks)}
    </section>"""


def _badge(passed: bool) -> str:
    cls, txt = ("pass", "PASS") if passed else ("fail", "FAIL")
    return f'<span class="badge {cls}">{txt}</span>'


def _dataset_section(df: pd.DataFrame, code: str) -> str:
    cfg = DATASETS[code]

    qa = run_expectations(df, cfg)

    overall = all(res["passed"] for checks in qa.values() for res in checks.values())

    rows = [
        {"dimension": dim, "check": name, "passed": res["passed"],
         "failed": res.get("failed"), "sample": res.get("sample_bad")}
        for dim, checks in qa.items() for name, res in checks.items()
    ]
    summary = pd.DataFrame(rows)
    summary["passed"] = summary["passed"].map(_badge)
    dim_html = summary.fillna("—").to_html(index=False, escape=False, classes="dq", border=0)

    adf = isolation_forest(zscore_flags(df))
    flagged = (adf[adf["z_anomaly"] | adf["if_anomaly"]]
               .sort_values("if_score")[["geo", "time", "value", "z", "if_score"]])
    flagged_html = flagged.round(3).fillna("—").to_html(index=False, classes="dq", border=0)

    val = validate_rows(df, cfg)
    summary_html = pd.DataFrame([val[2]]).to_html(index=False, classes="dq", border=0)
    err_clean = [{"row": err["row"], "errors": [d["msg"] for d in err["errors"]]} for err in val[1]]
    err_html = pd.DataFrame(err_clean).to_html(index=False, classes="dq", border=0)

    return f"""
    <section>
      <h2><span class="dataset">{code}</span> &nbsp; {_badge(overall)}</h2>
      <h3>Quality dimensions</h3>
      {dim_html}
      <h3>Flagged rows <span class="count">{len(flagged)}</span></h3>
      <div class="scroll">{flagged_html}</div>
      <h3>Failed rows <span class="count">{val[2]["failed"]}</span></h3>
      <b>Summary</b>
      {summary_html}
      {"<b>Fails by row</b>\n" + err_html if val[2]["failed"] > 0 else ""}
    </section>"""


def write_report(dfs: dict[str, pd.DataFrame]) -> None:
    sections = "".join(
        _dataset_section(df, code)
        for code, df in dfs.items()
    )

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Eurostat Data-Quality Report</title>
<style>{CSS}</style></head>
<body><main>
  <header>
    <h1>Eurostat Data-Quality Report</h1>
    <p class="meta">Generated {datetime.now():%Y-%m-%d %H:%M} · {len(list(dfs.keys()))} dataset(s) · Source: Eurostat</p>
  </header>
  <p class="legend">
    <b>—</b> in a dimension row: the check reports a value, not a per-row failure count (see <i>passed</i>).<br>
    <b>if_score —</b> in a flagged row: first year, no year-over-year change to score — flagged by z-score instead.
  </p>
  {sections}
  {_figures_section(list(dfs.keys()))}
</main></body></html>"""

    (PROJECT_ROOT / "reports" / "quality_report.html").write_text(html)
