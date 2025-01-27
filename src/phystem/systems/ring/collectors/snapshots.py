import numpy as np
from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.state_saver import StateSaver, StateData

from .base import RingCol, ColCfg
from .config_to_col import Configs2Collector

class SnapshotsColCfg(ColCfg):
    def __init__(self, snaps_dt: float, xlims=(-1, -1), wait_time: float = 0, autosave_cfg: ColAutoSaveCfg = None) -> None:
        super().__init__(autosave_cfg)
        self.snaps_dt = snaps_dt
        self.xlims = xlims
        self.wait_time = wait_time
        self.autosave_cfg = autosave_cfg

class SnapshotsCol(RingCol):
    def setup(self):
        self.cfgs = self.col_cfg

        # State
        self.snaps_last_time = self.solver.time
        self.snaps_count = 0
        self.init_time = self.solver.time
        self.times = []

        self.snaps_saver = StateSaver(
            solver=self.solver, root_path=self.data_path, configs=self.configs, xlims=self.col_cfg.xlims,
        )

    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend(
            ["snaps_count", "snaps_last_time", "init_time", "times"]            
        )
        return v
    
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
        )

        if collect_cfg.is_autosave:
            col.load_autosave()

        prog = progress.Continuos(collect_cfg.tf, start=col.init_time)
        while solver.time < collect_cfg.tf:
            solver.update()
            col.collect()
            prog.update(solver.time)
        col.save()
        prog.update(solver.time)
    
    @staticmethod
    def load_snaps(root_path):
        "Carrega todas as snapshot no caminho raiz `root_path`."
        data_path = Path(root_path) / "data"
        
        def value_path(name, id):
            return Path(data_path / f"{name}_{count}.npy")

        snaps: list[StateData] = []
        count = 0
        while value_path("pos", count).exists():
            snaps.append(StateData(
                pos=np.load(value_path("pos", count)),
                angle=np.load(value_path("angle", count)),
                uids=np.load(value_path("uids", count)),
                ids=None,
            ))

            count += 1
        
        return snaps

def pipeline(sim: Simulation, cfg: SnapshotsColCfg):
    SnapshotsCol.pipeline(sim, cfg)

Configs2Collector.add(SnapshotsColCfg, SnapshotsCol)