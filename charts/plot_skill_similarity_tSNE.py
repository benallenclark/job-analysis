import os
import sqlite3
import pandas as pd
import numpy as np
import webbrowser
import warnings

# ── Prevent loky from spawning WMIC subprocess on Windows ─────────────────────
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
import plotly.express as px


def plot_skill_similarity_tSNE(db_path="preview_jobs.db", perplexity=30, max_iter=500):
    """
    1) Load job_id, job_title, company, salary_avg from jobs, and skill name from skills.
    2) Build a 'skill_doc' per job by joining all its skills into one string.
    3) Compute TF-IDF vectors on these skill-documents.
    4) Run t-SNE (with warnings suppressed) to reduce TF-IDF vectors to 2D.
    5) Plot a scatter where each point is a job:
         • x = tsne_x
         • y = tsne_y
         • color = salary_avg
         • hover shows job_title, company, salary_avg
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    # 1) Load jobs and skills
    conn = sqlite3.connect(db_path)
    try:
        job_df = pd.read_sql_query(
            "SELECT job_id, title AS job_title, company, salary_avg FROM jobs",
            conn
        )
        skill_df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if job_df.empty or skill_df.empty:
        print("No data found in jobs or skills tables.")
        return

    # Only keep jobs that already have a numeric salary_avg
    job_df = job_df.dropna(subset=["salary_avg"])
    valid_ids = set(job_df["job_id"])

    # Filter skills to only those valid job_ids
    skill_df = skill_df[skill_df["job_id"].isin(valid_ids)].copy()
    skill_df["skill"] = skill_df["skill"].str.strip().str.lower()

    # 2) Aggregate skills per job into a single 'skill_doc' column
    skill_docs = (
        skill_df
        .groupby("job_id")["skill"]
        .agg(" ".join)
        .reset_index()
        .rename(columns={"skill": "skill_doc"})
    )

    # Merge with job_df to get job_title, company, salary_avg, and skill_doc
    merged = job_df.merge(skill_docs, on="job_id", how="inner")
    if merged.empty:
        print("No jobs with both salary and skills.")
        return

    # 3) Compute TF-IDF on 'skill_doc'
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(merged["skill_doc"])

    # 4) Run t-SNE to reduce to 2D (suppress warnings)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # suppress deprecation/user warnings
        tsne = TSNE(n_components=2, perplexity=perplexity, max_iter=max_iter, random_state=42)
        embeddings = tsne.fit_transform(tfidf_matrix.toarray())

    merged["tsne_x"] = embeddings[:, 0]
    merged["tsne_y"] = embeddings[:, 1]

    # 5) Plot with Plotly
    fig = px.scatter(
        merged,
        x="tsne_x",
        y="tsne_y",
        color="salary_avg",
        size_max=8,
        hover_data=["job_title", "company", "salary_avg"],
        color_continuous_scale="Viridis",
        title="t-SNE of Jobs by Skill TF-IDF (Colored by Salary)"
    )
    fig.update_layout(template="plotly_dark")

    out_file = "skill_similarity_tsne.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved t-SNE plot to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_skill_similarity_tSNE()
