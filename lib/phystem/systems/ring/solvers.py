import numpy as np

from phystem.core.run_config import ReplayDataCfg, UpdateType
from phystem.systems.ring.configs import RingCfg, SpaceCfg
from phystem.systems.ring.run_config import IntegrationCfg
from phystem import cpp_lib

class CppSolver:
    def __init__(self, pos: np.ndarray, self_prop_angle: np.ndarray, 
        dynamic_cfg: RingCfg, space_cfg: SpaceCfg, int_cfg: IntegrationCfg, rng_seed=None) -> None:
        if rng_seed is None:
            rng_seed = -1
        if int_cfg.num_col_windows is None:
            int_cfg.num_col_windows = 1

        dynamic_cfg = cpp_lib.configs.RingCfg(dynamic_cfg.cpp_constructor_args())
        
        in_pol_checker_cfg = cpp_lib.configs.InPolCheckerCfg(
            int_cfg.in_pol_checker.num_col_windows, int_cfg.in_pol_checker.update_freq,
            int_cfg.in_pol_checker.disable)

        pos_in = [cpp_lib.data_types.PosVec(ring_pos) for ring_pos in pos]
        angle_in = [cpp_lib.data_types.List(ring_angle) for ring_angle in self_prop_angle]

        pos = cpp_lib.data_types.Vector3d(pos_in)
        self_prop_angle = cpp_lib.data_types.List2d(angle_in)

        self.cpp_solver = cpp_lib.solvers.Ring(
            pos, self_prop_angle, 
            dynamic_cfg, 
            space_cfg.size, 
            int_cfg.dt, int_cfg.num_col_windows, 
            rng_seed, 
            int_cfg.windows_update_freq, 
            int_cfg.integration_type.value,
            in_pol_checker_cfg,
        )

        update_type_to_func = {
            UpdateType.NORMAL: self.cpp_solver.update_normal,
            UpdateType.WINDOWS: self.cpp_solver.update_windows,
        }
        self.update_func = update_type_to_func[int_cfg.update_type]

        self.time = 0
        self.dt = int_cfg.dt
        self.n = len(self_prop_angle)

    @property
    def num_rings(self):
        return self.cpp_solver.num_rings
    
    @property
    def num_particles(self):
        return self.cpp_solver.num_particles
    
    @property
    def num_time_steps(self):
        return self.cpp_solver.num_time_steps
    
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
    
    @property
    def differences(self):
        return self.cpp_solver.differences
    
    @property
    def center_mass(self):
        return self.cpp_solver.center_mass
    
    @property
    def in_pol_checker(self):
        return self.cpp_solver.in_pol_checker
    
    @property
    def spring_debug(self):
        return self.cpp_solver.spring_debug
    @property
    def excluded_vol_debug(self):
        return self.cpp_solver.excluded_vol_debug
    @property
    def area_debug(self):
        return self.cpp_solver.area_debug
    @property
    def update_debug(self):
        return self.cpp_solver.update_debug
    
    def update_visual_aids(self):
        self.cpp_solver.update_visual_aids()

    def update(self):
        self.update_func()
        self.time += self.dt
    
    def mean_vel_vec(self, ring_id: int):
        return self.cpp_solver.mean_vel_vec(ring_id)

    def mean_vel(self, ring_id: int):
        return self.cpp_solver.mean_vel(ring_id)

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

    def mean_vel(self, ring_id: int):
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
            
