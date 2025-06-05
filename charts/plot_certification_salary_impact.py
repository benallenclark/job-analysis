# charts/plot_certification_salary_impact.py

import sqlite3
import pandas as pd
import plotly.express as px
import os
import webbrowser
from scipy.stats import ttest_ind

def plot_certification_salary_impact(db_path="preview_jobs.db"):
    """
    1) Read job_id → salary_avg from jobs, and job_id → certification name from certifications.
    2) For each certification, compute average salary, std, and count of postings requiring that cert.
    3) For jobs with no certification, collect their salaries as the “no‐cert” group.
    4) Perform a t‐test comparing each cert’s salary distribution to the no‐cert distribution.
    5) Filter to certifications appearing in ≥20 postings, sort by avg_salary, and plot a horizontal bar chart
       with error bars (std). Hover shows count and p‐value.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # (1a) Load job_id, salary_avg from jobs
        jobs_df = pd.read_sql_query(
            "SELECT job_id, salary_avg FROM jobs WHERE salary_avg IS NOT NULL",
            conn
        )
        # (1b) Load job_id, name from certifications
        certs_df = pd.read_sql_query(
            "SELECT job_id, name AS certification FROM certifications",
            conn
        )
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if jobs_df.empty:
        print("No salary data found in 'jobs' table.")
        return

    # Merge salary with certifications
    merged = jobs_df.merge(certs_df, on="job_id", how="left")
    # Now 'certification' is NaN for jobs with no certification.

    # (2) Compute stats for each certification
    #   Group only rows where certification is not null
    with_cert = merged.dropna(subset=["certification"])
    if with_cert.empty:
        print("No postings with certifications in database.")
        return

    cert_stats = (
        with_cert
        .groupby("certification")["salary_avg"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={
            "mean": "avg_salary",
            "std": "std_salary",
            "count": "count_postings"
        })
    )

    # (3) Salaries for jobs with no certification
    no_cert_salaries = merged[merged["certification"].isna()]["salary_avg"]
    if no_cert_salaries.empty:
        print("No postings without any certification.")
        return

    # (4) For each cert, do a t-test against no-cert group
    pvals = []
    for cert in cert_stats["certification"]:
        cert_vals = merged[merged["certification"] == cert]["salary_avg"]
        # Perform Welch’s t-test
        tstat, p = ttest_ind(cert_vals, no_cert_salaries, equal_var=False, nan_policy="omit")
        pvals.append(p)
    cert_stats["p_value"] = pvals

    # (5) Filter to certifications with ≥20 postings, sort by avg_salary desc
    cert_stats = cert_stats[cert_stats["count_postings"] >= 20]
    if cert_stats.empty:
        print("No certifications have ≥20 postings.")
        return
    cert_stats = cert_stats.sort_values("avg_salary", ascending=False)

    # Plot horizontal bar chart
    fig = px.bar(
        cert_stats,
        x="avg_salary",
        y="certification",
        orientation="h",
        error_x="std_salary",
        hover_data=["count_postings", "p_value"],
        title="Average Salary by Certification (≥20 Postings)",
        labels={"avg_salary": "Avg Salary (USD)", "certification": "Certification"}
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"}
    )

    out_file = "certification_salary_impact.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_certification_salary_impact()
