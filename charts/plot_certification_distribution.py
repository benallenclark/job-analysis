# charts/plot_certification_distribution.py

import sqlite3
import pandas as pd
import plotly.express as px
import os
import webbrowser

def plot_certification_distribution(db_path="preview_jobs.db"):
    """
    1) Read the `certifications` table (columns: job_id, name, required).
    2) Count frequency of each `name` value.
    3) Plot the top 15 certifications (by count) as a horizontal bar chart.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # ‘name’ holds the certification string
        df = pd.read_sql_query(
            "SELECT name FROM certifications",
            conn
        )
    except Exception as e:
        print("ERROR reading from 'certifications' table:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No rows found in 'certifications' table.")
        return

    # Count frequency of each certification name
    cert_counts = df["name"].value_counts().reset_index()
    cert_counts.columns = ["certification", "count"]

    # Take top 15
    topN = cert_counts.nlargest(15, "count")

    # Plot horizontal bar chart
    fig = px.bar(
        topN,
        x="count",
        y="certification",
        orientation="h",
        title="Top 15 Certifications (by Frequency in DB)",
        labels={"count": "# of Postings", "certification": "Certification"},
        text="count"
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"}
    )

    out_file = "certification_distribution.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")

if __name__ == "__main__":
    plot_certification_distribution()
