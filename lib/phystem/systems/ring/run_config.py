from enum import Enum, auto

from phystem.core import run_config
from phystem.core.run_config import SolverType

class UpdateType(Enum):
    '''
    Modo de integração a ser utilizado pelo solver.

    Variants:
    ---------
        NORMAL:
            Integração normal, sem mágicas envolvidas.
        
        WINDOWS:
            Divide o espaço em janelas e mantém atualizado quem está em cada
            janela.
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
    def __init__(self, num_col_windows: int, num_rows_windows: int, update_freq: int, disable=False) -> None:
        self.num_col_windows = num_col_windows
        self.num_rows_windows = num_rows_windows
        self.update_freq = update_freq
        self.disable = disable

class ParticleWindows:
    def __init__(self, num_cols: int, num_rows: int, update_freq: int) -> None:
        self.num_cols = num_cols
        self.num_rows = num_rows
        self.update_freq = update_freq

class IntegrationCfg(run_config.IntegrationCfg):
    def __init__(self, dt: float, particle_win_cfg: ParticleWindows=None, 
        integration_type=IntegrationType.euler, solver_type=SolverType.CPP, update_type=UpdateType.PERIODIC_NORMAL,
        in_pol_checker=InPolCheckerCfg(3, 1, True)) -> None:
        if update_type == UpdateType.PERIODIC_WINDOWS and particle_win_cfg is None:
            raise ValueError("'particle_win_cfg' deve ser especificado.")

        super().__init__(dt, solver_type)
        self.update_type = update_type
        self.particle_win_cfg = particle_win_cfg
        self.integration_type = integration_type
        self.in_pol_checker = in_pol_checker