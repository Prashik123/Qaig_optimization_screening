import numpy as np
import networkx as nx
from typing import Tuple, List, Dict, Any
from qiskit.circuit.library import QAOAAnsatz
from qiskit.primitives import StatevectorEstimator, StatevectorSampler
from scipy.optimize import minimize
from .formulations import build_ising_operator

class QAOASolver:
    # Encapsulates the QAOA pipeline: ansatz generation, cost evaluation,

    # classical optimization, and optimal bitstring sampling using updated V2 Primitives.

    def __init__(self, graph: nx.Graph, p_layers: int = 2, maxiter: int = 50):
        self.graph: nx.Graph = graph
        self.operator = build_ising_operator(graph)
        self.ansatz: QAOAAnsatz = QAOAAnsatz(self.operator, reps=p_layers)
        self.maxiter: int = maxiter
        
        # Qiskit 1.x native V2 primitives for exact local simulation
        self.estimator: StatevectorEstimator = StatevectorEstimator()
        self.sampler: StatevectorSampler = StatevectorSampler()
        
        self.cost_history: List[float] = []
        self.energy_history: List[float] = []  # Explicit alias added to sync with main.py convergence tracking
        self.counts: Dict[str, int] = {}

    def _objective_function(self, params: np.ndarray) -> float:
        #Calculates the expectation value of the Ising Hamiltonian given current parameters.
        # Formulate a Primitive Unified Bloc (PUB) for the Estimator V2
        pub = (self.ansatz, [self.operator], [params])
        job = self.estimator.run([pub])
        result = job.result() 
        
        # Read the expectation value from the result object, handling both 1.x and 2.x API changes
        pub_result = result[0]
        expectation_value = pub_result.data.evs
        
        # Handle the 2.x API change for extracting the expectation value
        val: float = float(np.asarray(expectation_value).item())
        
        self.cost_history.append(val)
        self.energy_history.append(val)  # Sync value changes cleanly across execution modules
        return val

    def solve(self, seed: int = 42) -> Tuple[np.ndarray, float]:
        # Executes the closed-loop optimization between the classical optimizer and quantum estimator.
        np.random.seed(seed)
        initial_params: np.ndarray = np.random.uniform(0, np.pi, self.ansatz.num_parameters)
        
        # Reset tracker historical loops before calculation run begins
        self.cost_history = []
        self.energy_history = []
        
        opt_result = minimize(
            self._objective_function,
            x0=initial_params,
            method='COBYLA',
            options={'maxiter': self.maxiter}
        )
        
        # Parameterize the circuit with the optimized angles for final sampling
        bound_circuit = self.ansatz.assign_parameters(opt_result.x)
        bound_circuit.measure_all()
        
        # In V2, the Sampler expects a PUB containing purely the circuit (since it's already bound)
        pub = (bound_circuit,)
        job = self.sampler.run([pub], shots=1024)
        result = job.result()
        

        pub_result_sampler = result[0]
        
        # Support both new bitstring bit data envelopes (.get_counts() or via classical bit fields)
        if hasattr(pub_result_sampler.data, 'meas'):
            self.counts = pub_result_sampler.data.meas.get_counts()
        elif hasattr(pub_result_sampler.data, 'c'):
            self.counts = pub_result_sampler.data.c.get_counts()
        else:
            # Universal fallback catch for varying register string names
            data_keys = list(pub_result_sampler.data.keys())
            if data_keys:
                self.counts = getattr(pub_result_sampler.data, data_keys[0]).get_counts()
                
        best_bitstring: str = max(self.counts, key=lambda k: self.counts[k])
        
        # Reverse bitstring to counteract Qiskit's little-endian ordering
        best_bitstring = best_bitstring[::-1]
        partitions: np.ndarray = np.array([int(bit) for bit in best_bitstring])
        
        # Compute exact cut value based on the empirical graph structure
        cut_value: float = 0.0
        nodes: List[Any] = list(self.graph.nodes())
        for u, v, data in self.graph.edges(data=True):
            if partitions[nodes.index(u)] != partitions[nodes.index(v)]:
                cut_value += data.get('weight', 1.0)
                
        return partitions, cut_value
