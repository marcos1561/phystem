from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from .base import RingCol

class ColManager(RingCol):
    def __init__(self, 
        solver: CppSolver, root_path: str | Path, configs: dict, 
        is_autosave=False,
        autosave_cfg: ColAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok, data_dirname=None)

        self.is_autosave = is_autosave
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
        if self.is_autosave:
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