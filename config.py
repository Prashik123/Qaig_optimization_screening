# config.py

#Central configuration module for the QAIG optimization suite.
#Isolating configurations ensures environments remain reproducible and prevents
#magic numbers from cluttering the algorithmic logic.

import os
from pathlib import Path

# Repository Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global Determinism
RANDOM_SEED = 42

# VQA / QAOA Hyperparameters
QAOA_P_LAYERS = 2
QAOA_MAXITER = 50

# Simulated Annealing Hyperparameters
SA_NUM_READS = 1000
SA_SWEEPS = 1000

# Synthetic VRPTW Generation Parameters
VRPTW_NUM_CUSTOMERS = 10
VRPTW_NUM_VEHICLES = 6
VRPTW_VEHICLE_CAPACITY = 200
VRPTW_GRID_SIZE = 100
