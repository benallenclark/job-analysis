# plot_skill_network.py
from collections import defaultdict
from itertools import combinations
import networkx as nx
import matplotlib.pyplot as plt

def compute_skill_edges(job_skill_map):
    """
    Computes weighted edges between skills based on co-occurrence in job postings.

    Args:
        job_skill_map (dict): job_id → set of skills

    Returns:
        dict: (skill1, skill2) → count of co-occurrences
    """
    edge_weights = defaultdict(int)
    for skills in job_skill_map.values():
        skill_list = [s.lower() for s in skills]
        for skill1, skill2 in combinations(set(skill_list), 2):
            key = tuple(sorted([skill1, skill2]))
            edge_weights[key] += 1
    return edge_weights

def plot_skill_network(edge_weights, min_weight=5):
    """
    Plots a network graph of skills where edge thickness = co-occurrence frequency.

    Args:
        edge_weights (dict): (skill1, skill2) → weight
        min_weight (int): minimum weight for edge to be shown
    """
    G = nx.Graph()
    for (skill1, skill2), weight in edge_weights.items():
        if weight >= min_weight:
            G.add_edge(skill1, skill2, weight=weight)

    pos = nx.spring_layout(G, k=0.3, iterations=50)
    edges = G.edges(data=True)
    weights = [d["weight"] for (_, _, d) in edges]

    plt.figure(figsize=(14, 10))
    nx.draw(
        G, pos,
        with_labels=True,
        node_color="skyblue",
        node_size=800,
        width=[w * 0.2 for w in weights],
        edge_color="gray",
        font_size=8
    )
    plt.title("Skill Co-Occurrence Network")
    plt.tight_layout()
    plt.show()
