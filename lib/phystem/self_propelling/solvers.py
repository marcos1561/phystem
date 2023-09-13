import numpy as np
from math import atan2

from phystem.core.run_config import UpdateType, ReplayDataCfg
from phystem.self_propelling.configs import SelfPropellingCfg
import phystem.cpp_lib as cpp_lib

class CppSolver:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, self_prop_cfg: SelfPropellingCfg, 
        size: float, dt: float, num_windows: int, update_type: UpdateType, rng_seed=None) -> None:
        if rng_seed is None:
            rng_seed = -1

        self_prop_cfg = cpp_lib.configs.SelfPropellingCfg(self_prop_cfg.cpp_constructor_args())
        
        pos = cpp_lib.data_types.PosVec(pos.T)
        vel = cpp_lib.data_types.PosVec(vel.T)

        self.cpp_solver = cpp_lib.solvers.SelfPropelling(pos, vel, self_prop_cfg, size, dt, num_windows, rng_seed)
        update_func = {
            UpdateType.NORMAL: self.cpp_solver.update_normal,
            UpdateType.WINDOWS: self.cpp_solver.update_windows,
        }
        self.update_func = update_func[update_type]

        self.time = 0
        self.dt = dt

    @property
    def n(self):
        return self.cpp_solver.n

    @property
    def sum_forces_matrix_debug(self):
        return self.cpp_solver.sum_forces_matrix_debug
    
    @property
    def py_pos(self):
        return self.cpp_solver.py_pos
    
    @property
    def py_vel(self):
        return self.cpp_solver.py_vel
    
    @property
    def pos(self):
        return self.cpp_solver.pos
    
    @property
    def vel(self):
        return self.cpp_solver.vel
    
    @property
    def propelling_vel(self):
        return self.cpp_solver.py_propelling_vel
    
    @property
    def propelling_angle(self):
        return self.cpp_solver.propelling_angle
    
    @property
    def random_number(self):
        return self.cpp_solver.random_number

    def mean_vel_vec(self):
        return self.cpp_solver.mean_vel_vec()

    def update(self):
        self.update_func()
        self.time += self.dt

    def mean_vel(self):
        return self.cpp_solver.mean_vel()

class SolverRD:
    '''
    Solver utilizado no modo replay. Apenas itera sobre os dados salvos.  
    '''
    def __init__(self, run_cfg: ReplayDataCfg) -> None:
        import os
        
        self.pos_all = np.load(os.path.join(run_cfg.directory, "pos.npy"))
        self.vel_all = np.load(os.path.join(run_cfg.directory, "vel.npy"))
        self.time_arr = np.load(os.path.join(run_cfg.directory, "time.npy"))

        self.py_pos = self.pos_all[0]
        self.py_vel = self.vel_all[0]
        
        self.pos = self.py_pos.T
        self.vel = self.py_vel.T
        
        self.num_particles = self.pos_all.shape[2]
        self.id = 0
        self.dt = run_cfg.dt
        
        self.run_cfg = run_cfg
        self.count = 0
    

    @property
    def time(self):
        return self.time_arr[self.id]    

    def mean_vel(self):
        id = self.id
        speeds = np.sqrt(self.vel_all[id][0]**2 + self.vel_all[id][1]**2)
        speeds[speeds < 1e-6] = 1e-6
        m_vel = (self.vel_all[id] / speeds).sum(axis=1) / self.num_particles
        return (m_vel[0]**2 + m_vel[1]**2)**.5

    def mean_vel_vec(self):
        return [0, 1]

    def update(self):
        self.count += 1
        if self.count > self.run_cfg.frequency:
            self.count = 0
            self.id += 1

            self.py_pos[:] = self.pos_all[self.id]
            self.py_vel[:] = self.vel_all[self.id]
            
