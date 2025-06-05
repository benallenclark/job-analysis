import networkx as nx
import numpy as np
import plotly.graph_objects as go
from sklearn.manifold import SpectralEmbedding
from networkx.algorithms import community as nx_community

def plot_skill_clusters_radial(job_skill_map, max_skills=1000, min_edge_weight=1):
    """
    Draw a 2D radial layout in which:
      - Each detected community is assigned its own wedge of the circle.
      - Within each wedge, skills are placed along a ray from center → outer circle,
        with “important” (high‐degree) skills closer to center, and less connected
        ones near the rim.
      - Node color = community ID.
      - Hover text remains the skill name + top co‐occurring neighbors.
    """
    # ─── 1. Build co‐occurrence graph (same as before) ───────────────────────
    co_occurrence = {}
    for skills in job_skill_map.values():
        skill_list = [s.lower() for s in skills]
        for i in range(len(skill_list)):
            for j in range(i + 1, len(skill_list)):
                a, b = skill_list[i], skill_list[j]
                edge = tuple(sorted([a, b]))
                co_occurrence[edge] = co_occurrence.get(edge, 0) + 1

    G = nx.Graph()
    for (a, b), weight in co_occurrence.items():
        if weight >= min_edge_weight:
            G.add_edge(a, b, weight=weight)

    # ─── 1b. Ensure every skill (even with zero edges) is added as a node ─
    all_skills = {s.lower() for skills in job_skill_map.values() for s in skills}
    G.add_nodes_from(all_skills)
    
     # ─── Remove any skill‐node that has degree=0 (i.e. no “heavy” co‐occurrence) ──
    isolates = [node for node, deg in G.degree() if deg == 0]
    
    from collections import Counter

    flat_skills = [s.lower() for skills in job_skill_map.values() for s in skills]
    freq = Counter(flat_skills)
    for iso in isolates:
        print(f"{iso!r} appears in {freq[iso]} listing(s)")

    if isolates:
        #print(isolates)
        G.remove_nodes_from(isolates)



    if len(G.nodes) > max_skills:
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:max_skills]
        keep = {n for n, _ in top_nodes}
        G = G.subgraph(keep).copy()
        
        

    # ─── 2. Detect communities ────────────────────────────────────────────────
    try:
        communities = list(nx_community.greedy_modularity_communities(G, weight="weight"))
    except Exception:
        communities = [set(G.nodes())]

    # Map each node → its community index
    node_to_comm = {}
    for idx, comm in enumerate(communities):
        for node in comm:
            node_to_comm[node] = idx

    # ─── 3. For each community, gather node‐degrees and sort by importance ───
    #    (“importance” = total co‐occurrence weight = node degree in G)
    comm_degrees = {}
    max_deg = 1
    for idx, comm in enumerate(communities):
        degs = {node: G.degree[node] for node in comm}
        comm_degrees[idx] = degs
        local_max = max(degs.values()) if degs else 1
        max_deg = max(max_deg, local_max)

    # ─── 4. Assign angular wedges for each community ─────────────────────────
    num_comms = len(communities)
    # center angle of wedge i = (i + 0.5) * 2π/num_comms
    angles = {}
    for i in range(num_comms):
        start = 2 * np.pi * i / num_comms
        end   = 2 * np.pi * (i + 1) / num_comms
        center = (start + end) / 2
        angles[i] = (start, end, center)

    # ─── 5. For each skill/node → compute (radius, angle) in its wedge ──────
    labels = list(G.nodes())
    coords = np.zeros((len(labels), 2))  # (x, y) for each node
    node_degrees = np.array([G.degree[n] for n in labels], dtype=float)
    node_comm_ids = np.array([node_to_comm[n] for n in labels], dtype=int)

    hover_texts = []
    for node in labels:
        # Build hover text showing top neighbors
        nbrs = [(nbr, G[node][nbr]["weight"]) for nbr in G.neighbors(node)]
        nbrs_sorted = sorted(nbrs, key=lambda x: x[1], reverse=True)
        lines = [f"{nbr} ({w})" for nbr, w in nbrs_sorted[:10]]
        hover_texts.append(f"<b>{node}</b><br>" + "<br>".join(lines))

    # Precompute: for each community, sort its nodes by degree descending
    sorted_by_degree = {}
    for comm_idx, deg_dict in comm_degrees.items():
        sorted_list = sorted(deg_dict.items(), key=lambda kv: kv[1], reverse=True)
        # just keep the node names in sorted order
        sorted_by_degree[comm_idx] = [node for node, _ in sorted_list]

    # Now assign radius/angle to each node
    for i, node in enumerate(labels):
        comm_id = node_to_comm[node]
        deg = G.degree[node]
        # radius from [r_min, r_max] (choose inner radius = 0.1, outer = 1.0)
        # We invert so that high‐degree (deg ~ local_max) → small radius (near center)
        local_max = max(comm_degrees[comm_id].values()) or 1
        r_min, r_max = 0.1, 1.0
        # radius = r_min + (r_max - r_min) * (1 - deg/local_max)
        radius = r_min + (r_max - r_min) * (1.0 - deg / local_max)

        # angle = “middle of wedge” + tiny jitter so points don’t all lie on the same ray
        wedge_start, wedge_end, wedge_center = angles[comm_id]
        jitter = (wedge_end - wedge_start) * 0.15  # up to 15% of the wedge width
        theta = wedge_center + np.random.uniform(-jitter, +jitter)

        # Convert polar → Cartesian
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        coords[i, 0] = x
        coords[i, 1] = y

    # ─── 6. Build edge‐lines (optional, but helpful to see strong co‐occurrences) ─
    edge_x, edge_y = [], []
    for u, v, data in G.edges(data=True):
        i_u = labels.index(u)
        i_v = labels.index(v)
        # only draw if weight ≥ some threshold (e.g. ≥ 2 * min_edge_weight)
        if data["weight"] >= min_edge_weight * 2:
            x0, y0 = coords[i_u]
            x1, y1 = coords[i_v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode="lines",
        line=dict(color="rgba(200,200,200,0.2)", width=1),
        hoverinfo="none",
        showlegend=False
    )

    # 7a. Define the “high‐degree” threshold
    threshold = 200

    # 7b. Partition indices
    high_idx = [i for i, deg in enumerate(node_degrees) if deg >= threshold]
    low_idx  = [i for i, deg in enumerate(node_degrees) if deg <  threshold]

    # 7c. Build low‐degree trace (blue→red up to threshold)
    low_trace = go.Scatter(
        x=[coords[i, 0] for i in low_idx],
        y=[coords[i, 1] for i in low_idx],
        mode="markers",
        marker=dict(
            size=[8 + 4 * (node_degrees[i] / max_deg) for i in low_idx],
            color=[node_degrees[i] for i in low_idx],
            colorscale="Bluered",
            cmin=0,
            cmax=threshold,             # clamp at threshold so red peaks at 200
            colorbar=dict(title="Degree"),  # optional legend for color ramp
            line=dict(width=0),
            opacity=0.9,
        ),
        text=[hover_texts[i] for i in low_idx],
        hoverinfo="text",
        name=f"deg < {threshold}"
    )

    # 7d. Build high‐degree trace (all gold)
    high_trace = go.Scatter(
        x=[coords[i, 0] for i in high_idx],
        y=[coords[i, 1] for i in high_idx],
        mode="markers",
        marker=dict(
            size=[8 + 4 * (node_degrees[i] / max_deg) for i in high_idx],
            color="gold",               # fixed gold color
            line=dict(width=1, color="black"),  # optional black outline
            opacity=1.0,
        ),
        text=[hover_texts[i] for i in high_idx],
        hoverinfo="text",
        name=f"deg ≥ {threshold}"
    )


    # ─── 8. Draw circle outline and cluster wedges (optional but clarifying) ─
    circle_theta = np.linspace(0, 2 * np.pi, 200)
    circle_x = np.cos(circle_theta)
    circle_y = np.sin(circle_theta)

    circle_trace = go.Scatter(
        x=circle_x,
        y=circle_y,
        mode="lines",
        line=dict(color="white", width=1),
        hoverinfo="none",
        showlegend=False
    )

    # Optionally, draw radial lines dividing each cluster wedge
    wedge_traces = []
    for i in range(num_comms):
        start, end, center = angles[i]
        # draw a straight line from r=0 to r=1 at both start and end angles
        x_start = [0, np.cos(start)]
        y_start = [0, np.sin(start)]
        x_end   = [0, np.cos(end)]
        y_end   = [0, np.sin(end)]
        wedge_traces.append(go.Scatter(x=x_start, y=y_start, mode="lines",
                                       line=dict(color="rgba(255,255,255,0.1)", width=1),
                                       hoverinfo="none", showlegend=False))
        wedge_traces.append(go.Scatter(x=x_end, y=y_end, mode="lines",
                                       line=dict(color="rgba(255,255,255,0.1)", width=1),
                                       hoverinfo="none", showlegend=False))

    # ─── 9. Compose figure ───────────────────────────────────────────────────
    layout = go.Layout(
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="rgb(10,10,10)",
        paper_bgcolor="rgb(10,10,10)",
        margin=dict(l=0, r=0, t=0, b=0),
        width=800,
        height=800,
    )

    fig = go.Figure(
        data=[circle_trace] + wedge_traces + [edge_trace, low_trace, high_trace],
        layout=layout
    )
    fig.update_yaxes(scaleanchor="x", scaleratio=1)

    fig.write_html("skill_clusters_2d_radial.html", auto_open=True, include_plotlyjs="cdn", full_html=True)
