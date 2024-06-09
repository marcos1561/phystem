import yaml
import numpy as np
from pathlib import Path

from phystem.systems.ring import solvers
from phystem.core.collectors import ColAutoSaveCfg
from .base import RingCol

class CreationRateCol(RingCol):
    def __init__(self, wait_time, collect_time, collect_dt, 
        solver: solvers.CppSolver, root_path: str | Path, configs: dict, 
        autosave_cfg: ColAutoSaveCfg=None, load_autosave=False, exist_ok=False) -> None:
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok=exist_ok)
        # Configuration
        self.wait_time = wait_time
        self.collect_time = collect_time
        self.collect_dt = collect_dt

        # State        
        self.wait_time_done = False
        self.last_time = self.solver.time
        self.point_id = 0
        self.num_points = int(self.collect_time/self.collect_dt)

        # Data        
        self.time_arr = np.zeros(self.num_points, dtype=np.float32)
        self.num_created_arr = np.zeros(self.num_points, dtype=np.int32)
        self.num_active_arr = np.zeros(self.num_points, dtype=np.int32)

        if load_autosave:
            self.load_autosave()

    def collect(self) -> None:
        time = self.solver.time

        if time < self.wait_time:
            return

        if time > self.collect_time + self.wait_time:
            return
        
        if self.point_id > self.num_points-1:
            return

        self.num_created_arr[self.point_id] += self.solver.num_created_rings   
        
        if self.solver.time - self.last_time > self.collect_dt:
            self.last_time = self.solver.time
            self.time_arr[self.point_id] = self.solver.time
            self.num_active_arr[self.point_id] = self.solver.num_active_rings   
            self.point_id += 1
        
    @property
    def vars_to_save(self):
        return [
            "wait_time_done",
            "last_time",
            "point_id",
            "num_points",
            "time_arr",
            "num_created_arr",
            "num_active_arr",
        ]

    def save(self, data_path: Path=None):
        if data_path is None:
            data_path = self.data_path
        else:
            data_path = Path(data_path)

        metadata = {"num_points": self.point_id}
        with open(data_path / "cr_metadata.yaml", "w") as f:
            yaml.dump(metadata, f)

        np.save(data_path / f"time.npy", self.time_arr)
        np.save(data_path / f"num_created.npy", self.num_created_arr)
        np.save(data_path / f"num_active.npy", self.num_active_arr)
