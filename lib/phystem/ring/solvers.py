import numpy as np

from phystem.core.run_config import ReplayDataCfg   
from phystem.ring.configs import RingCfg
from phystem import cpp_lib

class CppSolver:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, self_prop_angle: np.ndarray, 
        dynamic_cfg: RingCfg, size: float, dt: float, rng_seed=None) -> None:
        if rng_seed is None:
            rng_seed = -1

        dynamic_cfg = cpp_lib.configs.RingCfg(dynamic_cfg.cpp_constructor_args())
        
        pos = cpp_lib.data_types.PosVec(pos.T)
        vel = cpp_lib.data_types.PosVec(vel.T)
        self_prop_angle = cpp_lib.data_types.List(self_prop_angle)

        self.cpp_solver = cpp_lib.solvers.Ring(pos, vel, self_prop_angle, dynamic_cfg, size, dt, rng_seed)
        self.update_func = self.cpp_solver.update_normal

        self.time = 0
        self.dt = dt
        self.n = len(self_prop_angle)

    @property
    def pos_t(self):
        return self.cpp_solver.pos_t
    
    @property
    def pos(self):
        return self.cpp_solver.pos
    
    @property
    def graph_points(self):
        return self.cpp_solver.graph_points
    
    @property
    def vel(self):
        return self.cpp_solver.vel
    
    @property
    def self_prop_vel(self):
        return self.cpp_solver.self_prop_vel
    
    @property
    def self_prop_angle(self):
        return self.cpp_solver.self_prop_angle
    
    @property
    def pos_continuos(self):
        return self.cpp_solver.pos_continuos
    
    @property
    def total_forces(self):
        return self.cpp_solver.total_forces
    
    @property
    def count_zero_speed(self):
        return self.cpp_solver.count_zero_speed
    
    @property
    def count_overlap(self):
        return self.cpp_solver.count_overlap
   
    @property
    def spring_forces(self):
        return self.cpp_solver.spring_forces
    
    @property
    def vol_forces(self):
        return self.cpp_solver.vol_forces

    @property
    def area_forces(self):
        return self.cpp_solver.area_forces
    
    @property
    def total_forces(self):
        return self.cpp_solver.total_forces
    
    def update(self):
        self.update_func()
        self.time += self.dt
    
    def mean_vel_vec(self):
        return self.cpp_solver.mean_vel_vec()

    def mean_vel(self):
        return self.cpp_solver.mean_vel()

class SolverRD:
    '''
    Solver utilizado no modo replay. Apenas itera sobre os dados salvos.  
    '''
    def __init__(self, run_cfg: ReplayDataCfg) -> None:
        import os
        
        self.pos_all = np.load(os.path.join(run_cfg.directory, "pos.npy"))
        self.graph_points_all = np.load(os.path.join(run_cfg.directory, "graph_points.npy"))
        self.vel_all = np.load(os.path.join(run_cfg.directory, "vel.npy"))
        self.time_arr = np.load(os.path.join(run_cfg.directory, "time.npy"))

        self.graph_points = self.graph_points_all[0]
        self.pos = self.pos_all[0]
        self.pos_t = self.pos.T
        self.vel = self.vel_all[0]
        
        self.num_particles = self.pos_all.shape[1]
        self.id = 0
        self.dt = run_cfg.dt
        
        self.run_cfg = run_cfg
        self.count = 0

        self.count_zero_speed = -1
        self.count_overlap = -1
        self.spring_forces = np.zeros((self.num_particles, 2))
        self.vol_forces = np.zeros((self.num_particles, 2))
        self.total_forces = np.zeros((self.num_particles, 2))
    
    @property
    def time(self):
        return self.time_arr[self.id]    

    def mean_vel(self):
        return -1

    def update(self):
        self.count += 1
        if self.count > self.run_cfg.frequency:
            self.count = 0
            self.id += 1

            self.graph_points[:] = self.graph_points_all[self.id]
            self.pos[:] = self.pos_all[self.id]
            self.pos_t = self.pos.T
            self.vel[:] = self.vel_all[self.id]
            
