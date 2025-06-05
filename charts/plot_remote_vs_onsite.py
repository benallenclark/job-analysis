# plot_remote_vs_onsite.py

import sqlite3
import pandas as pd
import plotly.express as px
import os
import webbrowser

def plot_remote_vs_onsite(db_path="preview_jobs.db"):
    """
    1) Connects to preview_jobs.db
    2) SELECT job_id, location FROM jobs
    3) Classifies each row as Remote / Hybrid / On-Site
    4) Builds a pie chart showing overall percentages
    5) Saves to 'remote_vs_onsite_pie.html' and opens it in the browser
    """

    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)

    try:
        df = pd.read_sql_query("SELECT job_id, location FROM jobs", conn)
    except Exception as e:
        print("ERROR reading from 'jobs' table:", e)
        conn.close()
        return

    conn.close()

    if df.empty:
        print("No rows found in the 'jobs' table.")
        return

    # Classify each row into Remote / Hybrid / On-Site
    def classify_remote(loc):
        loc_lower = loc.lower() if isinstance(loc, str) else ""
        if "remote" in loc_lower:
            return "Remote"
        elif "hybrid" in loc_lower:
            return "Hybrid"
        else:
            return "On-Site"

    df['work_type'] = df['location'].apply(classify_remote)

    # Build pie‐chart DataFrame
    pie_df = df['work_type'].value_counts().reset_index()
    pie_df.columns = ['work_type', 'count']

    # Create and save pie chart
    fig = px.pie(
        pie_df,
        names='work_type',
        values='count',
        title="Remote vs. Hybrid vs. On-Site (All Jobs)"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    out_file = "remote_vs_onsite_pie.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved pie chart to '{out_file}'")

    # Automatically open in default browser
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_remote_vs_onsite()
