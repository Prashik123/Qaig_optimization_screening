# Classical Constraint solver utilizing Google OR-Tools.
# Establishes the ground-truth routing benchmark.

from typing import List, Tuple, Optional
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
import numpy as np
from .dataset import Customer  # Fixed: Added missing space after dot

def solve_vrptw_exact(
    dist_matrix: np.ndarray, 
    customers: List[Customer], 
    num_vehicles: int, 
    vehicle_capacity: int
) -> Tuple[Optional[List[List[int]]], float]:
    
   # Executes the exact constraint solver utilizing OR-Tools AddDimension logic.
    
    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    # Callback 1: Distance Mapping
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(dist_matrix[from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Callback 2: Capacity Dimension
    demands = [0] + [c.demand for c in customers] 
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return demands[from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimension(
        demand_callback_index,
        slack_max=0,
        capacity=vehicle_capacity,
        fix_start_cumul_to_zero=True,
        name="Capacity"
    )

    # Callback 3: Time Windows Dimension
    service_times = [0] + [c.service_time for c in customers]
    time_windows = [(0, 9999)] + [(c.tw_start, c.tw_end) for c in customers]

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # Total time includes physical transit PLUS service duration at the origin
        return int(dist_matrix[from_node][to_node] + service_times[from_node])

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        slack_max=3000,  # Vehicles can wait at locations
        capacity=9999,
        fix_start_cumul_to_zero=False,
        name="Time"
    )
    
    time_dimension = routing.GetDimensionOrDie("Time")
    for location_idx, tw in enumerate(time_windows):
        if location_idx == 0:
            continue
        index = manager.NodeToIndex(location_idx)
        # Fixed: Converted to proper OR-Tools scalar assignment syntax parameters
        time_dimension.CumulVar(index).SetRange(tw[0], tw[1])

    # Optimizer Configurations
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.time_limit.seconds = 30

    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        return None, 0.0

    # Route Extraction Logic
    routes = []  
    total_distance = 0.0
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        route = [] 
        route_dist = 0.0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_dist += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        route.append(manager.IndexToNode(index))
        routes.append(route)
        total_distance += route_dist

    return routes, total_distance
