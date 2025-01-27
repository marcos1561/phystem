from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from .base import RingCol
from phystem.core import settings

class ColManager(RingCol):
    def __init__(self, 
        solver: CppSolver, root_path: Path, configs: dict, 
        to_load_autosave=False,
        autosave_cfg: ColAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok, data_dirname=None)

        self.to_load_autosave = to_load_autosave
        self.cols: dict[str, RingCol] = {}

        if self.to_load_autosave:
            # self.use_backup = self.get_autosave_path(self.autosave_container_path).stem == settings.autosave_root_backup_name
            # print("Use backup:", self.use_backup)
            self.load_autosave()

    def add_collector(self, ColT: type[RingCol], configs: dict[str], name: str):
        if "autosave_cfg" in configs:
            raise ValueError((
                "'configs' contém a chave 'autosave_cfg', mas é proibido utilizá-la. "
                "'autosave_cfg' apenas deve ser utilizado pelo gerenciador dos coletores."
            ))

        root_path = self.root_path / name
        col = ColT(**configs, 
            solver=self.solver, root_path=root_path, configs=self.configs,
        )

        self.cols[name] = col
        if self.to_load_autosave:
            col.load_autosave()

            if abs(col.autosave_last_time - self.autosave_last_time) > 0.01:
                col.load_autosave(use_backup=True)
                if abs(col.autosave_last_time - self.autosave_last_time) > 0.01:
                    raise Exception(f"O coletor '{name}' não possui um auto-salvamento válido!")

    def collect(self) -> None:
        for col in self.cols.values():
            col.collect()

        if self.autosave_cfg:
            self.check_autosave()
    
    def autosave(self):
        super().autosave()
        
        for col in self.cols.values():
            col.autosave_last_time = self.solver.time
            col.exec_autosave()

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
                autosave_cfg=cfg.get("autosave_cfg", None),
                to_load_autosave=collect_cfg.is_autosave,
            )
            for name, ColT in cols.items():
                collectors.add_collector(ColT, ColT.get_kwargs_configs(cfg[name]), name)

            prog = progress.Continuos(collect_cfg.tf)
            while solver.time < collect_cfg.tf:
                prog.update(solver.time)
                solver.update()
                collectors.collect()

            if collectors.autosave_cfg:
                collectors.exec_autosave()
            collectors.save()
            prog.update(solver.time)
        
        return pipeline