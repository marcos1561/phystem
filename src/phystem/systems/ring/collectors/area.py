from pathlib import Path
import numpy as np
import yaml, pickle

from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring import collectors

class AreaCol(collectors.RingCol):
    def __init__(self, freq_dt, 
        solver: CppSolver, root_path: Path, configs: dict, 
        wait_time=0,
        autosave_cfg: collectors.ColAutoSaveCfg = None, exist_ok=False, **kwargs) -> None:
        "Coletor da área formada pelos centros das partículas do anel."
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok, **kwargs)

        self.freq_dt = freq_dt
        self.wait_time = wait_time

        # State
        self.last_col_time = self.solver.time
        self.areas = []
        self.pos = []
        self.times = []

    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend(["areas", "pos", "times", "last_col_time"])
        return v

    def collect(self) -> None:
        t = self.solver.time

        if t < self.wait_time:
            return

        if t - self.last_col_time < self.freq_dt:
            return
        self.last_col_time = t

        num_active = self.solver.num_active_rings
        ids_active = np.array(self.solver.rings_ids[:num_active])

        areas = np.array(self.solver.area_debug.area)[ids_active]
        cms = np.array(self.solver.center_mass)[ids_active]
        
        self.areas.append(np.array(areas))
        self.pos.append(np.array(cms))
        self.times.append(t)

        if self.autosave_cfg:
            self.check_autosave()
    
    def save(self):
        with open(self.data_path / "data.pickle", "wb") as f:
            pickle.dump({
                "times": self.times, "areas": self.areas,
                "pos": self.pos ,
            }, f)

        with open(self.data_path / "metadata.yaml", "w") as f:
            yaml.dump({
                "num_points": len(self.times),
            }, f)