import numpy as np
import os, pickle

from phystem.systems.ring.solvers import CppSolver
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
    
class StateCheckpoint(collectors.Collector):
    def __init__(self, solver: CppSolver, path: str, configs: list, num_checkpoints: int, tf: float, to: float = 0) -> None:
        super().__init__(solver, path, configs)
        self.solver: CppSolver

        freq = int(((tf-to)/solver.dt)/num_checkpoints)
        if freq == 0:
            freq = 1
        self.freq = freq
        print("save freq:", self.freq)
        
        self.num_saves = 0

        num_rings = self.solver.num_max_rings
        num_particles = self.solver.num_particles

        self.pos = np.zeros((num_rings, num_particles, 2), dtype=np.float64),
        self.vel = np.zeros((num_rings, num_particles, 2), dtype=np.float64),
        self.angle = np.zeros((num_rings, num_particles), dtype=np.float64),
        self.metadata = {
            "num_time_steps": 0,
            "time": 0,
        }

        self.file_path = self.get_files_path(self.path)
        self.save()
    
    @staticmethod
    def get_files_path(path):
        return [
            os.path.join(path, "pos.npy"),
            os.path.join(path, "angle.npy"),
            os.path.join(path, "check_point_metadata.pickle"),
        ]

    def collect(self, count: int) -> None:
        if count % self.freq == 0:
            self.pos = np.array(self.solver.pos)
            self.angle = np.array(self.solver.self_prop_angle)
            self.metadata["num_time_steps"] = self.solver.num_time_steps
            self.metadata["time"] = self.solver.time
            
            # print(f"Saving | t = {self.solver.time} | count = {count} | count/f = {count/self.freq}")
            self.num_saves += 1

            np.save(self.file_path[0], self.pos)
            np.save(self.file_path[1], self.angle)
            
            with open(self.file_path[2], "wb") as f:
                pickle.dump(self.metadata, f)                

    @staticmethod
    def load(path: str):
        from phystem.systems.ring.creators import InitData

        files_path = StateCheckpoint.get_files_path(path)
        pos = np.load(files_path[0]) 
        angle = np.load(files_path[1])
        
        metadata = None
        if os.path.exists(files_path[2]):
            with open(files_path[2], "rb") as f:
                metadata = pickle.load(f)

        init_data = InitData(pos, angle)
        return init_data, metadata

class LastState(collectors.Collector):
    '''
    Coleta a posição no final da simulação. Para tal, apenas é necessário
    rodar a simulação e chamar o método 'save' após sua finalização.
    '''
    solver: CppSolver

    def __init__(self, solver: CppSolver, path: str, configs: list) -> None:
        super().__init__(solver, path, configs)

    def collect(self, count: int) -> None:
        pass

    def save(self) -> None:
        super().save()
        pos_path = os.path.join(self.path, "pos.npy")
        angle_path = os.path.join(self.path, "angle.npy")
        np.save(pos_path, np.array(self.solver.pos)[self.solver.rings_ids])
        np.save(angle_path, np.array(self.solver.self_prop_angle)[self.solver.rings_ids])
