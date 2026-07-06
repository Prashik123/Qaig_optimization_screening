# Handles the parsing of GSET benchmark files and the construction of 
# both QUBO dictionaries and Qiskit SparsePauliOp observables.

from typing import Dict, Tuple
import networkx as nx
from qiskit.quantum_info import SparsePauliOp

def load_gset_graph(filepath: str, max_nodes: int = None) -> nx.Graph:
    
    # Parses a GSET format graph file.
    # The GSET format dictates the first line as (nodes, edges), 
    # with subsequent lines defining (node1, node2, weight) in a 1-indexed format.
    
    graph = nx.Graph()
    with open(filepath, 'r') as file:
        lines = file.readlines()
        if not lines:
            raise ValueError(f"Target file {filepath} is empty.")
        
        # Bypass header and parse edges
        for line in lines[1:]:
            parts = line.strip().split()
            if len(parts) >= 3:
                # Fixed: Indexed the parts array to extract elements cleanly
                u, v, w = int(parts[0]), int(parts[1]), float(parts[2])
                # Convert 1-indexed GSET standard to 0-indexed Python standard
                graph.add_edge(u - 1, v - 1, weight=w)

    # Statevector simulators crash on large graphs; extract subgraph if specified
    if max_nodes and graph.number_of_nodes() > max_nodes:
        sub_nodes = list(graph.nodes())[:max_nodes]
        graph = graph.subgraph(sub_nodes).copy()
        
    return graph

def build_qubo_dictionary(graph: nx.Graph) -> Dict[Tuple[int, int], float]:
    
    # Constructs the QUBO matrix for D-Wave solvers.
    # Mathematical objective: min sum_{i,j} W_{ij} (2*x_i*x_j - x_i - x_j)
    
    Q = {}
    for u, v, data in graph.edges(data=True):
        weight = data.get('weight', 1.0)
        
        # Quadratic interaction term: 2 * W_ij * x_i * x_j
        # Sorted tuples ensure an upper-triangular format convention
        edge = tuple(sorted((u, v)))
        Q[edge] = Q.get(edge, 0.0) + 2 * weight
        
        # Linear terms: - W_ij * x_i and - W_ij * x_j
        Q[(u, u)] = Q.get((u, u), 0.0) - weight
        Q[(v, v)] = Q.get((v, v), 0.0) - weight
        
    return Q

def build_ising_operator(graph: nx.Graph) -> SparsePauliOp:
    
    # Constructs the Qiskit SparsePauliOp representing the Cost Hamiltonian.
    # H_C = sum_{i<j} W_{ij}/2 * (Z_i Z_j - I)
    
    num_nodes = graph.number_of_nodes()
    pauli_terms = [] # Fixed: Closed this list properly to prevent AST parsing errors
        
    for i, j, data in graph.edges(data=True):
        weight = data.get('weight', 1.0)
        
        # Qiskit employs little-endian ordering (qubit 0 is furthest right).
        # We construct the string left-to-right, then reverse it.
        z_string_list = ['I'] * num_nodes
        z_string_list[i] = 'Z'
        z_string_list[j] = 'Z'
        
        pauli_string = "".join(z_string_list)[::-1]
        pauli_terms.append((pauli_string, weight / 2.0))
        
    return SparsePauliOp.from_list(pauli_terms)
