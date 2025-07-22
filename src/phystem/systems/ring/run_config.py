from enum import Enum, auto

from phystem.core import run_config
from phystem.systems.ring.configs import SpaceCfg, RingCfg
from phystem.core.run_config import (
    load_configs, save_configs,
    RunType,
    SolverType,
    RealTimeCfg,
    SaveCfg,
    CheckpointCfg,
    CollectDataCfg,
    ReplayDataCfg,
    SaveCfg,
)


class UpdateType(Enum):
    '''
    Integration mode to be used by the solver.

    Variants:
    ---------
        PERIODIC_NORMAL:
            Normal integration, no tricks involved, with periodic boundaries.
        
        PERIODIC_WINDOWS:
            Window technique with periodic boundaries.

        STOKES:
            Stokes flow geometry.

        INVAGINATION:
            Ring made of rings with control of the inner and outer surface configurations.
    '''
    PERIODIC_NORMAL = auto()
    PERIODIC_WINDOWS = auto()
    STOKES = auto()
    INVAGINATION = auto()

class IntegrationType(Enum):
    euler=0
    verlet=1
    rk4=2

class InPolCheckerCfg:
    def __init__(self, num_col_windows: int, num_rows_windows: int, update_freq: int, steps_after, disable=False) -> None:
        self.num_col_windows = num_col_windows
        self.num_rows_windows = num_rows_windows
        self.update_freq = update_freq
        self.steps_after = steps_after
        self.disable = disable

class ParticleWindows:
    def __init__(self, num_cols: int, num_rows: int, update_freq: int) -> None:
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.update_freq = update_freq

class IntegrationCfg(run_config.IntegrationCfg):
    def __init__(self, dt: float, particle_win_cfg: ParticleWindows=None, 
        integration_type=IntegrationType.euler, solver_type=SolverType.CPP, update_type=UpdateType.PERIODIC_NORMAL,
        in_pol_checker: InPolCheckerCfg=None) -> None:
        if update_type == UpdateType.PERIODIC_WINDOWS and particle_win_cfg is None:
            raise ValueError("'particle_win_cfg' deve ser especificado.")

        super().__init__(dt, solver_type)
        
        self.update_type = update_type
        self.particle_win_cfg = particle_win_cfg
        self.integration_type = integration_type
        self.in_pol_checker = in_pol_checker

    def update_grid_shapes(self, space_cfg: SpaceCfg, dynamic_cfg: RingCfg):
        '''
        Updates the shape of the particle and ring grids, given a new space configuration (`space_cfg`),
        so that the number of cells is as large as possible.
        '''
        num_cols, num_rows = space_cfg.particle_grid_shape(dynamic_cfg.max_dist)
        num_cols_cm, num_rows_cm = space_cfg.rings_grid_shape(dynamic_cfg.get_ring_radius())
        self.particle_win_cfg.num_cols = num_cols
        self.particle_win_cfg.num_rows = num_rows
        self.in_pol_checker.num_col_windows = num_cols_cm
        self.in_pol_checker.num_rows_windows = num_rows_cm