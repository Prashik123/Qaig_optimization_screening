# Generates synthetic, deterministic geospatial datasets for logistics routing.

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

@dataclass
class Customer:
    id: int
    x: float
    y: float
    demand: int
    tw_start: int
    tw_end: int
    service_time: int

def generate_vrptw_dataset(num_customers: int, grid_size: int = 100, seed: int = 42) -> Tuple[Customer, List[Customer]]:
    
    # Instantiates a depot and a distributed list of customers with randomized parameters.
    
    np.random.seed(seed)
    
    # Uniform spacing around division operators
    depot = Customer(
        id=0, x=grid_size / 2, y=grid_size / 2, demand=0, 
        tw_start=0, tw_end=9999, service_time=0
    )
    
    customers = []  
    for i in range(1, num_customers + 1):
        x = np.random.uniform(0, grid_size)
        y = np.random.uniform(0, grid_size)
        demand = np.random.randint(5, 20)
        
        # Ensure logical time windows (start precedes end)
        base_time = np.random.randint(0, 200)
        tw_start = base_time
        tw_end = base_time + np.random.randint(50, 150)
        service_time = np.random.randint(10, 30)
        
        customers.append(Customer(i, x, y, demand, tw_start, tw_end, service_time))
        
    return depot, customers

def calculate_distance_matrix(depot: Customer, customers: List[Customer]) -> np.ndarray:
    
    #Computes the complete Euclidean distance matrix.
    
    nodes = [depot] + customers
    n_nodes = len(nodes)
    dist_matrix = np.zeros((n_nodes, n_nodes))
    
    for i in range(n_nodes):
        for j in range(n_nodes):
            dist_matrix[i][j] = np.sqrt(
                (nodes[i].x - nodes[j].x)**2 + (nodes[i].y - nodes[j].y)**2
            )
            
    return dist_matrix
