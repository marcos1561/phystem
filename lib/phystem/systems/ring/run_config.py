from enum import Enum

from phystem.core import run_config
from phystem.core.run_config import SolverType, UpdateType, CheckpointCfg

class IntegrationType(Enum):
    euler=0
    verlet=1

class RealTimeCfg(run_config.RealTimeCfg):
    def __init__(self, dt: float, num_steps_frame: int, fps: int, num_col_windows: int=None, 
        windows_update_freq=1, graph_cfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL, 
        integration_type=IntegrationType.euler, checkpoint: CheckpointCfg=None) -> None:
        
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, num_steps_frame, fps, graph_cfg, solver_type, update_type, checkpoint)
        
        self.num_col_windows = num_col_windows
        self.windows_update_freq = windows_update_freq
        self.integration_type = integration_type


class CollectDataCfg(run_config.CollectDataCfg):
    def __init__(self, tf: float, dt: float, folder_path: str, num_col_windows: int=None, windows_update_freq=1,
        func_cfg=None, func: callable = None, func_id=None, get_func: callable = None, solver_type=SolverType.CPP, 
        update_type=UpdateType.NORMAL,  integration_type=IntegrationType.euler, checkpoint: CheckpointCfg=None) -> None:
        
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(tf, dt, folder_path, func_cfg, func, func_id, get_func, solver_type, update_type, checkpoint)
        
        self.num_col_windows = num_col_windows
        self.windows_update_freq = windows_update_freq
        self.integration_type = integration_type

class SaveCfg(run_config.SaveCfg):
    def __init__(self, path: str, speed: float, fps: int, dt: float, num_col_windows:int=None, windows_update_freq=1, 
        duration: float = None,  tf: float = None, graph_cfg=None, solver_type=SolverType.CPP, 
        update_type=UpdateType.NORMAL, integration_type=IntegrationType.euler, checkpoint: CheckpointCfg=None) -> None:
        
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")
        
        super().__init__(path, speed, fps, dt, duration, tf, graph_cfg, solver_type, update_type, checkpoint)
        
        self.num_col_windows = num_col_windows
        self.windows_update_freq = windows_update_freq
        self.integration_type = integration_type
