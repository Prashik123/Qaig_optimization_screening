# Classical baseline implementations for Max-Cut to provide approximation ratios.

from typing import Tuple
import networkx as nx
import numpy as np

def greedy_max_cut(graph: nx.Graph, seed: int = 42) -> Tuple[np.ndarray, float]:
    
    # A randomized greedy heuristic solver for Max-Cut problems. 
    # Nodes are sequentially shifted between partitions if the shift results 
    # in a strictly positive improvement to the final cut value.
    
    nodes = list(graph.nodes())
    n_nodes = len(nodes)
    
    np.random.seed(seed)
    partitions = np.random.randint(0, 2, size=n_nodes)
    
    improvement_found = True
    while improvement_found:
        improvement_found = False
        for i in range(n_nodes):
            current_node = nodes[i]
            current_assignment = partitions[i]
            
            cost_if_stay = 0.0
            cost_if_flip = 0.0
            
            for neighbor in graph.neighbors(current_node):
                neighbor_idx = nodes.index(neighbor)
                edge_weight = graph[current_node][neighbor].get('weight', 1.0)
                
                if partitions[neighbor_idx] != current_assignment:
                    cost_if_stay += edge_weight
                else:
                    cost_if_flip += edge_weight
                    
            if cost_if_flip > cost_if_stay:
                partitions[i] = 1 - current_assignment
                improvement_found = True
                
    # Evaluate final objective value
    final_cut_value = 0.0
    for u, v, data in graph.edges(data=True):
        if partitions[nodes.index(u)] != partitions[nodes.index(v)]:
            final_cut_value += data.get('weight', 1.0)
            
    return partitions, final_cut_value
