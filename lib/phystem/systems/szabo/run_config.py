from enum import Enum, auto

from phystem.core import run_config
from phystem.core.run_config import SolverType

class UpdateType(Enum):
    WINDOWS = auto()
    NORMAL = auto()

class IntegrationCfg(run_config.IntegrationCfg):
    def __init__(self, dt: float, num_col_windows: int=None, 
        solver_type=SolverType.CPP, update_type=UpdateType.WINDOWS) -> None:
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, solver_type, update_type)
        self.num_col_windows = num_col_windows

class GraphCfg:
    '''
    Configurações do gráfico das partículas.
    '''
    def __init__(self, show_circles=False) -> None:
        self.show_circles = show_circles