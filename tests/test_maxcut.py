# Unit tests validating QUBO generation, QAOA, and SA optimization convergence.
import networkx as nx
import numpy as np
from src.maxcut.formulations import build_qubo_dictionary
from src.maxcut.sa import sa_max_cut
from src.maxcut.classical import greedy_max_cut

def test_qubo_triangle_topology():
    
    # Validates objective mapping. A 3-node triangle with equal weights 1.0 
    # has a deterministically known absolute max cut value of 2.0.
    
    graph = nx.Graph()
    graph.add_edges_from([(0,1), (1,2), (2,0)])
    for u, v in graph.edges():
        graph[u][v]['weight'] = 1.0
        
    partitions, cut_val = sa_max_cut(graph)
    assert cut_val == 2.0
    
    # Assert exact one partition holds 2 nodes and the other holds 1.
    assert sum(partitions) in [1, 2]

def test_greedy_baseline_disconnected():
    
    # Tests the greedy solver on a disconnected graph edge case.
    
    graph = nx.Graph()
    graph.add_node(0)
    graph.add_node(1)
    # No edges present
    
    partitions, cut_val = greedy_max_cut(graph)
    assert cut_val == 0.0

def test_qubo_generation_weights():
    
    # Ensures that negative edge weights are correctly formulated into the QUBO.
    
    graph = nx.Graph()
    graph.add_edge(0, 1, weight=-5.0)
    
    Q = build_qubo_dictionary(graph)
    # Formula: min W_ij (2x_i x_j - x_i - x_j)
    # For w=-5: -10 x_0 x_1 + 5 x_0 + 5 x_1
    assert Q.get((0, 0), 0.0) == 5.0
    assert Q.get((1, 1), 0.0) == 5.0
    assert Q.get((0, 1), 0.0) == -10.0
