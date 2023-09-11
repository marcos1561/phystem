import numpy as np
import os, yaml

from physical_system.solver import CppSolver

class Collector:
    def __init__(self, path: str, configs: list) -> None:
        self.configs = configs
        self.path = path

    def save(self):
        config_path = os.path.join(self.path, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(self.configs, f)

class State(Collector):
    file_names = ("pos.npy", "vel.npy", "propelling_vel.npy", "propelling_angle.npy", 
        "sum_forces_matrix.npy" "rng.npy", "time.npy")

    def __init__(self, solver: CppSolver, path: str, configs: list, tf: float, dt: float, to=0.0, 
        num_points:int=None) -> None:
        super().__init__(path, configs)

        collect_all_steps = num_points is None

        if num_points is None:
            if tf is None or dt is None:
                raise ValueError("Como 'num_points = None', 'tf' e 'dt' devem ser passados.")
            num_points = int((tf-to)/dt)

        if not os.path.exists(path):
            raise ValueError("O caminho especificado não existe.")

        if collect_all_steps:
            freq = 1
        else:
            freq = int(((tf-to)/dt)/num_points)
            if freq == 0:
                freq = 1

        self.num_points = num_points
        self.dt = dt
        self.tf = tf
        self.freq = freq

        self.solver = solver

        self.pos = np.zeros((num_points, 2, solver.n), dtype=np.float64)
        self.vel = np.zeros((num_points, 2, solver.n), dtype=np.float64)
        self.sum_forces_matrix = np.zeros((num_points, solver.n, 2), dtype=np.float64)
        self.propelling_vel = np.zeros((num_points, 2, solver.n), dtype=np.float64)
        self.propelling_angle = np.zeros((num_points, solver.n), dtype=np.float64)
        self.time = np.zeros(num_points, dtype=np.float64)
        self.rng = np.zeros(num_points, dtype=np.float64)

        self.data_vars = {
            "pos" : self.pos,
            "vel" : self.vel,
            "propelling_vel" : self.propelling_vel,
            "propelling_angle" : self.propelling_angle,
            "sum_forces_matrix" : self.sum_forces_matrix,
            "rng" : self.rng,
            "time" : self.time,
        }

        self.data_count = 0

    def collect(self, count: int):
        if count % self.freq == 0 and self.data_count < self.num_points:
            self.pos[self.data_count] = self.solver.pos
            self.vel[self.data_count] = self.solver.vel
            self.sum_forces_matrix[self.data_count] = self.solver.sum_forces_matrix_debug
            self.propelling_vel[self.data_count] = self.solver.propelling_vel
            self.propelling_angle[self.data_count] = self.solver.propelling_angle
            self.time[self.data_count] = self.solver.time
            self.rng[self.data_count] = self.solver.random_number
            self.data_count += 1
    
    def save(self):
        super().save()
        for var_name, var_data in self.data_vars.items():
            np.save(os.path.join(self.path, var_name + ".npy"), var_data)


    @staticmethod
    def load(path: str):
        data_list = []
        for file_name in State.file_names:
            data_list.append(np.load(os.path.join(path, file_name)))
        return data_list
    
    @staticmethod
    def memory_needed(dt: float, tf: float, num_particles: int):
        '''
        Retorna a memória necessária em MB para todos os passos temporais até `tf`
        com 'num_particles' partículas.
        '''
        num_points = tf/dt
        array_2d_size = num_points * 2 * num_particles
        array_1d_size = num_points * num_particles

        return (4 * array_2d_size + array_1d_size + num_points * 2) / 1e6

class MeanVel:
    def __init__(self, solver: CppSolver, tf: float, dt: float, num_points: int, path: str) -> None:
        freq = int((tf/dt)/num_points)
        if freq == 0:
            freq = 1
        self.freq = freq

        self.solver = solver
        self.data = np.zeros((2, num_points), dtype=np.float64)
        self.data_count = 0
        self.has_space = True

        self.num_points = num_points

        self.path = path

    def collect(self, count: int):
        if count % self.freq == 0 and self.has_space:
            self.data[0, self.data_count] = self.solver.mean_vel()
            self.data[1, self.data_count] = self.solver.time
            self.data_count += 1
            
            if self.data_count >= self.num_points:
                self.has_space = False

    def save(self):
        np.save(self.path, self.data)

if __name__ == "__main__":
    print(State.memory_needed(1, 1000, 1000))
