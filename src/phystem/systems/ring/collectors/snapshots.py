from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.simulation import Simulation

from .base import RingCol, StateSaver

class SnapshotsColCfg:
    def __init__(self, snaps_dt: float, wait_time: float = 0, autosave_cfg: ColAutoSaveCfg = None) -> None:
        self.snaps_dt = snaps_dt
        self.wait_time = wait_time
        self.autosave_cfg = autosave_cfg

class SnapshotsCol(RingCol):
    def __init__(self, col_cfg: SnapshotsColCfg,
        solver: CppSolver, root_path: Path, configs: dict, 
        exist_ok=False, to_load_autosave=False, **kwargs) -> None:
        super().__init__(solver, root_path, configs, col_cfg.autosave_cfg, exist_ok, **kwargs)

        self.cfgs = col_cfg

        # State
        self.snaps_last_time = self.solver.time
        self.snaps_count = 0
        self.init_time = self.solver.time
        self.times = []

        self.snaps_saver = StateSaver(
            solver=solver, root_path=self.data_path, configs=configs,
        )

        if to_load_autosave:
            self.load_autosave()

    @property
    def vars_to_save(self):
        return ["snaps_count", "snaps_last_time", "init_time", "times"]            
    
    def collect(self) -> None:
        if self.solver.time < self.cfgs.wait_time:
            return

        if self.solver.time < self.snaps_last_time + self.cfgs.snaps_dt:
            return
        
        self.snaps_last_time = self.solver.time

        self.snaps_saver.save(
            filenames=StateSaver.FileNames(
                pos=f"pos_{self.snaps_count}",
                angle=f"angle_{self.snaps_count}",
                uids=f"uids_{self.snaps_count}",
                metadata=None,
                ids=None,
            )
        )
        self.times.append(self.solver.time)

        self.snaps_count += 1

        if self.autosave_cfg:
            self.check_autosave()
    
    def save(self):
        import yaml
        import numpy as np

        np.save(self.data_path / "times.npy", np.array(self.times))

        with open(self.data_path / "metadata.yaml", "w") as f:
            yaml.dump({
                "frame_dt": self.cfgs.snaps_dt,
                "init_time": self.init_time,
                "num_frames": self.snaps_count,
            }, f)

    @staticmethod
    def pipeline(sim: Simulation, cfg: SnapshotsColCfg):
        from phystem.core.run_config import CollectDataCfg
        from phystem.utils import progress
        
        collect_cfg: CollectDataCfg = sim.run_cfg
        solver = sim.solver

        col = SnapshotsCol(cfg,
            root_path=collect_cfg.folder_path, solver=sim.solver, configs=sim.configs, 
            to_load_autosave=collect_cfg.is_autosave,
        )

        prog = progress.Continuos(collect_cfg.tf, start=col.init_time)
        while solver.time < collect_cfg.tf:
            solver.update()
            col.collect()
            prog.update(solver.time)
        col.save()
        prog.update(solver.time)
