import pandas as pd
from datetime import datetime
from .ingest import fetch_dataset
from .clean import to_tidy, apply_slice
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
"""


def _badge(passed: bool) -> str:
    cls, txt = ("pass", "PASS") if passed else ("fail", "FAIL")
    return f'<span class="badge {cls}">{txt}</span>'


def _dataset_section(code: str, cfg, *, use_cache: bool) -> str:
    clean = apply_slice(to_tidy(fetch_dataset(code, use_cache=use_cache)), cfg)
    qa = run_expectations(clean, cfg)

    overall = all(res["passed"] for checks in qa.values() for res in checks.values())

    rows = [
        {"dimension": dim, "check": name, "passed": res["passed"],
         "failed": res.get("failed"), "sample": res.get("sample_bad")}
        for dim, checks in qa.items() for name, res in checks.items()
    ]
    summary = pd.DataFrame(rows)
    summary["passed"] = summary["passed"].map(_badge)
    dim_html = summary.fillna("—").to_html(index=False, escape=False, classes="dq", border=0)

    adf = isolation_forest(zscore_flags(clean))
    flagged = (adf[adf["z_anomaly"] | adf["if_anomaly"]]
               .sort_values("if_score")[["geo", "time", "value", "z", "if_score"]])
    flagged_html = flagged.round(3).fillna("—").to_html(index=False, classes="dq", border=0)

    return f"""
    <section>
      <h2><span class="dataset">{code}</span> &nbsp; {_badge(overall)}</h2>
      <h3>Quality dimensions</h3>
      {dim_html}
      <h3>Flagged rows <span class="count">{len(flagged)}</span></h3>
      <div class="scroll">{flagged_html}</div>
    </section>"""


def write_report(*, use_cache: bool = True) -> None:
    sections = "".join(
        _dataset_section(code, cfg, use_cache=use_cache)
        for code, cfg in DATASETS.items()
    )

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Eurostat Data-Quality Report</title>
<style>{CSS}</style></head>
<body><main>
  <header>
    <h1>Eurostat Data-Quality Report</h1>
    <p class="meta">Generated {datetime.now():%Y-%m-%d %H:%M} · {len(DATASETS)} dataset(s) · Source: Eurostat</p>
  </header>
  <p class="legend">
    <b>—</b> in a dimension row: the check reports a value, not a per-row failure count (see <i>passed</i>).<br>
    <b>if_score —</b> in a flagged row: first year, no year-over-year change to score — flagged by z-score instead.
  </p>
  {sections}
</main></body></html>"""

    (PROJECT_ROOT / "reports" / "quality_report.html").write_text(html)
