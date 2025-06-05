# charts/plot_title_salary_bubble_chart.py

import sqlite3
import pandas as pd
import plotly.express as px
import re
import os
import webbrowser

def parse_salary(sal_str):
    """
    Parse raw salary text (e.g. "$60k - $80k a year" or "$25 - $30 an hour") 
    to a numeric USD/year midpoint. Returns float or None.
    """
    if not isinstance(sal_str, str):
        return None

    text = sal_str.lower().strip()
    # Hourly vs. yearly
    is_hourly = "hour" in text
    # Find two numbers (if range) or one number
    nums = re.findall(r"\$?([\d,]+)(?:k)?(?:\.\d+)?", text)
    if not nums:
        return None

    # Convert each to float (detect 'k' suffix)
    def to_val(tok):
        tok = tok.replace(",", "")
        val = float(tok)
        # Multiply by 1000 if 'k' was in the original token
        if tok.endswith("k") or "k" in text:
            val *= 1000
        return val

    # If it’s a range (at least two numbers), take first two
    if len(nums) >= 2:
        try:
            lo = to_val(nums[0])
            hi = to_val(nums[1])
        except:
            return None
    else:
        try:
            lo = to_val(nums[0])
            hi = lo
        except:
            return None

    # If hourly, convert to yearly assuming 2080 hours/year
    if is_hourly:
        lo *= 2080
        hi *= 2080

    return (lo + hi) / 2.0


def plot_title_salary_bubble_chart(db_path="preview_jobs.db"):
    """
    1) Connect to preview_jobs.db
    2) SELECT job_id, title, salary FROM jobs
    3) Parse salary → salary_val (USD/year)
    4) Drop rows with missing salary_val
    5) Group by title → avg_salary, count (# postings)
    6) Filter to titles with ≥ 20 postings, keep top 50 by count
    7) Plot bubble chart: x=avg_salary, y=count, size=count, color=avg_salary
    """

    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT job_id, title AS job_title, salary FROM jobs",
            conn
        )
    except Exception as e:
        print("ERROR reading from 'jobs' table:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No rows found in 'jobs' table.")
        return

    # Parse salary text to numeric midpoint (USD/year)
    df["salary_val"] = df["salary"].apply(parse_salary)

    # Drop rows where salary_val is None
    df = df.dropna(subset=["salary_val"])

    if df.empty:
        print("No valid salary values after parsing.")
        return

    # Group by job title
    agg = (
        df.groupby("job_title")
          .agg(
              avg_salary=("salary_val", "mean"),
              count=("job_id", "count")
          )
          .reset_index()
    )

    # Filter to titles with ≥ 20 postings, then take top 50 by count
    agg = agg[agg["count"] >= 2]
    if agg.empty:
        print("No job titles have ≥ 20 postings with valid salary.")
        return
    agg = agg.nlargest(100, "count")

    # Create bubble chart: size=count, color=avg_salary
    fig = px.scatter(
        agg,
        x="avg_salary",
        y="count",
        size="count",
        color="avg_salary",
        hover_name="job_title",
        color_continuous_scale="Turbo",
        title="Job Title vs. Salary vs. Posting Volume (Bubble=Volume)",
        labels={
            "avg_salary": "Average Salary (USD/year)",
            "count": "# of Postings"
        }
    )
    fig.update_layout(template="plotly_dark")

    out_file = "title_salary_bubble.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved bubble chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_title_salary_bubble_chart()
