from pathlib import Path
from phystem.core import settings
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring import Simulation
from .base import RingCol, StateSaver

class CheckpointCol(RingCol):
    def __init__(self, 
        solver: CppSolver, root_path: Path, configs: dict, autosave_cfg: ColAutoSaveCfg=None, 
        exist_ok=False, to_load_autosave=False, **kwargs) -> None:
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok, 
            data_dirname=None, **kwargs)
        self.checkpoint_path = self.root_path / "checkpoint"
        
        if settings.IS_TESTING:
            exist_ok = True
        self.checkpoint_path.mkdir(parents=True, exist_ok=exist_ok)

        self.check_saver = StateSaver(solver, self.checkpoint_path, configs)

        if to_load_autosave:
            self.load_autosave()

    @property
    def vars_to_save(self):
        return []

    def collect(self) -> None:
        if self.autosave_cfg:
            self.check_autosave()

    def save(self):
        self.check_saver.save()
    
    @staticmethod
    def pipeline(sim: Simulation, cfg: dict):
        from phystem.core.run_config import CollectDataCfg
        from phystem.utils import progress
        
        collect_cfg: CollectDataCfg = sim.run_cfg
        solver = sim.solver

        col = CheckpointCol(**cfg,
            root_path=collect_cfg.folder_path, solver=sim.solver, configs=sim.configs, 
            to_load_autosave=collect_cfg.is_autosave,
        )

        prog = progress.Continuos(collect_cfg.tf)
        while solver.time < collect_cfg.tf:
            solver.update()
            col.collect()
            prog.update(solver.time)
        col.save()
        prog.update(solver.time)