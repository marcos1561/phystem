import yaml
import numpy as np
from pathlib import Path

from phystem.systems.ring import solvers
from phystem.core.collectors import ColAutoSaveCfg
from .base import RingCol, ColCfg
from .config_to_col import Configs2Collector

class CreationRateColCfg(ColCfg):
    def __init__(self, wait_time, collect_time, collect_dt, autosave_cfg = None):
        super().__init__(autosave_cfg)
        self.wait_time = wait_time
        self.collect_dt = collect_dt
        self.collect_time = collect_time

class CreationRateCol(RingCol):
    def setup(self):
        #  Configuration
        self.wait_time = self.col_cfg.wait_time
        self.collect_time = self.col_cfg.collect_time
        self.collect_dt = self.col_cfg.collect_dt

        # State        
        self.wait_time_done = False
        self.last_time = self.solver.time
        self.point_id = 0

        # Data        
        self.num_points = int(self.collect_time/self.collect_dt)
        self.init_data_arrays()

        # if to_load_autosave:
        #     self.load_autosave()

    def init_data_arrays(self):
        self.time_arr = np.zeros(self.num_points, dtype=np.float32)
        self.num_created_arr = np.zeros(self.num_points, dtype=np.int32)
        self.num_active_arr = np.zeros(self.num_points, dtype=np.int32)


    def collect(self) -> None:
        time = self.solver.time

        if time < self.wait_time:
            return

        self.wait_time_done = True

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
        
        if self.autosave_cfg:
            self.check_autosave()
        
    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend([
            "wait_time_done",
            "last_time",
            "point_id",
            "time_arr",
            "num_created_arr",
            "num_active_arr",
        ]) 
        return v

    def load_autosave(self, use_backup=False):
        super().load_autosave(use_backup)
        
        time_arr = self.time_arr
        num_created_arr = self.num_created_arr
        num_active_arr = self.num_active_arr

        self.init_data_arrays()
        self.time_arr[:time_arr.size] = time_arr
        self.num_created_arr[:num_created_arr.size] = num_created_arr
        self.num_active_arr[:num_active_arr.size] = num_active_arr

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

Configs2Collector.add(CreationRateColCfg, CreationRateCol)