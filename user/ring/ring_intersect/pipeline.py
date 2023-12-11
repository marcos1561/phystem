import numpy as np
import time, os
from datetime import timedelta

from phystem.systems.ring.simulation import Simulation
from phystem.core.run_config import CollectDataCfg
from phystem.systems.ring.collectors import LastState

from phystem.utils import progress

def collect_pipeline(sim: Simulation, collect_cfg): 
    solver = sim.solver
    cfg: CollectDataCfg = sim.run_cfg

    timer = sim.time_it

    prog = progress.Continuos(cfg.tf)

    collector = LastState(solver, cfg.folder_path, sim.configs)
    in_data = []
    has_intersection = False

    count = 0
    t1 = time.time()
    while solver.time < cfg.tf:
        num_inside = solver.in_pol_checker.num_inside_points
        if num_inside > 0:
            # print("Sim time:", solver.time)
            # print("Intersecção de anéis")
            
            # n = solver.in_pol_checker.num_inside_points
            # file_path = os.path.join(cfg.folder_path, "inside_points.npy")
            # np.save(file_path, np.array(solver.in_pol_checker.inside_points[:n]))

            # collector.save()
            # break

            if not has_intersection:
                has_intersection = True
                in_data.append([solver.time, num_inside])
        else:
            has_intersection = False

        timer.decorator(solver.update)
        prog.update(solver.time)
        count += 1
    t2 = time.time()

    collector.save()
    in_data_path = os.path.join(collector.path, "in_data.npy")
    np.save(in_data_path, np.array(in_data))

    n = solver.in_pol_checker.num_inside_points
    last_in_points_path = os.path.join(cfg.folder_path, "inside_points.npy")
    if n > 0:
        np.save(last_in_points_path, np.array(solver.in_pol_checker.inside_points[:n]))
    else:
        np.save(last_in_points_path, np.array([]))

    print("Elapsed time:", timedelta(seconds=t2-t1))
