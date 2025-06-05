# charts/plot_company_skill_cluster_sankey.py

import os
import sqlite3
import pandas as pd
import numpy as np
import webbrowser

from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
import plotly.graph_objects as go

def plot_company_skill_cluster_sankey(
    db_path="preview_jobs.db",
    n_skill_clusters=10,
    min_jobs_per_company=5,
    top_skills_per_cluster=5
):
    """
    1) Load job_id→company from jobs and job_id→skill from skills.
    2) Filter out companies with fewer than min_jobs_per_company postings.
    3) Build a skill×job binary matrix, cluster each skill into n_skill_clusters.
    4) For each cluster:
         • Gather all skills assigned to that cluster.
         • Rank them by # of jobs they appear in (descending).
         • Keep top_skills_per_cluster for the cluster's label.
    5) For each (company, cluster), count distinct job_ids where any skill in that cluster appears.
    6) Build and render a Sankey diagram where:
         • source = company (left nodes)
         • target = “Cluster <i>: top_skill1, top_skill2, …” (right nodes)
         • value = # of postings at that company needing at least one skill in that cluster
    7) Save as “company_skill_cluster_sankey.html” and open in browser.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # (1) Read job↔company and job↔skill tables
        jobs_df = pd.read_sql_query(
            "SELECT job_id, company FROM jobs WHERE company IS NOT NULL",
            conn
        )
        skills_df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if jobs_df.empty or skills_df.empty:
        print("No data found in jobs or skills tables.")
        return

    # (2) Filter companies with at least min_jobs_per_company postings
    job_counts = jobs_df["company"].value_counts()
    keep_companies = job_counts[job_counts >= min_jobs_per_company].index.tolist()
    jobs_df = jobs_df[jobs_df["company"].isin(keep_companies)].copy()
    valid_jobs = set(jobs_df["job_id"])

    # Filter skills to only those jobs we kept
    skills_df = skills_df[skills_df["job_id"].isin(valid_jobs)].copy()
    skills_df["skill"] = skills_df["skill"].str.strip().str.lower()

    if skills_df.empty:
        print("No skill data after filtering to kept jobs.")
        return

    # (3) Build skill×job binary matrix
    #    Rows = skill, Cols = job_id. Entry = 1 if that skill appears in that job.
    skill_job_ct = (
        skills_df
        .drop_duplicates(["job_id", "skill"])
        .groupby(["skill", "job_id"])
        .size()
        .unstack(fill_value=0)
    )  # DataFrame: index=skill, columns=job_id

    skill_list = skill_job_ct.index.tolist()
    job_cols = skill_job_ct.columns.tolist()
    X = skill_job_ct.values  # shape = (n_skills, n_kept_jobs)
    # Normalize each row (skill) so KMeans isn’t dominated by high-frequency skills
    X_norm = normalize(X, norm="l2", axis=1)

    # If fewer skills than requested clusters, reduce n_skill_clusters
    n_skills = X_norm.shape[0]
    k = min(n_skill_clusters, n_skills)

    # Cluster skills
    kmeans = KMeans(n_clusters=k, random_state=42)
    labels = kmeans.fit_predict(X_norm)  # length = n_skills

    # Build a mapping skill → cluster_id
    skill_to_cluster = dict(zip(skill_list, labels))

    # (4) For each cluster, collect its skills and compute top by job frequency
    #    We know each row of skill_job_ct sums to how many jobs that skill appears in.
    skill_freq = skill_job_ct.sum(axis=1).to_dict()  # skill → # of jobs

    cluster_to_skills = {}
    for skill, cluster_id in skill_to_cluster.items():
        cluster_to_skills.setdefault(cluster_id, []).append(skill)

    # Now build a human‐readable label for each cluster
    cluster_labels = {}
    for cid, skills_in_cluster in cluster_to_skills.items():
        # Sort those skills by descending frequency
        sorted_skills = sorted(
            skills_in_cluster,
            key=lambda s: skill_freq.get(s, 0),
            reverse=True
        )
        # Keep top_skills_per_cluster
        top_n = sorted_skills[:top_skills_per_cluster]
        # Format label: “Cluster <i>: skill1, skill2, …”
        label = f"Cluster {cid}:\n" + "\n".join(top_n)
        cluster_labels[cid] = label

    # (5) For each (company, cluster), count distinct job_ids:
    #    Map each row in skills_df to its cluster_id via skill_to_cluster.
    skills_df["cluster_id"] = skills_df["skill"].map(skill_to_cluster)

    # Merge in company from jobs_df
    merged = skills_df.merge(jobs_df, on="job_id", how="inner")
    # Drop duplicates of (job_id, company, cluster_id)
    merged_unique = merged[["job_id", "company", "cluster_id"]].drop_duplicates()

    # Group by (company, cluster_id) to count distinct job_ids
    company_cluster_counts = (
        merged_unique
        .groupby(["company", "cluster_id"])
        .size()
        .reset_index(name="count")
    )  # columns: company, cluster_id, count

    if company_cluster_counts.empty:
        print("No company↔cluster counts to plot.")
        return

    # (6) Build Sankey nodes and links
    # Left nodes = companies, right nodes = clusters (with human‐readable labels)
    companies = sorted(company_cluster_counts["company"].unique())
    clusters = [cluster_labels[cid] for cid in sorted(cluster_labels.keys())]

    # Build label list: all companies first, then all cluster labels
    labels = companies + clusters

    # Map each company → index (0 … len(companies)-1)
    company_to_idx = {c: i for i, c in enumerate(companies)}
    # Map each cluster_label → index (len(companies) … len(companies)+len(clusters)-1)
    base_cluster_idx = len(companies)
    cluster_to_idx = {
        cluster_labels[cid]: base_cluster_idx + idx
        for idx, cid in enumerate(sorted(cluster_labels.keys()))
    }

    # Build source/target/value arrays
    source_idxs = []
    target_idxs = []
    values = []

    for _, row in company_cluster_counts.iterrows():
        comp = row["company"]
        cid = row["cluster_id"]
        cnt = row["count"]
        source_idxs.append(company_to_idx[comp])
        label = cluster_labels[cid]
        target_idxs.append(cluster_to_idx[label])
        values.append(cnt)

    # Create Sankey diagram
    link = dict(source=source_idxs, target=target_idxs, value=values)
    # Color left nodes blue, right nodes orange
    node_colors = ["#636EFA"] * len(companies) + ["#EF553B"] * len(clusters)
    node = dict(label=labels, pad=15, thickness=20, color=node_colors)

    fig = go.Figure(data=[go.Sankey(node=node, link=link)])
    fig.update_layout(
        title_text=(
            f"Company → Skill‐Cluster Sankey\n"
            f"(Each cluster lists its top {top_skills_per_cluster} skills)"
        ),
        font_size=12,
        template="plotly_dark"
    )

    out_file = "company_skill_cluster_sankey.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved Sankey to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_company_skill_cluster_sankey()
