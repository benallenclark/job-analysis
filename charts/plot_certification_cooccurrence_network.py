# charts/plot_certification_cooccurrence_network.py

import sqlite3
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import os
import webbrowser
from collections import Counter
from itertools import combinations

def plot_certification_cooccurrence_network(
    db_path="preview_jobs.db",
    min_pair_count=5,
    min_node_freq=5,
    spring_k=0.5,
    spring_iterations=50
):
    """
    1) Read job_id→certification name from the 'certifications' table.
    2) Group by job_id to get a list of certs per job.
    3) Count how often each pair of certs appears together across all jobs.
    4) Build a NetworkX graph:
         • Include only certs that appear in ≥ min_node_freq postings.
         • Include only edges (a,b) with co-occurrence ≥ min_pair_count.
    5) Compute a spring layout and draw with Plotly:
         • Node size ~ frequency of that cert
         • Edge width ~ co-occurrence count
    6) Save as "certification_cooccurrence_network.html" and open in browser.
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT job_id, name AS certification FROM certifications",
            conn
        )
    except Exception as e:
        print("ERROR reading from 'certifications' table:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No rows found in 'certifications' table.")
        return

    # 2) For each job_id, gather its list of certifications
    certs_per_job = df.groupby("job_id")["certification"].apply(list)

    # 3) Count co-occurrence of each pair (sorted tuple)
    pair_counts = Counter()
    all_certs = []
    for cert_list in certs_per_job:
        # Only count pairs if there are at least 2 certs on that job
        unique_certs = list(set(cert_list))
        for a, b in combinations(sorted(unique_certs), 2):
            pair_counts[(a, b)] += 1
        # Also track individual cert frequencies
        all_certs.extend(unique_certs)

    cert_freq = Counter(all_certs)

    # 4) Build graph
    G = nx.Graph()
    # Add nodes only if freq ≥ min_node_freq
    for cert, freq in cert_freq.items():
        if freq >= min_node_freq:
            G.add_node(cert, freq=freq)

    # Add edges only when both endpoints exist in G and co-occurrence ≥ min_pair_count
    for (a, b), w in pair_counts.items():
        if w >= min_pair_count and a in G and b in G:
            G.add_edge(a, b, weight=w)

    if G.number_of_nodes() == 0:
        print(f"No certifications with freq ≥ {min_node_freq}. Try lowering that threshold.")
        return
    if G.number_of_edges() == 0:
        print(f"No pairs with co-occurrence ≥ {min_pair_count}. Try lowering that threshold.")
        return

    # 5) Compute 2D spring layout
    pos = nx.spring_layout(G, k=spring_k, iterations=spring_iterations, seed=42)

    # Build edge traces (x,y with None separators) and a separate parallel list for widths
    edge_x = []
    edge_y = []
    edge_widths = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_widths.append(data["weight"])

    # To draw varying widths, we need multiple segments. Simplest: draw each edge separately.
    edge_traces = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        w = data["weight"]
        trace = go.Scatter(
            x=[x0, x1],
            y=[y0, y1],
            mode="lines",
            line=dict(width=max(1, 0.3 * w), color="lightgray"),
            hoverinfo="none",
            showlegend=False
        )
        edge_traces.append(trace)

    # Build node trace
    node_x = []
    node_y = []
    node_size = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        freq = G.nodes[node]["freq"]
        node_size.append(20 + freq * 2)  # node size scales with freq
        node_text.append(f"{node.upper()}<br>#Postings: {freq}")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(size=node_size, color="gold", line=dict(width=1, color="black")),
        text=[n.upper() for n in G.nodes()],
        textposition="bottom center",
        hovertext=node_text,
        hoverinfo="text",
        showlegend=False
    )

    # 6) Compose figure
    fig = go.Figure(data=edge_traces + [node_trace])
    fig.update_layout(
        title=(
            f"Certification Co-Occurrence Network\n"
            f"(Node freq ≥ {min_node_freq}; Pair co-occurrence ≥ {min_pair_count})"
        ),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="white",
        margin=dict(t=50, b=0, l=0, r=0)
    )

    out_file = "certification_cooccurrence_network.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved network graph to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    # Example standalone call
    plot_certification_cooccurrence_network()
