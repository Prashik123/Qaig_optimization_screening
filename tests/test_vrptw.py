# Unit tests validating synthetic data constraints and VRPTW formulations.

import numpy as np
import pytest
from src.vrptw.dataset import generate_vrptw_dataset, calculate_distance_matrix, Customer
from src.vrptw.ortools_solver import solve_vrptw_exact
from src.vrptw.hybrid_solver import build_clustering_qubo

def test_distance_matrix_symmetry():
    
    # Distance matrix for Euclidean points must be perfectly symmetric and zero on diagonal.
    
    depot, customers = generate_vrptw_dataset(num_customers=5)
    matrix = calculate_distance_matrix(depot, customers)
    
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), 0)

def test_ortools_infeasible_time_window():
    
    # Tests the exact solver's failure state when presented with an impossible time window constraint.
    
    depot = Customer(id=0, x=0, y=0, demand=0, tw_start=0, tw_end=100, service_time=0)
    # Customer is too far (distance 500) to reach within time window (ends at 10)
    impos_cust = Customer(id=1, x=500, y=0, demand=10, tw_start=0, tw_end=10, service_time=5)
    
    matrix = calculate_distance_matrix(depot, [impos_cust])
    routes, total_dist = solve_vrptw_exact(matrix, [impos_cust], num_vehicles=1, vehicle_capacity=50)
    
    # The exact solver should return None for routes when mathematically infeasible
    assert routes is None
    assert total_dist == 0.0
    
def test_clustering_qubo_hard_constraint():
    
    #Validates that the spatial QUBO heavily penalizes assigning one customer to multiple vehicles.
    
    matrix = np.zeros((3, 3)) # 1 depot, 2 customers
    Q = build_clustering_qubo(matrix, num_customers=2, num_vehicles=2)
    
    # Check the penalty (alpha) for the linear and quadratic terms for customer 0
    # ALPHA = 100.0. Linear term is -ALPHA. Quadratic is 2*ALPHA.
    idx_v0 = 0 * 2 + 0 # customer 0, vehicle 0
    idx_v1 = 0 * 2 + 1 # customer 0, vehicle 1
    
    assert Q[(idx_v0, idx_v0)] == -100.0
    assert Q[(idx_v0, idx_v1)] == 200.0
