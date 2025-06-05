# charts/plot_skill_cooccurrence_network.py

import sqlite3
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import os
import webbrowser

def plot_skill_cooccurrence_network(
    user_selected_skills,
    db_path="preview_jobs.db",
    min_edge_weight=5,
    min_node_degree=3,
    min_skill_degree_for_edges=50,
    spring_k=0.40,
    spring_iterations=150
):
    """
    1) user_selected_skills: list of skill strings to exclude (already owned by the user)
    2) Connects to preview_jobs.db
    3) SELECT job_id, name FROM skills
    4) Build co-occurrence counts, then:
         • Keep only edges with weight ≥ min_edge_weight
         • Remove nodes whose degree < min_node_degree
         • Remove any node in user_selected_skills
    5) Compute spring layout with k=spring_k
    6) While drawing edges, skip any edge if either endpoint has degree < min_skill_degree_for_edges
    7) Plot nodes without on‐page labels (use hover instead)
    8) Save to 'skill_network_2d.html' and open it
    """
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at '{db_path}'")
        return

    # Normalize user_selected_skills
    excluded_set = set(s.strip().lower() for s in user_selected_skills)

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT job_id, name AS skill FROM skills", conn)
    except Exception as e:
        print("ERROR reading from 'skills' table:", e)
        conn.close()
        return
    conn.close()

    if df.empty:
        print("No data found in 'skills' table.")
        return

    # 1) Build co‐occurrence counts (skill pairs)
    co_occ = {}
    grouped = df.groupby("job_id")["skill"].apply(
        lambda s: [x.strip().lower() for x in s.tolist()]
    )
    for slist in grouped:
        for i in range(len(slist)):
            for j in range(i + 1, len(slist)):
                a, b = sorted([slist[i], slist[j]])
                co_occ[(a, b)] = co_occ.get((a, b), 0) + 1

    # 2) Build graph, but only add edges whose weight ≥ min_edge_weight
    G = nx.Graph()
    for (a, b), w in co_occ.items():
        if w >= min_edge_weight:
            G.add_edge(a, b, weight=w)

    if G.number_of_edges() == 0:
        print(f"No edges with weight ≥ {min_edge_weight}. Try lowering min_edge_weight.")
        return

    # 3) Remove nodes whose degree < min_node_degree
    low_deg_nodes = [n for n, d in G.degree() if d < min_node_degree]
    G.remove_nodes_from(low_deg_nodes)

    if G.number_of_nodes() == 0:
        print(f"No nodes with degree ≥ {min_node_degree}. Try lowering min_node_degree.")
        return

    # 4) Remove any nodes that the user has already selected
    G.remove_nodes_from(excluded_set.intersection(G.nodes()))

    if G.number_of_nodes() == 0:
        print("After excluding your skills, no nodes remain. Try adjusting thresholds.")
        return

    # 5) Recompute degrees (after removal) for edge filtering and sizes
    deg = dict(G.degree())
    # 6) Compute spring layout
    pos = nx.spring_layout(G, k=spring_k, iterations=spring_iterations)
    # pos = nx.kamada_kawai_layout(G)


    # 7) Build edge traces, skipping edges where either node's degree < min_skill_degree_for_edges
    edge_x, edge_y = [], []
    for u, v, data in G.edges(data=True):
        if deg[u] < min_skill_degree_for_edges or deg[v] < min_skill_degree_for_edges:
            continue
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(width=0.5, color="gray"),
        hoverinfo="none"
    )

    # 8) Build node trace (no on‐page labels, use hover)
    nodes = list(G.nodes())
    node_x = [pos[n][0] for n in nodes]
    node_y = [pos[n][1] for n in nodes]
    node_deg = [deg[n] for n in nodes]
    hover_text = [f"{n} (degree={deg[n]})" for n in nodes]

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        marker=dict(
            size=[3 + d * 0.3 for d in node_deg],
            color=node_deg,
            colorscale="Bluered",
            cmin=0,
            cmax=max(node_deg),
            line_width=0.5
        ),
        hovertext=hover_text,
        hoverinfo="text",
        showlegend=False
    )

    # 9) Create figure
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=(
            "Skill Co‐occurrence Network (2D Force‐Directed)<br>"
            f"(Edges≥{min_edge_weight}, Nodes≥deg{min_node_degree}, "
            f"Edges drawn only if both endpoints ≥ deg{min_skill_degree_for_edges})"
        ),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="white",
        margin=dict(t=50, b=0, l=0, r=0)
    )

    # 10) Save & open HTML
    out_file = "skill_network_2d.html"
    fig.write_html(out_file, auto_open=False)
    print(f"Saved network graph to '{out_file}'")
    abs_path = os.path.abspath(out_file)
    webbrowser.open(f"file://{abs_path}")


if __name__ == "__main__":
    # Example standalone usage; exclude no skills:
    plot_skill_cooccurrence_network(user_selected_skills=[]) 
