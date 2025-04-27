from pathlib import Path
from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring.solvers import CppSolver
from phystem.core import settings

from .base import RingCol, ColCfg
from .config_to_col import Configs2Collector

class ColManagerCfg(ColCfg):
    def __init__(self, cols_cfgs: dict[str, ColCfg], autosave_cfg = None):
        super().__init__(autosave_cfg)
        self.cols_cfgs = cols_cfgs

        self.to_load_autosave = False

class ColManager(RingCol):
    col_cfg: ColManagerCfg
    
    def setup(self):
        self.cols: dict[str, RingCol] = {}

        if self.col_cfg.to_load_autosave:
            # self.use_backup = self.get_autosave_path(self.autosave_container_path).stem == settings.autosave_root_backup_name
            # print("Use backup:", self.use_backup)
            self.load_autosave()

        for name, col_i_cfg in self.col_cfg.cols_cfgs.items():
            self.add_collector(col_i_cfg, name)

    def add_collector(self, configs: ColCfg, name: str):
        if configs.autosave_cfg is not None:
            raise ValueError((
                "'configs' contém 'autosave_cfg', mas é proibido utilizá-lo."
                "'autosave_cfg' apenas deve ser utilizado pelo gerenciador dos coletores."
            ))

        root_path = self.root_path / name
        ColT: type[RingCol] = Configs2Collector.get(type(configs))
        col = ColT(col_cfg=configs, 
            solver=self.solver, root_path=root_path, configs=self.configs,
        )

        self.cols[name] = col
        if self.col_cfg.to_load_autosave:
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

    @classmethod
    def get_pipeline(Cls):
        from phystem.systems.ring import Simulation
        from phystem.core.run_config import CollectDataCfg
        from phystem.utils import progress

        def pipeline(sim: Simulation, cfg: ColManagerCfg):
            solver = sim.solver
            collect_cfg: CollectDataCfg = sim.run_cfg

            cfg.to_load_autosave = collect_cfg.is_autosave

            collectors = Cls(
                col_cfg=cfg,
                solver=solver, root_path=collect_cfg.folder_path, configs=sim.configs,
            )
            # for name, ColT in cols.items():
            #     collectors.add_collector(ColT, ColT.get_kwargs_configs(cfg[name]), name)

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
    
Configs2Collector.add(ColManagerCfg, ColManager)