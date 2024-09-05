from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import CollectDataCfg
from phystem.utils import progress

from phystem.systems.ring.collectors import DenVelCol, CreationRateCol, DeltaCol, ColManager

def collect_pipeline(sim: Simulation, cfg):
    solver = sim.solver
    collect_cfg: CollectDataCfg = sim.run_cfg

    collectors = ColManager(
        solver=solver, root_path=collect_cfg.folder_path, configs=sim.configs,
        autosave_cfg=cfg["autosave_cfg"],
        to_load_autosave=collect_cfg.is_autosave,
    )
    collectors.add_collector(DeltaCol, cfg["delta"], "delta")
    collectors.add_collector(DenVelCol, cfg["den_vel"], "den_vel")
    collectors.add_collector(CreationRateCol, cfg["cr"], "cr")

    prog = progress.Continuos(collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        prog.update(solver.time)
        solver.update()
        collectors.collect()

    collectors.save()
    prog.update(solver.time)
