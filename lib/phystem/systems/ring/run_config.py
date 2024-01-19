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

class IntegrationType(Enum):
    euler=0
    verlet=1
    rk4=2

class InPolCheckerCfg:
    def __init__(self, num_col_windows: int, update_freq: int, disable=False) -> None:
        self.num_col_windows = num_col_windows
        self.update_freq = update_freq
        self.disable = disable

class IntegrationCfg(run_config.IntegrationCfg):
    def __init__(self, dt: float, num_col_windows: int=None, windows_update_freq=1, 
        integration_type=IntegrationType.euler, solver_type=SolverType.CPP, update_type=UpdateType.PERIODIC_NORMAL,
        in_pol_checker=InPolCheckerCfg(3, 1, True)) -> None:
        if update_type == UpdateType.PERIODIC_WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, solver_type)
        self.update_type = update_type
        self.num_col_windows = num_col_windows
        self.windows_update_freq = windows_update_freq
        self.integration_type = integration_type
        self.in_pol_checker = in_pol_checker