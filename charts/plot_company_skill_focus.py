# charts/plot_company_skill_focus.py

import sqlite3
import pandas as pd
import plotly.express as px
import os
import webbrowser

def plot_company_skill_focus(user_skills, db_path="preview_jobs.db", top_n_companies=5, top_n_skills=10):
    """
    1) user_skills: list of skills the user already has (lower/upper case doesn’t matter).
    2) Connect to preview_jobs.db.
    3) SELECT job_id, company from jobs; SELECT job_id, name AS skill from skills.
    4) Exclude any skill in user_skills from consideration.
    5) Identify top_n_companies by number of postings.
    6) For each of those companies, count frequencies of missing skills, then keep top_n_skills.
    7) Render a grouped bar chart and open it in the browser.
    """
    # Normalize user_skills to lowercase
    user_set = set(s.strip().lower() for s in user_skills)

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # 3) Read job_id→company and job_id→skill
        job_comp = pd.read_sql_query("SELECT job_id, company FROM jobs WHERE company IS NOT NULL", conn)
        skill_df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if job_comp.empty or skill_df.empty:
        print("No data found in jobs/skills tables.")
        return

    # 4) Filter out any skill that the user already has
    skill_df['skill'] = skill_df['skill'].str.strip().str.lower()
    mask = ~skill_df['skill'].isin(user_set)
    skill_df = skill_df[mask].copy()

    # 5) Identify top N companies by number of postings
    top_companies = job_comp['company'].value_counts().nlargest(top_n_companies).index.tolist()

    # 6) Filter skill_df to only include postings from those top companies
    #    First, merge job_comp into skill_df to get company for each row
    merged = skill_df.merge(job_comp, on="job_id", how="inner")
    merged = merged[merged['company'].isin(top_companies)].copy()

    # Count skill frequencies within each of those companies
    grp = merged.groupby(['company', 'skill']).size().reset_index(name='count')

    # For each company, keep only the top_n_skills
    frames = []
    for comp in top_companies:
        sub = grp[grp['company'] == comp].nlargest(top_n_skills, 'count')
        frames.append(sub)
    if not frames:
        print("No skills remain after excluding your skills.")
        return

    plot_df = pd.concat(frames)

    # 7) Plot grouped bar chart
    fig = px.bar(
        plot_df,
        x='skill',
        y='count',
        color='company',
        barmode='group',
        title=f"Top {top_n_skills} Missing Skills by Company (Top {top_n_companies} Employers)",
        labels={'count': '# of Postings', 'skill': 'Skill'}
    )
    fig.update_layout(template='plotly_dark', xaxis_tickangle=-45)

    out_file = "company_skill_focus.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    # Example standalone call, replace with actual user skills
    plot_company_skill_focus(["python", "sql"])
