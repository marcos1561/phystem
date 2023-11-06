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

class AreaCollector(collectors.Collector):
    def __init__(self, solver: CppSolver, path: str, configs: list, tf: float, dt: float, num_points: int) -> None:
        super().__init__(solver, path, configs)

        self.areas = []
        self.time = []

        self.freq = int((tf/dt) / num_points)
        if self.freq == 0:
            self.freq = 1

    def collect(self, count: int) -> None:
        if count % self.freq == 0:
            self.areas.append(list(self.solver.area_debug.area))
            self.time.append(self.solver.time)

    def save(self) -> None:
        super().save()
        path_area = os.path.join(self.path, "areas.npy")
        path_time = os.path.join(self.path, "time.npy")
        np.save(path_area, np.array(self.areas))
        np.save(path_time, np.array(self.time))
    
class LastPos(collectors.Collector):
    def __init__(self, solver: CppSolver, path: str, configs: list) -> None:
        super().__init__(solver, path, configs)

    def collect(self, count: int) -> None:
        pass

    def save(self) -> None:
        super().save()
        path_area = os.path.join(self.path, "pos.npy")
        np.save(path_area, np.array(self.solver.pos))
    
    

