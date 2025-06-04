import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import networkx as nx
import matplotlib.cm as cm
import matplotlib.colors as mcolors
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

    # Step 2: Use spring layout for natural clustering (scale weights as attraction strength)
    pos_2d = nx.spring_layout(G, weight='weight', dim=3, seed=42)  # 3D layout using spring physics
    pos = {k: (v[0], v[1], v[2]) for k, v in pos_2d.items()}

    # Normalize weights for color gradient
    weights = [d['weight'] for _, _, d in G.edges(data=True)]
    if not weights:
        weights = [1]
    norm = mcolors.Normalize(vmin=min(weights), vmax=max(weights))
    cmap = cm.get_cmap('plasma')

    # Plot
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title("Skill Galaxy – Clustered by Co-occurrence")

    # Draw nodes
    xs, ys, zs = zip(*[pos[n] for n in G.nodes()])
    ax.scatter(xs, ys, zs, s=40, c='skyblue', alpha=0.9)

    if show_edges:
        for a, b, data in G.edges(data=True):
            x = [pos[a][0], pos[b][0]]
            y = [pos[a][1], pos[b][1]]
            z = [pos[a][2], pos[b][2]]
            color = cmap(norm(data['weight']))
            ax.plot(x, y, z, c=color, linewidth=1.0, alpha=0.7)

    # Interactivity enabled when plt.show() is called by Tk backend
    return fig
