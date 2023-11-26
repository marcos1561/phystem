from enum import Enum

from phystem.core import run_config
from phystem.core.run_config import SolverType, UpdateType

class IntegrationType(Enum):
    euler=0
    verlet=1
    rk4=2

class IntegrationCfg(run_config.IntegrationCfg):
    def __init__(self, dt: float, num_col_windows: int=None, windows_update_freq=1, 
        integration_type=IntegrationType.euler, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, solver_type, update_type)
        self.num_col_windows = num_col_windows
        self.windows_update_freq = windows_update_freq
        self.integration_type = integration_type