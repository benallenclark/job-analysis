# word_cloud_job_titles.py

import sqlite3
import pandas as pd
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import webbrowser
import os


def make_word_cloud(text, filename):
    """
    Given a long text blob, generate a PNG word cloud and save to `filename`.
    """
    stopwords = set(STOPWORDS)
    wc = WordCloud(
        background_color="white",
        stopwords=stopwords,
        max_words=200,
        width=800,
        height=400
    ).generate(text)

    # Plot and save
    plt.figure(figsize=(10, 5))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def run_word_clouds(db_path="preview_jobs.db"):
    """
    1) Connect to preview_jobs.db
    2) SELECT all job titles from the 'jobs' table
    3) Combine them into one large text blob
    4) Call make_word_cloud(...) to produce 'wc_job_titles.png'
    5) Open the PNG in your default image viewer
    """
    # 1) Connect to SQLite
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)

    try:
        # 2) Read every title from jobs
        df = pd.read_sql_query("SELECT title FROM jobs WHERE title IS NOT NULL", conn)
    except Exception as e:
        print("ERROR reading from 'jobs' table:", e)
        conn.close()
        return

    conn.close()

    if df.empty:
        print("No job titles found in the 'jobs' table.")
        return

    # 3) Build one giant string of all titles
    combined_text = " ".join(df['title'].dropna().tolist())

    # 4) Generate and save the word cloud
    output_filename = "wc_job_titles.png"
    make_word_cloud(combined_text, output_filename)
    print(f"✅  Saved word cloud to '{output_filename}'")

    # 5) Auto‐open the PNG in the default viewer
    abs_path = os.path.abspath(output_filename)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    run_word_clouds()
