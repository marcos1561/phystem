from pathlib import Path
from phystem.core import settings
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring import Simulation
from phystem.systems.ring.state_saver import StateSaver
from .base import RingCol, ColCfg
from .config_to_col import Configs2Collector

class CheckpointColCfg(ColCfg):
    def __init__(self, autosave_cfg = None):
        super().__init__(autosave_cfg)
        self.to_load_autosave = False

class CheckpointCol(RingCol):
    def setup(self):
        self.checkpoint_path = self.root_path / "checkpoint"
        
        if settings.IS_TESTING:
            exist_ok = True
        self.checkpoint_path.mkdir(parents=True, exist_ok=exist_ok)

        self.check_saver = StateSaver(self.solver, self.checkpoint_path, self.configs)

    def collect(self) -> None:
        if self.autosave_cfg:
            self.check_autosave()

    def save(self):
        self.check_saver.save()
    
    @staticmethod
    def pipeline(sim: Simulation, cfg: CheckpointColCfg):
        from phystem.core.run_config import CollectDataCfg
        from phystem.utils import progress
        
        collect_cfg: CollectDataCfg = sim.run_cfg
        solver = sim.solver

        col = CheckpointCol(
            col_cfg=cfg,
            root_path=collect_cfg.folder_path, solver=sim.solver, configs=sim.configs, 
        )

        if collect_cfg.is_autosave:
            col.load_autosave()

        prog = progress.Continuos(collect_cfg.tf)
        while solver.time < collect_cfg.tf:
            solver.update()
            col.collect()
            prog.update(solver.time)
        col.save()
        prog.update(solver.time)

    @classmethod
    def get_pipeline(Cls):
        return Cls.pipeline

def pipeline(sim: Simulation, cfg: dict):
    CheckpointCol.pipeline(sim, cfg)

Configs2Collector.add(CheckpointColCfg, CheckpointCol)