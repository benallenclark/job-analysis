# charts/plot_skill_gap_similarity_matrix.py

import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import os
import webbrowser
from collections import Counter

def plot_skill_gap_similarity_matrix(user_skills, db_path="preview_jobs.db"):
    """
    1) user_skills: list of skills the user already has (e.g. ["python","sql"])
    2) Connect to preview_jobs.db
    3) SELECT job_id, name AS skill FROM skills
    4) Build each job’s full skill set, subtract user_skills → missing‐skill sets
    5) Identify top 20 most frequent missing skills
    6) Build a co‐occurrence matrix among those top 20 missing skills
    7) Plot a heatmap and open it in the browser
    """
    # 1) Normalize user_skills
    user_set = set(s.strip().lower() for s in user_skills)

    # 2) Validate database file
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # 3) Read every (job_id, skill) pair from the 'skills' table
        df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
    except Exception as e:
        print("ERROR reading from 'skills' table:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No data found in 'skills' table.")
        return

    # 4) Build per‐job skill sets
    df['skill'] = df['skill'].str.strip().str.lower()
    posting_skills = df.groupby("job_id")["skill"].apply(set).to_dict()

    # 5) Build a list of missing‐skill sets per job
    missing_list = []
    for job_id, req_set in posting_skills.items():
        missing = req_set - user_set
        if missing:
            missing_list.append(missing)

    if not missing_list:
        print("No missing skills found (maybe you already have every skill?).")
        return

    # 6) Count frequencies of each missing skill
    counter = Counter()
    for missing in missing_list:
        counter.update(missing)
    top_missing = [skill for skill, _ in counter.most_common(20)]

    if not top_missing:
        print("No missing skills appear more than once.")
        return

    # 7) Build co‐occurrence matrix among top_missing
    n = len(top_missing)
    mat = np.zeros((n, n), dtype=int)
    for missing in missing_list:
        relevant = [s for s in missing if s in top_missing]
        for i, s1 in enumerate(top_missing):
            for j, s2 in enumerate(top_missing):
                if s1 in relevant and s2 in relevant:
                    mat[i, j] += 1

    # 8) Plot heatmap
    fig = px.imshow(
        mat,
        x=top_missing,
        y=top_missing,
        color_continuous_scale="Blues",
        labels={'x': 'Missing Skill', 'y': 'Missing Skill', 'color': '#Postings'},
        title="Missing‐Skill Co‐Occurrence (Given Your Current Skills)"
    )
    fig.update_layout(template="plotly_dark")
    out_file = "skill_gap_similarity_matrix.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved heatmap to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    # Example standalone call; replace with actual user skills
    plot_skill_gap_similarity_matrix(["python", "sql"])
