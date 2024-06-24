import numpy as np
import os, yaml

from phystem.core.run_config import ReplayDataCfg
from phystem.systems.ring.configs import RingCfg, SpaceCfg, StokesCfg
from phystem.systems.ring.run_config import IntegrationCfg, UpdateType, IntegrationType, ParticleWindows, InPolCheckerCfg
from phystem import cpp_lib

from .solver_config import *
from . import utils

class CppSolver:
    def __init__(self, pos: np.ndarray, self_prop_angle: np.ndarray, num_particles: int,
        dynamic_cfg: RingCfg, space_cfg: SpaceCfg, int_cfg: IntegrationCfg, stokes_cfg: StokesCfg=None, rng_seed=None) -> None:
        if stokes_cfg is None and int_cfg.update_type is UpdateType.STOKES:
            raise Exception("Informe a configuração do fluxo de stokes")
        
        if rng_seed is None:
            rng_seed = -1
        if int_cfg.particle_win_cfg is None:
            int_cfg.particle_win_cfg = ParticleWindows(3, 3, -1)
        if int_cfg.in_pol_checker is None:
            int_cfg.in_pol_checker = InPolCheckerCfg(3, 3, 1, True)

        dynamic_cfg = cpp_lib.configs.RingCfg(dynamic_cfg.cpp_constructor_args())
        
        if stokes_cfg is not None:
            stokes_cfg = cpp_lib.configs.StokesCfgPy(stokes_cfg.cpp_constructor_args())
        else:
            stokes_cfg = cpp_lib.configs.StokesCfgPy(StokesCfg.get_null_cpp_cfg())

        particle_win_cfg = cpp_lib.configs.ParticleWindowsCfg(
            int_cfg.particle_win_cfg.num_cols, int_cfg.particle_win_cfg.num_rows,
            int_cfg.particle_win_cfg.update_freq)
        
        in_pol_checker_cfg = cpp_lib.configs.InPolCheckerCfg(
            int_cfg.in_pol_checker.num_col_windows, int_cfg.in_pol_checker.num_rows_windows, 
            int_cfg.in_pol_checker.update_freq, int_cfg.in_pol_checker.disable)

        integration_type_to_cpp_type = {
            IntegrationType.euler: cpp_lib.configs.RingIntegrationType.euler, 
            IntegrationType.verlet: cpp_lib.configs.RingIntegrationType.verlet, 
            IntegrationType.rk4: cpp_lib.configs.RingIntegrationType.rk4, 
        }
        update_type_to_cpp_type = {
            UpdateType.PERIODIC_NORMAL: cpp_lib.configs.RingUpdateType.periodic_borders, 
            UpdateType.PERIODIC_WINDOWS: cpp_lib.configs.RingUpdateType.periodic_borders, 
            UpdateType.STOKES: cpp_lib.configs.RingUpdateType.stokes, 
            UpdateType.INVAGINATION: cpp_lib.configs.RingUpdateType.invagination, 
        }

        pos_in = [cpp_lib.data_types.PosVec(ring_pos) for ring_pos in pos]

        pos = cpp_lib.data_types.Vector3d(pos_in)
        self_prop_angle = cpp_lib.data_types.List(self_prop_angle)
        
        self.cpp_solver = cpp_lib.solvers.Ring(
            pos, self_prop_angle, 
            num_particles,
            dynamic_cfg, 
            space_cfg.height, 
            space_cfg.length, 
            int_cfg.dt, 
            particle_win_cfg,
            update_type_to_cpp_type[int_cfg.update_type],
            integration_type_to_cpp_type[int_cfg.integration_type],
            stokes_cfg,
            in_pol_checker_cfg,
            rng_seed, 
        )
        
        update_type_to_func = {
            UpdateType.PERIODIC_NORMAL: self.cpp_solver.update_normal,
            UpdateType.PERIODIC_WINDOWS: self.cpp_solver.update_windows,
            UpdateType.STOKES: self.cpp_solver.update_stokes,
            UpdateType.INVAGINATION: self.cpp_solver.update_windows,
        }
        
        self.update_func = update_type_to_func[int_cfg.update_type]

        self.dt = int_cfg.dt
        self.n = len(self_prop_angle)

    @property
    def num_max_rings(self):
        return self.cpp_solver.num_max_rings
    
    @property
    def num_particles(self):
        return self.cpp_solver.num_particles
    
    @property
    def time(self):
        return self.cpp_solver.sim_time
    
    @property
    def num_time_steps(self):
        return self.cpp_solver.num_time_steps
    
    @property
    def pos_t(self):
        return self.cpp_solver.pos_t
    
    @property
    def num_active_rings(self):
        return self.cpp_solver.num_active_rings
    
    @property
    def rings_ids(self):
        return self.cpp_solver.rings_ids
    
    @property
    def unique_rings_ids(self):
        return self.cpp_solver.unique_rings_ids
    
    @property
    def pos(self):
        return self.cpp_solver.pos
    
    @property
    def vel(self):
        return self.cpp_solver.vel
    
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
    def format_forces(self):
        return self.cpp_solver.format_forces
    
    @property
    def obs_forces(self):
        return self.cpp_solver.obs_forces
    
    @property
    def invasion_forces(self):
        return self.cpp_solver.invasion_forces
    
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

    @property
    def num_created_rings(self):
        return self.cpp_solver.num_created_rings
    
    def load_checkpoint(self, pos, angle, ids, uids):
        pos_in = [cpp_lib.data_types.PosVec(ring_pos) for ring_pos in pos]

        pos = cpp_lib.data_types.Vector3d(pos_in)
        angle = cpp_lib.data_types.List(angle)
        ids = cpp_lib.data_types.ListInt(ids)
        uids = cpp_lib.data_types.VecUInt(uids)

        self.cpp_solver.load_checkpoint(pos, angle, ids, uids)

    def update_visual_aids(self):
        self.cpp_solver.update_visual_aids()

    def update(self):
        self.update_func()
    
    def mean_vel_vec(self, ring_id: int):
        return self.cpp_solver.mean_vel_vec(ring_id)

    def mean_vel(self, ring_id: int):
        return self.cpp_solver.mean_vel(ring_id)
    
class SolverReplay:
    def __init__(self, run_cfg: ReplayDataCfg, dynamic_cfg: RingCfg, space_cfg: SpaceCfg) -> None:
        self.root_path = run_cfg.data_path
        # self.data_dir = run_cfg.data_path
        self.dt = run_cfg.int_cfg.dt

        self.solver_cfg: ReplaySolverCfg
        self.set_solver_cfg(run_cfg)

        with open(self.root_path / "metadata.yaml", "r") as f:
            metadata = yaml.unsafe_load(f)
            self.num_frames = metadata["num_frames"]

        mode = self.solver_cfg.mode

        self.init_func_map = {
            ReplaySolverCfg.Mode.normal: self.init_normal,
            ReplaySolverCfg.Mode.same_ids: self.init_same_ids,
            ReplaySolverCfg.Mode.same_ids_pre_calc: self.init_same_ids_pre_calc,
        }
        self.update_func_map = {
            ReplaySolverCfg.Mode.normal: self.update_normal,
            ReplaySolverCfg.Mode.same_ids: self.update_same_ids,
            ReplaySolverCfg.Mode.same_ids_pre_calc: self.update_same_ids_pre_calc,
        }

        self.init_func = self.init_func_map[mode]
        self.update_func = self.update_func_map[mode]

        self.count = 0
        self.time_sign = 1
        self.times = np.load(self.root_path / "times.npy") 
        self.time = self.times[self.count]
        
        self.init_func()
        self.num_particles = self.pos.shape[1]
        
        #=
        # Density
        #=
        ring_per_grid = self.solver_cfg.ring_per_grid

        self.space_cfg = space_cfg
        self.ring_d = utils.get_ring_radius(dynamic_cfg.diameter, self.num_particles)

        height, length = space_cfg.height, space_cfg.length
        num_rows, num_cols = (int(height/ring_per_grid/self.ring_d), int(length/ring_per_grid/self.ring_d))
        self.grid = utils.RegularGrid(
            length=length, height=height,
            num_cols=num_cols, num_rows=num_rows,
        )
        self.ring_count = np.zeros(self.grid.shape_mpl, dtype=int)
        self.calc_density()
        

    def set_solver_cfg(self, run_cfg: ReplayDataCfg):
        self.solver_cfg = run_cfg.solver_cfg
    
    def update_visual_aids(self):
        pass

    def init_normal(self):
        self.update_pos_normal(0)

    def init_same_ids(self):
        if not self.solver_cfg.vel_from_solver:
            self.pos2_original, self.ids2 = self.load(0)
        self.update_same_ids(0)

    def init_same_ids_pre_calc(self):
        ids_dir = os.path.join(self.root_path, "same_ids")
        self.all_ids = np.load(os.path.join(ids_dir, "ids.npy"))
        self.all_ids_size = np.load(os.path.join(ids_dir, "ids_size.npy"))
        
        self.pos2_original = np.load(os.path.join(self.data_dir, f"pos_{0}.npy"))
        self.update_pos_same_ids_pre_calc(0)
        self.calc_vel_cm(0)
    
    def update_pos_normal(self, frame):
        self.pos = np.load(self.root_path / f"pos_{frame}.npy")
    
    def update_pos_same_ids(self, frame):
        if frame >= self.num_frames-1:
            return

        if self.solver_cfg.vel_from_solver:
            self.pos, self.ids = self.load(frame)
        else:
            self.pos, self.ids = self.pos2_original, self.ids2
            self.pos2_original, self.ids2 = self.load(frame+1) 
            self.pos, self.pos2 = self.same_rings(self.pos, self.ids, self.pos2_original, self.ids2)
    
    def update_pos_same_ids_pre_calc(self, frame):
        self.pos = self.pos2_original
        self.pos2_original = np.load(self.root_path / f"pos_{frame+1}.npy")

        self.pos = self.pos[self.all_ids[frame, 0, :self.all_ids_size[frame]]]
        self.pos2 = self.pos2_original[self.all_ids[frame, 1, :self.all_ids_size[frame]]]

    def update_normal(self, frame):
        self.update_pos_normal(frame)

    def update_same_ids(self, frame):
        self.update_pos_same_ids(frame)
        self.calc_vel_cm(frame)
    
    def update_same_ids_pre_calc(self, frame):
        self.update_pos_same_ids_pre_calc(frame)
        self.calc_vel_cm(frame)


    @staticmethod
    def same_rings(pos1, ids1, pos2, ids2):
        argsort1 = np.argsort(ids1)
        argsort2 = np.argsort(ids2)
        
        ids1_sorted = np.sort(ids1)
        ids2_sorted = np.sort(ids2)

        common_ids = np.intersect1d(ids1_sorted, ids2_sorted)
        id_mask1 = np.where(np.in1d(ids1_sorted, common_ids))[0]
        id_mask2 = np.where(np.in1d(ids2_sorted, common_ids))[0]
        return pos1[argsort1[id_mask1]], pos2[argsort2[id_mask2]]

    def load(self, frame):
        pos = np.load(self.root_path / f"pos_{frame}.npy")
        ids = np.load(self.root_path / f"uids_{frame}.npy")
        return pos, ids

    def calc_vel_cm(self, frame):
        if self.solver_cfg.vel_from_solver:
            vel = np.load(os.path.join(self.data_dir, f"vel_{frame}.npy"))
        else:
            vel = (self.pos2 - self.pos)/self.dt
        
        self.vel_cm = vel.sum(axis=1)/vel.shape[1]
        self.vel_cm_dir = np.arctan2(self.vel_cm[:, 1], self.vel_cm[:, 0])

    def calc_density(self):
        self.cm = self.pos.sum(axis=1)/self.pos.shape[1]

        x = self.cm[:, 0] + self.space_cfg.length/2
        y = self.cm[:, 1] + self.space_cfg.height/2

        col_pos = (x / self.grid.cell_size[0]).astype(int)
        row_pos = (y / self.grid.cell_size[1]).astype(int)

        row_pos[row_pos == self.grid.shape_mpl[0]] -= 1
        col_pos[col_pos == self.grid.shape_mpl[1]] -= 1

        self.ring_count[:] = 0
        for idx in range(col_pos.size):
            self.ring_count[row_pos[idx], col_pos[idx]] += 1

    def update(self):
        self.count += self.time_sign
        
        if self.count >= self.num_frames: 
            self.count = self.num_frames-1
            return
        elif self.count < 0:
            self.count = 0
            return

        self.update_func(self.count)
        self.calc_density()

        self.time = self.times[self.count]

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