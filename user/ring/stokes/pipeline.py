import time, os
import numpy as np

from phystem.core.run_config import CollectDataCfg

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState

from phystem.utils import progress

# class PipelineCfg:
#     def __init__(self, ) -> None:
#         pass

def collect_pipeline(sim: Simulation, cfg):
    solver = sim.solver
    cfg: CollectDataCfg = sim.run_cfg

    prog = progress.Continuos(cfg.tf)

    collector = LastState(solver, cfg.folder_path, sim.configs)
    t1 = time.time()
    while solver.time < cfg.tf:
        solver.update()
        prog.update(solver.time)
    t2 = time.time()

    collector.save()

    last_invasion_path = os.path.join(cfg.folder_path, "last_invasion.npy")
    n = solver.in_pol_checker.num_inside_points
    if n > 0:
        np.save(last_invasion_path, np.array(solver.in_pol_checker.inside_points[:n]))
    else:
        np.save(last_invasion_path, np.array([]))

    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))
