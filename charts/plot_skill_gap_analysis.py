# plot_skill_gap_analysis.py

import sqlite3
import pandas as pd
import plotly.express as px
import sys

def plot_skill_gap_analysis(user_skills, db_path="preview_jobs.db"):
    # Normalize the user's skills into a lowercase set
    user_set = set(s.strip().lower() for s in user_skills)

    conn = sqlite3.connect(db_path)

    # ─── STEP 1 ───
    # Pull every (job_id, skill_name) pair from the 'skills' table.
    # If you also want to filter by salary_avg <= 200k, you can join jobs here.
    sql = """
        SELECT 
            s.job_id,
            s.name AS skill
        FROM skills AS s
        INNER JOIN jobs AS j
            ON s.job_id = j.job_id
        WHERE j.salary_avg IS NOT NULL
          AND j.salary_avg <= 200000
    """
    df = pd.read_sql_query(sql, conn)
    conn.close()

    # ─── STEP 2 ───
    # df now has columns ['job_id', 'skill'], one row per skill usage.
    df['skill'] = df['skill'].str.strip().str.lower()

    # Build each posting's skill set as a Python set
    posting_sets = df.groupby('job_id')['skill'].apply(set).to_dict()

    # ─── STEP 3 ───
    # For each job, compute which skills you’re missing (req_set − user_set).
    # Only count jobs where you’re missing at most 3 skills (tune threshold as desired).
    missing_counts = {}
    for job_id, req_set in posting_sets.items():
        missing = req_set - user_set
        if 0 < len(missing) <= 3:  # tune this “≤ 3” threshold if you like
            for skill in missing:
                missing_counts[skill] = missing_counts.get(skill, 0) + 1

    # ─── STEP 4 ───
    # Convert to a DataFrame and keep only the top 10 “most‐frequently missing” skills.
    gap_df = (
        pd.DataFrame.from_dict(missing_counts, orient='index', columns=['frequency'])
          .nlargest(10, 'frequency')
          .reset_index()
          .rename(columns={'index': 'skill'})
    )

    # ─── STEP 5 ───
    # Plot a horizontal bar chart of “top 10 missing skills you’d need to add.”
    fig = px.bar(
        gap_df,
        x='frequency',
        y='skill',
        orientation='h',
        title="Top 10 Skills You’re Missing\n(to qualify for jobs needing ≤ 3 more skills)",
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={'categoryorder': 'total ascending'},
        xaxis_title="Number of Postings Missing This Skill",
        yaxis_title="Skill"
    )
    fig.write_html("skill_gap_analysis.html", auto_open=True)


if __name__ == "__main__":
    # Usage: python plot_skill_gap_analysis.py "python,sql,power bi"
    user_skills = sys.argv[1].split(',') if len(sys.argv) > 1 else ["python", "sql"]
    plot_skill_gap_analysis(user_skills)
