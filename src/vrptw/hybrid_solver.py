# Hybrid Quantum-Inspired Clustering + Classical Routing Pipeline.
# Phase 1: Formulates customer grouping as a QUBO, minimizing spatial spread.
# Phase 2: Evaluates exact TSP pathways (with Time Windows) classically per cluster.

import numpy as np
from typing import List, Tuple, Dict, Any
from dwave.samplers import SimulatedAnnealingSampler
from .ortools_solver import solve_vrptw_exact
from .dataset import Customer

def build_clustering_qubo(dist_matrix: np.ndarray, num_customers: int, num_vehicles: int) -> Dict[Tuple[int, int], float]:
    # Constructs a QUBO to assign customers to distinct vehicle clusters.

    # Args:
        # dist_matrix: Fully computed global distance matrix.
        # num_customers: Total number of customer nodes.
        # num_vehicles: Size of available fleet.

    # Returns:
         # A dictionary mapping binary quadratic and linear variables to penalty weights.
    Q: Dict[Tuple[int, int], float] = {}
    
    # Helper to flatten 2D logic (customer, vehicle) into 1D binary variable space
    def var_idx(c: int, v: int) -> int: 
        return c * num_vehicles + v
    
    ALPHA: float = 2500.0  # Dominant penalty for violating the strict one cluster per customer rule
    BETA: float = 1.0     # Minor penalty to minimize intra-cluster geographical distance
    
    # 1. Spatial Proximity Optimization
    for i in range(num_customers):
        for j in range(i + 1, num_customers):
            # Matrix index offset by +1 to skip the depot (index 0)
            distance: float = float(dist_matrix[i + 1][j + 1])
            for v in range(num_vehicles):
                idx_u: int = var_idx(i, v)
                idx_v: int = var_idx(j, v)
                Q[(idx_u, idx_v)] = Q.get((idx_u, idx_v), 0.0) + BETA * distance

    # 2. Strict Partition Constraint: sum(y_{iv}) == 1 for all customers
    # Expanding ALPHA * (y_{i0} + y_{i1} +... - 1)^2
    for i in range(num_customers):
        for v1 in range(num_vehicles):
            idx1: int = var_idx(i, v1)
            # Linear component from the binary expansion (-2x + x^2 = -x)
            Q[(idx1, idx1)] = Q.get((idx1, idx1), 0.0) - ALPHA
            # Quadratic cross-terms
            for v2 in range(v1 + 1, num_vehicles):
                idx2: int = var_idx(i, v2)
                Q[(idx1, idx2)] = Q.get((idx1, idx2), 0.0) + 2 * ALPHA
                
    return Q

def solve_hybrid_vrptw(
    dist_matrix: np.ndarray, 
    depot: Customer, 
    customers: List[Customer], 
    num_vehicles: int, 
    vehicle_capacity: int
) -> Tuple[List[List[int]], float, Dict[int, List[Customer]]]:
    #Orchestrates the two-phase hybrid heuristic execution.

    #Returns: 
       # A tuple containing (Routes, Total Distance, Decoded Clusters)
    
    # Phase 1: Quantum-inspired Clustering via modern D-Wave SA
    Q: Dict[Tuple[int, int], float] = build_clustering_qubo(dist_matrix, len(customers), num_vehicles)
    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample_qubo(Q, num_reads=3000, num_sweeps=3000)
    best_sample: Dict[int, int] = sampleset.first.sample
    
    clusters: Dict[int, List[Customer]] = {v: [] for v in range(num_vehicles)}
    for i, customer in enumerate(customers):
        for v in range(num_vehicles):
            if best_sample.get(i * num_vehicles + v, 0) == 1:
                clusters[v].append(customer)
                break
                
    # Phase 2: Classical TSP Evaluation per Cluster
    global_routes: List[List[int]] = []
    total_distance: float = 0.0
    
    for v, cluster_members in clusters.items():
        if not cluster_members:
            continue
            
        # Reconstruct localized distance matrix for OR-Tools compatibility
        sub_nodes: List[Customer] = [depot] + cluster_members
        sub_dist_matrix: np.ndarray = np.zeros((len(sub_nodes), len(sub_nodes)))
        for x in range(len(sub_nodes)):
            for y in range(len(sub_nodes)):
                sub_dist_matrix[x][y] = dist_matrix[sub_nodes[x].id][sub_nodes[y].id]
                
        # Execute exact optimization constrained to this specific geographic cluster
        routes, dist = solve_vrptw_exact(sub_dist_matrix, cluster_members, 1, vehicle_capacity)
        
        # Recursively unpack and unwrap nested multi-vehicle routes arrays
        if routes:
            if isinstance(routes, list) and len(routes) > 0 and isinstance(routes[0], list):
                for route in routes:
                    mapped_route: List[int] = [sub_nodes[idx].id for idx in route]
                    global_routes.append(mapped_route)
            else:
                # Fallback support for single-dimensional route arrays
                mapped_route = [sub_nodes[idx].id for idx in routes]  # type: ignore
                global_routes.append(mapped_route)
                
            total_distance += dist
            
    # Fixed: Corrected missing signature return variable to resolve tuple mismatch
    return global_routes, total_distance, clusters
