import pandas as pd
from .ingest import fetch_dataset
from .clean import to_tidy, apply_slice
from .expectations import run_expectations
from .anomaly import zscore_flags, isolation_forest
from .config import DATASETS, PROJECT_ROOT

def write_report(*, use_cache: bool = True):
    code, cfg = "demo_r_d2jan", DATASETS["demo_r_d2jan"]
    raw = fetch_dataset(code, use_cache=use_cache)
    clean = apply_slice(to_tidy(raw), cfg)
    qa_dict = run_expectations(clean, cfg)

    rows = []
    for dim, checks in qa_dict.items():
        for name, res in checks.items():
            rows.append({"dimension": dim, "check": name,
                        "passed": res["passed"], "failed": res.get("failed"),
                        "sample": res.get("sample_bad")})
    summary = pd.DataFrame(rows)
    html_table = summary.fillna("-").to_html(index=False)

    anomaly_df = isolation_forest(zscore_flags(clean))

    flagged = anomaly_df[anomaly_df["z_anomaly"] | anomaly_df["if_anomaly"]]
    flagged_html = flagged[["geo", "time", "value", "z", "if_score"]].fillna("-").to_html(index=False)

    html = f"""<html><body>
    <h1>Data Quality Report — {cfg.code}</h1>
    <h2>Dimensions</h2>{html_table}
    <h2>Flagged rows</h2>{flagged_html}
    </body></html>"""
    (PROJECT_ROOT / "reports" / "quality_report.html").write_text(html)