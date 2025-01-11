import numpy as np
import os, yaml

from phystem.core.run_config import ReplayDataCfg
from phystem.systems.ring.configs import RingCfg, SpaceCfg, StokesCfg
from phystem.systems.ring.run_config import IntegrationCfg, UpdateType, IntegrationType, ParticleWindows, InPolCheckerCfg
from phystem import cpp_lib

from .solver_config import *
from . import utils, rings_quantities

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
            int_cfg.in_pol_checker = InPolCheckerCfg(3, 3, 1, 1, True)

        dynamic_cfg_cpp = cpp_lib.configs.RingCfg(dynamic_cfg.cpp_constructor_args())
        
        if stokes_cfg is not None:
            stokes_cfg = cpp_lib.configs.StokesCfgPy(stokes_cfg.cpp_constructor_args())
        else:
            stokes_cfg = cpp_lib.configs.StokesCfgPy(StokesCfg.get_null_cpp_cfg())

        particle_win_cfg = cpp_lib.configs.ParticleWindowsCfg(
            int_cfg.particle_win_cfg.num_cols, int_cfg.particle_win_cfg.num_rows,
            int_cfg.particle_win_cfg.update_freq)
        
        in_pol_checker_cfg = cpp_lib.configs.InPolCheckerCfg(
            int_cfg.in_pol_checker.num_col_windows, int_cfg.in_pol_checker.num_rows_windows, 
            int_cfg.in_pol_checker.update_freq, int_cfg.in_pol_checker.steps_after, 
            int_cfg.in_pol_checker.disable)

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
            dynamic_cfg_cpp, 
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
        
        # self.cpp_solver.stokes_spawn_pos = cpp_lib.data_types.PosVec(
        #     dynamic_cfg.ring_spawn_pos()
        # )

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
    def creation_forces(self):
        return self.cpp_solver.creation_forces
    
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
    
    @property
    def windows_manager(self):
        return self.cpp_solver.windows_manager
    
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
    def __init__(self, run_cfg: ReplayDataCfg, num_max_rings, cfg: ReplaySolverCfg=None) -> None:
        self.root_path = run_cfg.data_path
        self.dt = run_cfg.int_cfg.dt
        self.num_max_rings = num_max_rings
        
        if cfg is None:
            cfg = ReplaySolverCfg()
        self.cfg = cfg

        self.solver_cfg: ReplaySolverCfg
        self.set_solver_cfg(run_cfg)

        with open(self.root_path / "metadata.yaml", "r") as f:
            metadata = yaml.unsafe_load(f)
            self.num_frames = metadata["num_frames"]

        self.times = np.load(self.root_path / "times.npy") 
        
        self.area_debug = AreaDebug(self)

        #state
        self.frame = -1
        self.time_sign = 1
        
        self.init()
        self.update()

        self.num_particles = self.pos.shape[1]
        if num_max_rings is None:
            num_max_rings = self.pos.shape[0]
        self.num_max_rings = num_max_rings

        self.rings_ids = np.arange(self.num_max_rings)

    @property
    def num_active_rings(self):
        return self.pos.shape[0]

    # @property
    # def rings_ids(self):
    #     if self.num_active_rings > self._ring_ids.size:
    #         self._ring_ids = np.arange(self.num_active_rings)
    #     return self._ring_ids

    @property
    def pos_continuos(self):
        return self.pos
    
    @property
    def center_mass(self):
        return rings_quantities.get_cm(self.pos)

    def set_solver_cfg(self, run_cfg: ReplayDataCfg):
        self.solver_cfg = run_cfg.solver_cfg
        if self.solver_cfg is None:
            self.solver_cfg = ReplaySolverCfg()

    def update_visual_aids(self):
        pass

    def init(self, frame=0):
        'Inicializa as posições para o frame `frame`'
        if not self.solver_cfg.vel_from_solver:
            self.pos2_original, self.ids2 = self.load(frame)

    def load(self, frame):
        '''
        Carrega e retorna as posições e uids do frame
        de índice `frame`.
        '''
        pos = np.load(self.root_path / f"pos_{frame}.npy")
        ids = np.load(self.root_path / f"uids_{frame}.npy")
        return pos, ids

    def get_vel_cm(self):
        '''
        Calcula e retorna a velocidade do centro de massa do frame atual e sua direção. 
        O calculo é realizado utilizando a posição do próximo frame.
        
        Retorno:
            (vel_cm, vel_cm_dir)
        '''
        if self.solver_cfg.vel_from_solver:
            vel = np.load(os.path.join(self.data_dir, f"vel_{self.frame}.npy"))
        else:
            vel = (self.pos2 - self.pos)/self.dt
        
        vel_cm = vel.sum(axis=1)/vel.shape[1]
        vel_cm_dir = np.arctan2(vel_cm[:, 1], vel_cm[:, 0])
        return vel_cm, vel_cm_dir

    def update_pos(self):
        "Atualiza as posições para o frame atual"
        if self.frame >= self.num_frames-self.cfg.calc_vel_dframes:
            return

        if self.solver_cfg.vel_from_solver:
            self.pos, self.ids = self.load(self.frame)
        else:
            self.pos, self.ids = self.pos2_original, self.ids2
            self.pos2_original, self.ids2 = self.load(self.frame+self.cfg.calc_vel_dframes) 
            self.pos, self.pos2, self.common_ids = utils.same_rings(self.pos, self.ids, self.pos2_original, self.ids2, return_common_ids=True)
            # self.ids = self.ids2 = common_ids

    def update(self):
        'Avança para o próximo frame.'
        self.frame += self.time_sign
        
        if self.frame >= self.num_frames: 
            self.frame = self.num_frames-self.cfg.calc_vel_dframes
            return
        elif self.frame < 0:
            self.frame = 0
            return

        self.update_pos()
        
        self.time = self.times[self.frame]


class AreaDebug:
    def __init__(self, solver: SolverReplay):
        self.solver = solver
        self._area: np.ndarray = None
        self.last_frame = None

    @property
    def area(self):
        if self.last_frame is None or self.last_frame != self.solver.frame:
            self.last_frame = self.solver.frame
            self._area = rings_quantities.get_area(self.solver.pos)
        
        return self._area