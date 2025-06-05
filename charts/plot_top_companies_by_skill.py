# charts/plot_top_companies_by_skill.py

import sqlite3
import pandas as pd
import plotly.express as px
import os
import webbrowser

def plot_top_companies_by_skill(selected_skills, db_path="preview_jobs.db"):
    """
    selected_skills: a list of skill‐strings (e.g. ["python", "sql"]).
    This will show the top 10 companies hiring for ANY of those skills.
    """

    # 1) Validate that the database file exists
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    # If no skills were selected, do nothing
    if not selected_skills:
        print("No skill selected.")
        return

    # Normalize & lowercase everything
    normalized = [s.strip().lower() for s in selected_skills if s.strip()]
    if not normalized:
        print("No valid skill names after stripping.")
        return

    # Build an SQL clause like: (LOWER(s.name) LIKE '%python%' OR LOWER(s.name) LIKE '%sql%' ...)
    where_clauses = " OR ".join(["LOWER(s.name) LIKE '%' || ? || '%'" for _ in normalized])
    params = tuple(normalized)

    conn = sqlite3.connect(db_path)

    sql = f"""
        SELECT j.company
        FROM jobs AS j
        INNER JOIN skills AS s
          ON j.job_id = s.job_id
        WHERE ({where_clauses})
          AND j.company IS NOT NULL
    """
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    # If no matching rows, inform the user
    if df.empty:
        print(f"No postings found requiring any of {normalized}.")
        return

    # 2) Count top 10 companies
    vc = df["company"].value_counts().nlargest(10)
    top_companies = vc.reset_index()
    top_companies.columns = ["company", "count"]  # ensure unique column names

    # 3) Build a human‐readable title
    skill_display = ", ".join([s.capitalize() for s in normalized])
    title = f"Top Companies Hiring for “{skill_display}”"

    # 4) Plot horizontal bar chart
    fig = px.bar(
        top_companies,
        x="count",
        y="company",
        orientation="h",
        title=title,
        labels={"count": "Number of Postings", "company": "Company"}
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"}
    )

    # 5) Save and open
    slug = "_".join([s.replace(" ", "_") for s in normalized])
    out_file = f"top_companies_{slug}.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved bar chart to '{out_file}'")

    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")
