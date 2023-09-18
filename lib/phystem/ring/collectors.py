import numpy as np
import os, yaml

from phystem.ring.solvers import CppSolver
from phystem.core import collectors

class State(collectors.State):
    def generate_data_vars(self) -> None:
        self.solver: CppSolver

        self.data_vars = {
            "pos":  np.zeros((self.num_points, self.solver.n, 2), dtype=np.float64),
            "vel":  np.zeros((self.num_points, self.solver.n, 2), dtype=np.float64),
            "self_prop_vel":  np.zeros((self.num_points, self.solver.n, 2), dtype=np.float64),
            "self_prop_angle":  np.zeros((self.num_points, self.solver.n), dtype=np.float64),
            "sum_forces":  np.zeros((self.num_points, self.solver.n, 2), dtype=np.float64),
            "graph_points":  np.zeros((self.num_points, 3*self.solver.n, 2), dtype=np.float64),
            "time": np.zeros(self.num_points, dtype=np.float64),
        }
    
    def collect_vars(self) -> None:
        self.data_vars["pos"][self.data_count] = self.solver.pos
        self.data_vars["vel"][self.data_count] = self.solver.vel
        self.data_vars["self_prop_vel"][self.data_count] = self.solver.self_prop_vel
        self.data_vars["self_prop_angle"][self.data_count] = self.solver.self_prop_angle
        self.data_vars["sum_forces"][self.data_count] = self.solver.total_forces
        self.data_vars["graph_points"][self.data_count] = self.solver.graph_points
        self.data_vars["time"][self.data_count] = self.solver.time
