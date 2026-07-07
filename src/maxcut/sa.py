# Simulated Annealing solver using the dwave-neal library.
# Specifically architected to handle utility-scale QUBO matrices (e.g.: full GSET graphs).

from typing import Tuple
import networkx as nx
import numpy as np
from neal import SimulatedAnnealingSampler
from .formulations import build_qubo_dictionary 

def sa_max_cut(graph: nx.Graph, num_reads: int = 1000, sweeps: int = 1000) -> Tuple[np.ndarray, float]:
    
    # Executes simulated annealing against the generated QUBO model.
    
    Q = build_qubo_dictionary(graph)
    sampler = SimulatedAnnealingSampler()
    
    # Execute the probabilistic heuristic across multiple reads
    sampleset = sampler.sample_qubo(
        Q, 
        num_reads=num_reads,
        num_sweeps=sweeps
    )
    
    # Retrieve the state possessing the lowest thermal energy
    optimal_sample = sampleset.first.sample
    
    nodes = list(graph.nodes())
    partitions = np.zeros(len(nodes), dtype=int)
    for idx, node in enumerate(nodes):
        partitions[idx] = optimal_sample.get(node, 0)
        
    cut_value = 0.0
    for u, v, data in graph.edges(data=True):
        if partitions[nodes.index(u)] != partitions[nodes.index(v)]: 
            cut_value += data.get('weight', 1.0)
            
    return partitions, cut_value
