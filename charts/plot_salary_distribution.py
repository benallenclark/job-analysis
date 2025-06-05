# plot_salary_distribution.py

import sqlite3
import pandas as pd
import plotly.express as px


def plot_salary_distribution(db_path="preview_jobs.db", group_by="skill"):
    """
    Connects to the SQLite file (with cleaned salary columns), pulls:
      - job_id
      - salary_avg  (already numeric, USD/year)
      - skill
      - city       (location_details)
    Then either:
      - groups by skill (top 5), or
      - groups by city.
    Finally, generates a Plotly violin plot in 'salary_distribution.html'.
    """

    # 1) Open connection and join jobs ↔ skills
    conn = sqlite3.connect(db_path)

    sql = """
        SELECT
            j.job_id,
            j.salary_avg AS salary_val,
            s.name        AS skill,
            j.location_details AS city
        FROM jobs AS j
        INNER JOIN skills AS s
            ON j.job_id = s.job_id
        WHERE 
            j.salary_avg IS NOT NULL
            AND j.salary_avg <= 200000
            AND j.salary_avg >= 25000

    """

    df = pd.read_sql_query(sql, conn)
    conn.close()

    # 2) Now df.salary_val is already numeric (USD/year). No parsing required.

    # 3) Decide grouping logic
    if group_by == "skill":
        # Normalize skill text:
        df['skill'] = df['skill'].str.strip().str.lower()

        # Pick top 5 skills by frequency
        top5 = df['skill'].value_counts().nlargest(15).index.tolist()
        df = df[df['skill'].isin(top5)]

        title = "Salary Distribution by Skill"
        xaxis = "skill"

    else:  # group_by == "city"
        # Title-case city for readability; fill missing with "Unknown"
        df['city'] = df['city'].str.title().fillna("Unknown")
        title = "Salary Distribution by City"
        xaxis = "city"

    # 4) Build a Plotly violin plot using numeric salary_val
    fig = px.violin(
        df,
        x=xaxis,
        y="salary_val",
        box=True,
        points="all",
        color=xaxis,
        hover_data=['job_id'],
        title=title
    )

    fig.update_layout(
        template="plotly_dark",
        yaxis_title="Salary (USD/year)"
    )

    # 5) Write out the HTML and auto-open in your browser
    fig.write_html("salary_distribution.html", auto_open=True)


if __name__ == "__main__":
    # Choose group_by="skill" or group_by="city"
    plot_salary_distribution(group_by="skill")
