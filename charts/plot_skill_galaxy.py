import plotly.graph_objects as go
import networkx as nx
import numpy as np

def plot_skill_galaxy(job_skill_map, show_edges=True):
    # Step 1: Build co-occurrence graph
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
        if weight >= 3:
            G.add_edge(a, b, weight=weight)

    # 3D spring layout
    pos = nx.spring_layout(G, dim=3, seed=42, weight='weight')
    node_x, node_y, node_z, node_labels = [], [], [], []
    for node in G.nodes():
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        node_labels.append(node)

    # Plot nodes
    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=node_labels,
        textposition='top center',
        hoverinfo='text',
        marker=dict(
            size=6,
            color='skyblue',
            opacity=0.8
        )
    )

    # Plot edges
    edge_x, edge_y, edge_z, edge_colors = [], [], [], []
    weights = [d['weight'] for _, _, d in G.edges(data=True)]
    min_w, max_w = min(weights, default=1), max(weights, default=10)

    def weight_to_color(w):
        norm = (w - min_w) / (max_w - min_w + 1e-5)
        return f"rgb({int(255 * norm)}, 0, {int(255 * (1 - norm))})"  # red to blue

    for a, b, data in G.edges(data=True):
        x0, y0, z0 = pos[a]
        x1, y1, z1 = pos[b]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]
        edge_colors.append(weight_to_color(data['weight']))

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode='lines',
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        opacity=0.5
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title="Skill Galaxy (3D)",
        title_font_size=20,
        showlegend=False,
        margin=dict(l=0, r=0, b=0, t=40),
        paper_bgcolor='rgb(30,30,30)',
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='rgb(30,30,30)'
        )
    )

    fig.show()
