from metcompb import progress
import physical_system.collectors as collectors
from physical_system.simulation import Simulation
from physical_system.solver import CppSolver
from physical_system.configs import *

def state(sim: Simulation):
    run_cfg: CollectDataCfg = sim.run_cfg
    solver: CppSolver = sim.solver

    prog = progress.Continuos(run_cfg.tf)
    if not run_cfg.only_last:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            dt=run_cfg.dt, tf=run_cfg.tf, num_points=1000,
        )
        
        state_collector.collect(0)
        count = 0
        while solver.time < run_cfg.tf:
            solver.update()
            state_collector.collect(count)
            
            prog.update(solver.time)
            count += 1
        
        state_collector.save()
    else:
        state_collector = collectors.State(
            solver, run_cfg.folder_path, sim.configs,
            tf=0, dt=run_cfg.dt, num_points=2,
        )
        
        state_collector.collect(0)
        while solver.time < run_cfg.tf:
            solver.update()
            prog.update(solver.time)
        
        state_collector.collect(1)
        state_collector.save()

def nabla_range(sim: Simulation):
    import numpy as np
    import os
    
    run_cfg: CollectDataCfg = sim.run_cfg
    solver: CppSolver = sim.solver

    num_points = 1000
    nabla_range = np.linspace(0, 3, 20)
    
    prog = progress.Continuos(nabla_range.max())
    
    mean_vel_data = np.zeros((nabla_range.size, num_points))
    for id, nabla in enumerate(nabla_range):
        sim.self_propelling_cfg.nabla = nabla
        sim.init_sim()

        collector = collectors.MeanVel(
            solver, run_cfg.tf, run_cfg.dt,
            num_points=num_points, path=run_cfg.folder_path,
        )

        count = 0
        while solver.time < run_cfg.tf:
            solver.update()
            collector.collect(count)
            count += 1
        
        prog.update(nabla)

        mean_vel_data[id] = collector.data[0]     
        time_data = collector.data[1]     
    
    folder_path = "data/self_propelling/nabla_0-01"
    np.save(os.path.join(folder_path, "mean_vel.npy"), mean_vel_data)
    np.save(os.path.join(folder_path, "nabla.npy"), nabla_range)
    np.save(os.path.join(folder_path, "time.npy"), time_data)