import time, os, yaml
import numpy as np

from phystem.core.run_config import CollectDataCfg

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState
from phystem.systems.ring.solvers import CppSolver

from phystem.utils import progress

class PipelineCfg:
    def __init__(self, save_time_freq: int) -> None:
        self.save_time_freq = save_time_freq

class Collector(LastState):
    def __init__(self, solver: CppSolver, path: str, configs: list, save_time_freq: float) -> None:
        super().__init__(solver, path, configs)

        self.save_count = 0
        self.init_time = solver.time
        self.save_freq = save_time_freq

        self.last_invasion_path = os.path.join(path, "last_invasion.npy")
        self.metadata_path = os.path.join(path, "metadata.yaml")

    def save(self, is_finished=False) -> None:
        if not is_finished:
            if (self.solver.time - self.init_time) // self.save_freq != (self.save_count+1):
                return
            
        self.save_count += 1
        print(f"Salvando: {self.save_count}")

        super().save()
        
        n = self.solver.in_pol_checker.num_inside_points
        if n > 0:
            np.save(self.last_invasion_path, np.array(self.solver.in_pol_checker.inside_points[:n]))
        else:
            np.save(self.last_invasion_path, np.array([]))

        with open(self.metadata_path, "w") as f:
            yaml.dump({
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            }, f)

        
def collect_pipeline(sim: Simulation, cfg: PipelineCfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    
    solver = sim.solver
    
    if collect_cfg.checkpoint:
        path = os.path.join(collect_cfg.checkpoint.folder_path, "metadata.yaml")
        with open(path, "r") as f:
            metadata = yaml.unsafe_load(f)
        solver.cpp_solver.sim_time = metadata["time"] 
        solver.cpp_solver.num_time_steps = metadata["num_time_steps"] 
    
    collector = Collector(solver, collect_cfg.folder_path, sim.configs, cfg.save_time_freq)

    t1 = time.time()
    
    prog = progress.Continuos(collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        collector.save()
        solver.update()
        prog.update(solver.time)
    collector.save(is_finished=True)

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))
