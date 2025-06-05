# charts/plot_certification_presence_by_skill_cluster.py

import os
import sqlite3
import pandas as pd
import plotly.express as px
import networkx as nx
from networkx.algorithms import community as nx_community
import webbrowser
from itertools import combinations

def plot_certification_presence_by_skill_cluster(
    db_path="preview_jobs.db",
    min_edge_weight=3,
    min_skill_degree=1,
    top_n_certs_per_cluster=10
):
    """
    1) Read job_id→skill from `skills` table.
    2) Build a skill‐cooccurrence graph (edges ≥ min_edge_weight).
    3) Detect communities (skill clusters) via greedy modularity.
    4) Assign each job to the cluster containing the largest number of its skills.
    5) Read job_id→certification name from `certifications` table.
    6) For each (cluster, certification), compute:
         • count = #jobs in that cluster requiring that cert
         • cluster_size = total #jobs assigned to that cluster
         • pct_of_cluster = 100 * count / cluster_size
    7) Optionally, keep only the top N certifications per cluster.
    8) Plot a faceted bar chart (one facet per cluster) showing % penetration by cert.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        # (1) Load job_id + skill
        skills_df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
        # (5) Load job_id + certification name
        certs_df = pd.read_sql_query("SELECT job_id, name AS certification FROM certifications", conn)
    except Exception as e:
        print("ERROR reading from database:", e)
        conn.close()
        return
    conn.close()

    if skills_df.empty:
        print("No rows in 'skills' table.")
        return
    if certs_df.empty:
        print("No rows in 'certifications' table.")
        return

    # (1b) Aggregate all skills per job_id into a comma‐separated string
    skills_df["skill"] = skills_df["skill"].str.strip().str.lower()
    skills_agg = (
        skills_df
        .groupby("job_id")["skill"]
        .agg(lambda vals: ",".join(vals))
        .reset_index()
        .rename(columns={"skill": "skills_str"})
    )

    # (2) Build skill co-occurrence counts across all jobs
    co_occ = {}
    for skills_str in skills_agg["skills_str"]:
        sl = [s.strip() for s in skills_str.split(",") if s.strip()]
        for i in range(len(sl)):
            for j in range(i + 1, len(sl)):
                edge = tuple(sorted([sl[i], sl[j]]))
                co_occ[edge] = co_occ.get(edge, 0) + 1

    # (2b) Build graph G where nodes are skills, edges weighted by co-occurrence
    G = nx.Graph()
    for (a, b), w in co_occ.items():
        if w >= min_edge_weight:
            G.add_edge(a, b, weight=w)

    # Remove isolated nodes whose degree < min_skill_degree
    isolates = [n for n, d in G.degree() if d < min_skill_degree]
    G.remove_nodes_from(isolates)

    if G.number_of_nodes() == 0:
        print(f"No skills remain with degree ≥ {min_skill_degree}.")
        return
    if G.number_of_edges() == 0:
        print(f"No edges with weight ≥ {min_edge_weight}.")
        return

    # (3) Detect communities (each community = one “skill cluster”)
    comms = list(nx_community.greedy_modularity_communities(G, weight="weight"))
    skill_to_cluster = {}
    for idx, comm in enumerate(comms):
        for skill in comm:
            skill_to_cluster[skill] = idx

    # (4) Assign each job a “primary” cluster (the cluster containing most of its skills)
    def primary_cluster(skills_str: str):
        if not isinstance(skills_str, str) or not skills_str.strip():
            return None
        sl = [s.strip() for s in skills_str.split(",") if s.strip()]
        cluster_counts = {}
        for s in sl:
            c = skill_to_cluster.get(s)
            if c is not None:
                cluster_counts[c] = cluster_counts.get(c, 0) + 1
        if not cluster_counts:
            return None
        return max(cluster_counts, key=lambda k: cluster_counts[k])

    skills_agg["cluster"] = skills_agg["skills_str"].apply(primary_cluster)

    # Drop any jobs without a cluster assignment
    skills_agg = skills_agg.dropna(subset=["cluster"])
    if skills_agg.empty:
        print("No jobs could be assigned to any skill cluster.")
        return

    # (5b) Join certifications to the cluster assignment
    # merged: job_id, skills_str, cluster, certification
    merged = skills_agg.merge(certs_df, on="job_id", how="inner")
    if merged.empty:
        print("No job has any certification in the database.")
        return

    # (6) Count how many jobs in each (cluster, certification)
    cc = (
        merged
        .groupby(["cluster", "certification"])
        .size()
        .reset_index(name="count")
    )

    # Determine cluster_size = total number of distinct jobs in that cluster
    cluster_sizes = skills_agg["cluster"].value_counts().to_dict()
    cc["cluster_size"] = cc["cluster"].map(cluster_sizes)
    cc["pct_of_cluster"] = cc["count"] / cc["cluster_size"] * 100

    # (7) Optionally filter to top_n_certs_per_cluster by frequency
    top_certs = (
        cc
        .sort_values(["cluster", "count"], ascending=[True, False])
        .groupby("cluster")
        .head(top_n_certs_per_cluster)
        .copy()
    )

    # (8) Plot faceted bar chart (one facet per cluster)
    fig = px.bar(
        top_certs,
        x="pct_of_cluster",
        y="certification",
        facet_col="cluster",
        facet_col_wrap=3,
        orientation="h",
        title=f"Top {top_n_certs_per_cluster} Certs by % Penetration in Each Skill Cluster",
        labels={"pct_of_cluster": "% of Jobs", "certification": "Certification"}
    )
    fig.update_layout(template="plotly_dark", height=600, showlegend=False)

    out_file = "certs_by_skill_cluster.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved chart to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    plot_certification_presence_by_skill_cluster()
