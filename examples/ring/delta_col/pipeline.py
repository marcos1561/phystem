from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import StateSaver
from phystem.core.run_config import CollectDataCfg
from phystem.utils import progress

from delta_col import DeltaCol

def collect_pipeline(sim: Simulation, cfg):
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg

    col = DeltaCol(**cfg, 
        solver=solver, path=collect_cfg.folder_path, configs=sim.configs,
        load_autosave=collect_cfg.is_autosave)

    prog = progress.Continuos(collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        prog.update(solver.time)
        solver.update()
        col.collect()
        col.check_autosave()

    col.save()
    prog.update(solver.time)