# charts/plot_skill_salary_correlation.py

import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.stats import pearsonr
import os
import webbrowser

def plot_skill_salary_correlation(db_path="preview_jobs.db"):
    """
    1) Connect to preview_jobs.db
    2) SELECT job_id, salary_avg, skill_name FROM jobs ↔ skills
    3) Build a one‐hot matrix of skills per job, join salary_avg
    4) Compute Pearson correlation (skill presence vs. salary)
    5) Plot top 20 positive correlations
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # 2) Grab job_id, numeric salary (salary_avg), and skill name
        sql = """
            SELECT
                j.job_id,
                j.salary_avg AS salary_val,
                s.name       AS skill
            FROM jobs AS j
            INNER JOIN skills AS s
                ON j.job_id = s.job_id
            WHERE j.salary_avg IS NOT NULL
                AND j.salary_avg <= 200000
                AND j.salary_avg >= 25000
        """
        df = pd.read_sql_query(sql, conn)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No salary/skill data found.")
        return

    # 3) Build one‐hot matrix of skills per job
    #    First, ensure lowercase/stripped skills
    df['skill'] = df['skill'].str.strip().str.lower()

    #    Use crosstab to get 1 if skill present in job, 0 otherwise
    one_hot = pd.crosstab(df['job_id'], df['skill']).astype(int)

    #    Now bring in salary_val per job_id
    salary_map = df[['job_id', 'salary_val']].drop_duplicates().set_index('job_id')['salary_val']
    data = one_hot.join(salary_map, how='inner')

    # 4) Compute Pearson r for each skill
    corrs = []
    for skill in data.columns[:-1]:  # all columns except 'salary_val'
        x = data[skill].values
        y = data['salary_val'].values
        # skip skills that appear in fewer than 5 jobs
        if x.sum() < 5:
            continue
        r, p = pearsonr(x, y)
        corrs.append((skill, r, p))

    corr_df = pd.DataFrame(corrs, columns=['skill', 'pearson_r', 'pval'])
    if corr_df.empty:
        print("No skill appears in ≥ 5 postings.")
        return

    #    Keep top 20 by descending pearson_r
    corr_df = corr_df.sort_values('pearson_r', ascending=False).head(20)

    # 5) Plot bar chart
    fig = px.bar(
        corr_df,
        x='pearson_r',
        y='skill',
        orientation='h',
        title="Top 20 Skills Most Correlated with Higher Salary",
        labels={'pearson_r': 'Pearson r', 'skill': 'Skill'},
        hover_data={'pval': True}
    )
    fig.update_layout(
        template='plotly_dark',
        yaxis={'categoryorder': 'total ascending'}
    )

    out_file = "skill_salary_correlation.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_skill_salary_correlation()
