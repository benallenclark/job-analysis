import plotly.graph_objects as go
import networkx as nx
import numpy as np

def plot_skill_clusters(job_skill_map, max_skills=1000, min_edge_weight=3):
    print("Launching 3D skill cluster visualization...")

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
        if weight >= min_edge_weight:
            G.add_edge(a, b, weight=weight)

    if len(G.nodes) > max_skills:
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:max_skills]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    pos = nx.spring_layout(G, dim=3, weight="weight", seed=42)
    coords = np.array([pos[n] for n in G.nodes()])
    labels = list(G.nodes())
    degrees = np.array([G.degree[n] for n in labels])

    # Create 3D edge traces (initially hidden)
    edge_traces = []
    edge_map = {}  # for sidebar display
    for node in G.nodes():
        edge_map[node] = []
        for neighbor in G.neighbors(node):
            x0, y0, z0 = pos[node]
            x1, y1, z1 = pos[neighbor]
            edge_map[node].append((neighbor, G.degree[neighbor]))
            edge_traces.append(go.Scatter3d(
                x=[x0, x1, None], y=[y0, y1, None], z=[z0, z1, None],
                mode='lines',
                line=dict(color='rgba(255,255,255,0.6)', width=2),
                hoverinfo='none',
                hovertemplate="%{text}<extra></extra>",
                name=f'{node}↔{neighbor}',
                visible=False
            ))

    trace = go.Scatter3d(
        x=coords[:, 0], y=coords[:, 1], z=coords[:, 2],
        mode='markers',
        marker=dict(
            size=5,
            color=degrees,
            colorscale='Viridis',
            opacity=0.8,
            line=dict(width=0),
        ),
        text=labels,
        hovertemplate="%{text}<extra></extra>"  # Hides XYZ
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

    fig = go.Figure(data=[trace] + edge_traces, layout=layout)
    fig.write_html("skill_clusters_3d.html", auto_open=True, include_plotlyjs='cdn')

    with open("skill_clusters_3d.html", "a", encoding="utf-8") as f:
        f.write("""
<script>
document.addEventListener('DOMContentLoaded', () => {
    const plotDiv = document.querySelector(".js-plotly-plot");

    if (!plotDiv) return;

    plotDiv.on('plotly_hover', function(data) {
        const node = data.points[0].text;
        const traces = plotDiv.data;
        const vis = [];

        for (let i = 0; i < traces.length; i++) {
            if (i === 0) {
                vis.push(true);  // Node trace always on
            } else if (traces[i].name.startsWith(node + '↔') || traces[i].name.endsWith('↔' + node)) {
                vis.push(true);  // Show only edges connected to hovered node
            } else {
                vis.push(false); // Hide all other edges
            }
        }

        Plotly.restyle(plotDiv, { visible: vis });
    });

    plotDiv.on('plotly_unhover', function() {
        const traces = plotDiv.data;
        const vis = traces.map((_, i) => i === 0); // Only node scatter trace stays on
        Plotly.restyle(plotDiv, { visible: vis });
    });
});
</script>

""")
