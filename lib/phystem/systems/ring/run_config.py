from phystem.core import run_config
from phystem.core.run_config import SolverType, UpdateType
from phystem.systems.ring.ui.graph import GraphCfg


class RealTimeCfg(run_config.RealTimeCfg):
    def __init__(self, dt: float, num_steps_frame: int, fps: int, num_col_windows: int=None, graph_cfg: GraphCfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, num_steps_frame, fps, graph_cfg, solver_type, update_type)
        self.num_col_windows = num_col_windows

class CollectDataCfg(run_config.CollectDataCfg):
    def __init__(self, tf: float, dt: float, folder_path: str, num_col_windows: int=None, func_cfg=None, func: callable = None, func_id=None, get_func: callable = None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(tf, dt, folder_path, func_cfg, func, func_id, get_func, solver_type, update_type)
        self.num_col_windows = num_col_windows

class SaveCfg(run_config.SaveCfg):
    def __init__(self, path: str, speed: float, fps: int, dt: float, num_col_windows:int=None, duration: float = None, tf: float = None, graph_cfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        if update_type == UpdateType.WINDOWS and num_col_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")
        super().__init__(path, speed, fps, dt, duration, tf, graph_cfg, solver_type, update_type)
        self.num_col_windows = num_col_windows
        
