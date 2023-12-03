import numpy as np
import time, os
from datetime import timedelta

from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import CollectDataCfg
from phystem.systems.ring.collectors import LastPos

from phystem.utils import progress

def collect_pipeline(sim: Simulation, collect_cfg): 
    solver = sim.solver
    cfg: CollectDataCfg = sim.run_cfg

    timer = sim.time_it

    prog = progress.Continuos(cfg.tf)
    collector = LastPos(solver, cfg.folder_path, sim.configs)

    count = 0
    t1 = time.time()
    while solver.time < cfg.tf:
        if solver.in_pol_checker.num_inside_points > 0:
            print("Sim time:", solver.time)
            print("Intersecção de anéis")
            
            n = solver.in_pol_checker.num_inside_points
            file_path = os.path.join(cfg.folder_path, "inside_points.npy")
            np.save(file_path, np.array(solver.in_pol_checker.inside_points[:n]))

            collector.save()
            break

        timer.decorator(solver.update)
        prog.update(solver.time)
        count += 1
    t2 = time.time()

    print("Elapsed time:", timedelta(seconds=t2-t1))
