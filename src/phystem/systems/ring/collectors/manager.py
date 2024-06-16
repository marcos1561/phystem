from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from .base import RingCol

class ColManager(RingCol):
    def __init__(self, 
        solver: CppSolver, root_path: Path, configs: dict, 
        to_load_autosave=False,
        autosave_cfg: ColAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok, data_dirname=None)

        self.to_load_autosave = to_load_autosave
        self.cols: dict[str, RingCol] = {}

    @property
    def vars_to_save(self):
        return

    def add_collector(self, ColT: type[RingCol], configs: dict[str], name: str):
        root_path = self.root_path / name
        col = ColT(**configs, 
            solver=self.solver, root_path=root_path, configs=self.configs,
        )

        self.cols[name] = col
        if self.to_load_autosave:
            col.load_autosave()

    def collect(self) -> None:
        for col in self.cols.values():
            col.collect()

        if self.autosave_cfg:
            self.check_autosave()
    
    def autosave(self):
        super().autosave()
        for col in self.cols.values():
            col.autosave()

    def save(self):
        for col in self.cols.values():
            col.save()

    @staticmethod
    def get_pipeline(cols: dict[str, type[RingCol]]):
        from phystem.systems.ring import Simulation
        from phystem.core.run_config import CollectDataCfg
        from phystem.utils import progress

        def pipeline(sim: Simulation, cfg):
            solver = sim.solver
            collect_cfg: CollectDataCfg = sim.run_cfg

            collectors = ColManager(
                solver=solver, root_path=collect_cfg.folder_path, configs=sim.configs,
                autosave_cfg=cfg["autosave_cfg"],
                to_load_autosave=collect_cfg.is_autosave,
            )
            for name, ColT in cols.items():
                collectors.add_collector(ColT, cfg[name], name)

            prog = progress.Continuos(collect_cfg.tf)
            while solver.time < collect_cfg.tf:
                prog.update(solver.time)
                solver.update()
                collectors.collect()

            collectors.save()
            prog.update(solver.time)
        
        return pipeline