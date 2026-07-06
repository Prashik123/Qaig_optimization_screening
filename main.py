# Primary pipeline orchestration script. Integrates models, solvers, and reporting logic.

import os
import sys

# Injecting local path workspace rules for internal module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import warnings
from scipy.sparse import SparseEfficiencyWarning
warnings.simplefilter("ignore", category=SparseEfficiencyWarning)

import networkx as nx
from src.maxcut.classical import greedy_max_cut
from src.maxcut.qaoa import QAOASolver
from src.maxcut.sa import sa_max_cut
from src.vrptw.dataset import generate_vrptw_dataset, calculate_distance_matrix
from src.vrptw.ortools_solver import solve_vrptw_exact
from src.vrptw.hybrid_solver import solve_hybrid_vrptw

# Import all visualization tools
from src.utils.visualization import (
    plot_maxcut_partition, 
    plot_vrptw_routes, 
    plot_qaoa_convergence,
    plot_qaoa_probabilities,
    plot_vrptw_clusters,
    plot_solver_metrics
)
import config

# Import pyplot directly to handle interactive pop-up window generation
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt

def execute_maxcut_pipeline():
    print("Initiating Problem 1: Max-Cut Benchmark: ")
    
    graph = nx.erdos_renyi_graph(8, 0.5, seed=config.RANDOM_SEED)
    for u, v in graph.edges():
        graph[u][v]['weight'] = 1.0

    print("[1/3] Executing Classical Greedy Heuristic: ")
    part_c, cut_c = greedy_max_cut(graph)
    
    print("[2/3] Executing D-Wave Simulated Annealing (QUBO): ")
    part_sa, cut_sa = sa_max_cut(graph)
    
    print("[3/3] Executing Qiskit QAOA (Ising Hamiltonian): ")
    qaoa = QAOASolver(graph, p_layers=config.QAOA_P_LAYERS)
    part_q, cut_q = qaoa.solve()
    
    print(f"Results Summary -> Classical: {cut_c} | SA: {cut_sa} | QAOA: {cut_q}")
    
    # SAVE & SHOW GRAPH PARTITIONS 
    plot_maxcut_partition(graph, part_sa, "Simulated Annealing: Optimal Partition", "maxcut_sa_output.png")
    
    # UPDATED: Trigger Comprehensive QAOA Visualizations
    if hasattr(qaoa, 'cost_history') and qaoa.cost_history:
        plot_qaoa_convergence(qaoa.cost_history, "maxcut_qaoa_convergence.png")
    if hasattr(qaoa, 'counts') and qaoa.counts:
        plot_qaoa_probabilities(qaoa.counts, "QAOA Measurement Distribution", "maxcut_qaoa_probs.png")

    # SAVE QAOA QUANTUM CIRCUIT DIAGRAM 
    try:
        # Dynamically locate the underlying Qiskit circuit object inside your solver class
        circuit_obj = getattr(qaoa, 'circuit', getattr(qaoa, 'ansatz', None))
        if circuit_obj:
            circuit_path = os.path.join(config.OUTPUT_DIR, "qaoa_quantum_circuit.png")
            
            # Decompose the high-level QAOA wrapper into its ansatz components
            decomposed_circuit = circuit_obj.decompose()
            
            # Decompose a second time to unroll the ansatz into individual H, CNOT, and Rz gates
            fully_decomposed = decomposed_circuit.decompose()
            
            # Generate high-resolution gate-level circuit drawing layout
            fully_decomposed.draw(output='mpl', filename=circuit_path, scale=0.7)
            print(f" Fully decomposed gate-level Quantum Circuit saved to {circuit_path}")
        else:
            print("[Notice] Could not automatically locate the Qiskit circuit object inside QAOASolver.")
    except Exception as e:
        print(f"[Notice] Skipping circuit print layout calculation: {e}")

    # Force VS Code to render the active figures onto your user display
    plt.show()
    
    # UPDATED: Return metrics dictionary for side-by-side comparison
    return {"Greedy": cut_c, "SA (QUBO)": cut_sa, "QAOA": cut_q}


def execute_vrptw_pipeline():
    print("\n Initiating Problem 2: VRPTW Benchmark: ")
    
    depot, customers = generate_vrptw_dataset(config.VRPTW_NUM_CUSTOMERS)
    dist_matrix = calculate_distance_matrix(depot, customers)
    
    print("[1/2] Executing Classical OR-Tools Exact Solver: ")
    routes_exact, dist_exact = solve_vrptw_exact(
        dist_matrix, customers, config.VRPTW_NUM_VEHICLES, config.VRPTW_VEHICLE_CAPACITY
    )
    
    print("[2/2] Executing Hybrid Quantum-Classical Clustering Algorithm: ")
    # UPDATED: Unpack the third return value (clusters) from the hybrid solver
    routes_hyb, dist_hyb, clusters_hyb = solve_hybrid_vrptw(
        dist_matrix, depot, customers, config.VRPTW_NUM_VEHICLES, config.VRPTW_VEHICLE_CAPACITY
    )
    
    print(f"Total Aggregated Distance -> Exact Solver: {dist_exact:.2f} | Hybrid Model: {dist_hyb:.2f}")
    
    # UPDATED: SAVE ROUTING MAPS & CLUSTERS
    if clusters_hyb:
        plot_vrptw_clusters(depot, clusters_hyb, "Phase 1: Quantum QUBO Spatial Clustering", "vrptw_phase1_clusters.png")
    if routes_exact:
        plot_vrptw_routes(depot, customers, routes_exact, "OR-Tools Standard Routing", "vrptw_exact_output.png")
    if routes_hyb:
        plot_vrptw_routes(depot, customers, routes_hyb, "Phase 2: Hybrid Quantum-Inspired Routing", "vrptw_hybrid_output.png")
        
    # Force the navigation graphs onto the display
    plt.show()
    
    # UPDATED: Return metrics dictionary for side-by-side comparison
    return {"Exact (OR-Tools)": dist_exact, "Hybrid Q-C": dist_hyb}

if __name__ == "__main__":
    maxcut_metrics = execute_maxcut_pipeline()
    vrptw_metrics = execute_vrptw_pipeline()
    
    # UPDATED: Generate the aggregate side-by-side solver comparison chart
    plot_solver_metrics(maxcut_metrics, vrptw_metrics, "final_solver_comparisons.png")
    
    # Display the final performance metrics chart
    plt.show()