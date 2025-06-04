import plotly.graph_objects as go
import networkx as nx
import numpy as np
from pathlib import Path

def plot_skill_clusters(job_skill_map, max_skills=1000, min_edge_weight=3):
    print("Launching 3D skill cluster visualization...")

    # Build co-occurrence graph
    co_occurrence = {}
    for skills in job_skill_map.values():
        skills = list(skills)
        for i in range(len(skills)):
            for j in range(i + 1, len(skills)):
                a, b = skills[i].lower(), skills[j].lower()
                edge = tuple(sorted([a, b]))
                co_occurrence[edge] = co_occurrence.get(edge, 0) + 1

    G = nx.Graph()
    for (a, b), weight in co_occurrence.items():
        if weight >= min_edge_weight:
            G.add_edge(a, b, weight=weight)

    if len(G.nodes) > max_skills:
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:max_skills]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    pos = nx.spring_layout(G, dim=3, weight="weight", seed=42)
    coords = np.array([pos[n] for n in G.nodes()])
    labels = list(G.nodes())
    degrees = np.array([G.degree[n] for n in labels])

    # Build edge map for JS
    edge_segments = {}
    edge_x_all, edge_y_all, edge_z_all = [], [], []

    for i, (a, b) in enumerate(G.edges()):
        x0, y0, z0 = pos[a]
        x1, y1, z1 = pos[b]
        
        edge_segments.setdefault(a, []).append([x0, x1, None])
        edge_segments.setdefault(b, []).append([x0, x1, None])
        edge_segments.setdefault(a + "_y", []).append([y0, y1, None])
        edge_segments.setdefault(b + "_y", []).append([y0, y1, None])
        edge_segments.setdefault(a + "_z", []).append([z0, z1, None])
        edge_segments.setdefault(b + "_z", []).append([z0, z1, None])


    # Initially blank edge trace
    edge_trace = go.Scatter3d(
        x=[],
        y=[],
        z=[],
        mode='lines',
        line=dict(color='rgba(255,255,255,0.9)', width=2),
        hoverinfo='none',
        name='edges'
    )
    def format_into_text_columns(pairs, max_per_col=30, max_cols=5):
        # Sort by weight descending
        pairs.sort(key=lambda x: x[1], reverse=True)

        # Format each item as padded string using non-breaking spaces
        items = [f"{label} ({weight})" for label, weight in pairs]
        max_items = max_per_col * max_cols
        items = items[:max_items]

        # Split into vertical columns
        num_cols = (len(items) + max_per_col - 1) // max_per_col
        columns = [items[i * max_per_col:(i + 1) * max_per_col] for i in range(num_cols)]

        # Pad to equal height
        height = max(len(col) for col in columns)
        for col in columns:
            col += [''] * (height - len(col))

        # Build row-by-row with non-breaking spacing
        lines = []
        for row_idx in range(height):
            row = [col[row_idx].ljust(25).replace(" ", "&nbsp;") for col in columns]
            lines.append("&nbsp;&nbsp;&nbsp;&nbsp;".join(row))

        return "<br>".join(lines)






    hover_texts = []
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        neighbor_pairs = [(neighbor, G[node][neighbor]['weight']) for neighbor in neighbors]
        tooltip_text = format_into_text_columns(neighbor_pairs)

        hover_texts.append(f"<b>{node}</b><br><br>{tooltip_text}")




    # Node trace
    trace = go.Scatter3d(
        x=coords[:, 0],
        y=coords[:, 1],
        z=coords[:, 2],
        mode='markers',
        marker=dict(
            size=[5] * len(labels),
            color=degrees,
            colorscale='Viridis',
            opacity=0.9,
            line=dict(width=0),
        ),
        text=hover_texts,
        hoverinfo="text"
    )


    layout = go.Layout(
        margin=dict(l=0, r=0, b=0, t=0),
        scene=dict(
            bgcolor='rgb(10,10,10)',
            xaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False, title=''),
            yaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False, title=''),
            zaxis=dict(showbackground=False, showticklabels=False, showgrid=False, zeroline=False, title=''),
        )
    )

    # Final figure
    fig = go.Figure(data=[edge_trace, trace], layout=layout)
    fig.write_html("skill_clusters_3d.html", auto_open=True, include_plotlyjs='cdn', full_html=True)