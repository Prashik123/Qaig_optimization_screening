# Generates high-resolution graphical outputs for analytical reports and metric tracking.

import os
from typing import List, Dict
import numpy as np
import networkx as nx
import config

try:
    import matplotlib
    # Using TkAgg to enable interactive pop-up window rendering 
    matplotlib.use('TkAgg')  
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def plot_maxcut_partition(
    graph: nx.Graph, partitions: list, title: str, filename: str
):
    if not HAS_MATPLOTLIB:
        print(f"Skipped plotting '{filename}' -> Matplotlib is incompatible.")
        return

    plt.figure(figsize=(11, 9))
    pos = nx.spring_layout(graph, seed=config.RANDOM_SEED)
    
    nodes = list(graph.nodes())
    
    # Corrected list comprehension syntax
    colors = [
        '#2ECC71' if partitions[nodes.index(node)] == 1 else '#F1C40F' 
        for node in nodes
    ]
    
    # Draw base network configuration
    nx.draw_networkx_nodes(
        graph, pos, node_color=colors, node_size=700, 
        edgecolors='black', linewidths=1.5
    )
    nx.draw_networkx_labels(
        graph, pos, font_size=12, font_weight='bold', font_color='white'
    )
    nx.draw_networkx_edges(
        graph, pos, edge_color='#BDC3C7', width=1.5, style='dashed'
    )
    
    # Highlight successful cut edges in bold crimson red (added closing bracket)
    cut_edges = [
        (u, v) for u, v in graph.edges() 
        if partitions[nodes.index(u)] != partitions[nodes.index(v)]
    ]
    nx.draw_networkx_edges(
        graph, pos, edgelist=cut_edges, edge_color='#E52B50', width=3.5
    )
    
    # Compute and overlay literal edge weight indicators
    labels = nx.get_edge_attributes(graph, 'weight')
    formatted_labels = {k: f"{v:.1f}" for k, v in labels.items()}
    nx.draw_networkx_edge_labels(
        graph, pos, edge_labels=formatted_labels, 
        font_size=9, font_color='#2C3E50'
    )
    
    plt.title(
        f"{title}\n(Red Lines Denote Cut Edges)", 
        fontsize=13, fontweight='bold', pad=15
    )
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_vrptw_routes(
    depot, customers: list, routes: List[list], title: str, filename: str
):
    if not HAS_MATPLOTLIB:
        return

    plt.figure(figsize=(13, 11))
    
    # Render tracking layout with dynamic Depot coordinates in the legend
    plt.scatter(
        depot.x, depot.y, c='#E74C3C', marker='s', s=300, 
        edgecolors='black', label=f'Depot ({int(depot.x)},{int(depot.y)})', zorder=6
    )
    
    cx = [c.x for c in customers]
    cy = [c.y for c in customers]
    plt.scatter(
        cx, cy, c='#2C3E50', s=90, edgecolors='black', 
        label='Customer Nodes', zorder=4
    )
    
    # Overlay specific Customer ID and Demand parameters
    for c in customers:
        label_text = f"C{c.id}\n(D:{getattr(c, 'demand', 0)})"
        plt.annotate(
            label_text, (c.x, c.y), textcoords="offset points", 
            xytext=(0, 10), ha='center', fontsize=8, 
            fontweight='semibold', color='#34495E'
        )
        
    lookup = {0: depot}
    for c in customers:
        lookup[c.id] = c
        
    colormap = matplotlib.colormaps['tab10'].resampled(max(len(routes), 1))
    
    # Trace individual navigational paths with directional arrows 
    for v_id, route in enumerate(routes):
        if len(route) < 2:
            continue
        for i in range(len(route) - 1):
            n1 = lookup[route[i]]
            n2 = lookup[route[i + 1]]
            
            # Draw primary route segments
            plt.plot(
                [n1.x, n2.x], [n1.y, n2.y], c=colormap(v_id), 
                linewidth=2.5, alpha=0.85, 
                label=f'Vehicle {v_id + 1} Route' if i == 0 else ""
            )
            
            # Overlay directional arrows
            plt.annotate(
                '', xy=(n2.x, n2.y), xytext=(n1.x, n1.y),
                arrowprops=dict(
                    arrowstyle="->", color=colormap(v_id), 
                    lw=1.5, mutation_scale=15
                ),
                zorder=5
            )
            
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("X Coordinate Space", fontsize=11)
    plt.ylabel("Y Coordinate Space", fontsize=11)
    
    # Clean up duplicate legends
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(
        by_label.values(), by_label.keys(), 
        loc='upper right', bbox_to_anchor=(1.15, 1.0)
    )
    
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_vrptw_clusters(
    depot, clusters: Dict[int, List], title: str, filename: str
):

    # Visualizes the Phase 1 QUBO assignment, proving that 
    # the spatial quantum clustering successfully segregates nodes before classical routing.
    # Includes geographic centroids and spider-web connections to demonstrate optimization.
    
    if not HAS_MATPLOTLIB:
        return
        
    plt.figure(figsize=(11, 9))
    
    # Render depot with dynamic coordinate labeling
    plt.scatter(
        depot.x, depot.y, c='#E74C3C', marker='s', s=300, 
        edgecolors='black', label=f'Depot ({int(depot.x)},{int(depot.y)})', zorder=6
    )
    colormap = matplotlib.colormaps['tab10'].resampled(max(len(clusters), 1))
    
    for v_id, cluster_members in clusters.items():
        if not cluster_members:
            continue
            
        cx = [c.x for c in cluster_members]
        cy = [c.y for c in cluster_members]
        
        # Calculate cluster geographic centroid
        centroid_x = np.mean(cx)
        centroid_y = np.mean(cy)
        
        # Plot the centroid as a large star
        plt.scatter(
            centroid_x, centroid_y, color=colormap(v_id), 
            marker='*', s=400, edgecolors='black', zorder=5
        )
        
        # Draw spider-web lines from centroid to nodes
        for x, y in zip(cx, cy):
            plt.plot(
                [centroid_x, x], [centroid_y, y], color=colormap(v_id), 
                linestyle='--', linewidth=1.5, alpha=0.5, zorder=3
            )
            
        plt.scatter(
            cx, cy, color=colormap(v_id), s=100, 
            edgecolors='black', label=f'Vehicle {v_id + 1} Cluster', zorder=4
        )
        
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("X Coordinate Space", fontsize=11)
    plt.ylabel("Y Coordinate Space", fontsize=11)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(
        by_label.values(), by_label.keys(), 
        loc='upper right', bbox_to_anchor=(1.25, 1.0)
    )
    
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_qubo_matrix(Q: dict, title: str, filename: str):
    
    # Renders the raw QUBO dictionary as a 2D Heatmap. 
    # This provides visual proof of mathematical modeling capabilities.
    
    if not HAS_MATPLOTLIB or not Q:
        return
        
    # Determine the matrix dimensions
    max_idx = max(max(u, v) for u, v in Q.keys())
    size = max_idx + 1
    matrix = np.zeros((size, size))
    
    # Populate the symmetric matrix for visualization
    for (u, v), weight in Q.items():
        matrix[u, v] = weight
        matrix[v, u] = weight 
        
    plt.figure(figsize=(10, 8))
    plt.imshow(matrix, cmap='coolwarm', interpolation='nearest')
    plt.colorbar(label='Energy Penalty (+) / Reward (-) Weight')
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Binary Variable Index (Flattened Customer x Vehicle)", fontsize=11)
    plt.ylabel("Binary Variable Index", fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_qaoa_convergence(history: list, filename: str = "qaoa_convergence.png"):
    """Plots the optimization trajectory of the QAOA energy cost function."""
    if not HAS_MATPLOTLIB:
        return
        
    plt.figure(figsize=(9, 5))
    plt.plot(
        range(1, len(history) + 1), history, 
        marker='o', color='#8E44AD', linewidth=2, markersize=5
    )
    plt.title(
        "QAOA Variational Optimization Convergence", 
        fontsize=12, fontweight='bold', pad=10
    )
    plt.xlabel("Optimization Iteration Step", fontsize=10)
    plt.ylabel("Energy Expectation Value <H>", fontsize=10)
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_qaoa_probabilities(
    counts: dict, title: str, filename: str, top_k: int = 15
):
    
    # Generates a histogram of the most frequently measured quantum bitstrings.
    
    if not HAS_MATPLOTLIB or not counts:
        return
        
    plt.figure(figsize=(10, 6))
    
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    bitstrings = [x[0] for x in sorted_counts]
    frequencies = [x[1] for x in sorted_counts]
    
    plt.bar(bitstrings, frequencies, color='#2980B9', edgecolor='black')
    plt.xticks(rotation=45, ha='right', fontname='monospace')
    plt.title(title, fontsize=12, fontweight='bold')
    plt.ylabel("Measurement Frequency (Shots)", fontsize=10)
    plt.xlabel("Quantum Bitstring State", fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()


def plot_solver_metrics(
    maxcut_data: dict, vrptw_data: dict, filename: str = "solver_comparison.png"
):
    # Generates an analytical bar chart comparing the objective scores side-by-side.
    if not HAS_MATPLOTLIB:
        return
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Left subplot: Max-Cut (Higher is better) - Fixed syntax error on colors
    ax1.bar(
        list(maxcut_data.keys()), list(maxcut_data.values()), 
        color=['#3498DB', '#8E44AD', '#2ECC71'][:len(maxcut_data)], 
        edgecolor='black', width=0.5
    )
    ax1.set_title("Max-Cut Performance (Higher Cut = Better)", fontsize=11, fontweight='bold')
    ax1.set_ylabel("Total Cut Weight Value", fontsize=10)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Right subplot: VRPTW Distance (Lower is better)
    ax2.bar(
        list(vrptw_data.keys()), list(vrptw_data.values()), 
        color=['#E74C3C', '#E67E22', '#F1C40F'][:len(vrptw_data)], 
        edgecolor='black', width=0.4
    )
    ax2.set_title("VRPTW Fleet Tracking (Lower Distance = Better)", fontsize=11, fontweight='bold')
    ax2.set_ylabel("Aggregated Routed Distance", fontsize=10)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    
    plt.suptitle(
        "QAIG Optimization Suite Performance Analytics Baseline", 
        fontsize=13, fontweight='bold', y=0.98
    )
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_DIR, filename), dpi=300)
    plt.close()
