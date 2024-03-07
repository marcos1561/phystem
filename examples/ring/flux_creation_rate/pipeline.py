import time, os
import numpy as np

from phystem.utils import progress
from phystem.core.run_config import CollectDataCfg
from phystem.core import collectors
from phystem.systems.ring.simulation import Simulation

class Collector(collectors.Collector):
    def __init__(self, solver: collectors.SolverCore, path: str, configs: dict) -> None:
        super().__init__(solver, path, configs)

        collect_cfg: CollectDataCfg = configs["run_cfg"]
        cfg = collect_cfg.func_cfg

        self.id = cfg["id"]

        self.num_points = int(cfg["collect_time"]/collect_cfg.int_cfg.dt)
        self.time_arr = np.zeros(self.num_points, dtype=np.float32)
        self.num_created_arr = np.zeros(self.num_points, dtype=np.int32)
        self.num_active_arr = np.zeros(self.num_points, dtype=np.int32)

    def collect(self, count: int) -> None:
        if count < self.num_points:
            self.time_arr[count] = self.solver.time
            self.num_created_arr[count] = self.solver.num_created_rings   
            self.num_active_arr[count] = self.solver.num_active_rings   

    def save(self):
        np.save(os.path.join(self.path, f"time_{self.id}.npy"), self.time_arr)
        np.save(os.path.join(self.path, f"num_created_{self.id}.npy"), self.num_created_arr)
        np.save(os.path.join(self.path, f"num_active_{self.id}.npy"), self.num_active_arr)

def collect_pipeline(sim: Simulation, cfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    end_time = cfg["wait_time"] + cfg["collect_time"]
    
    t1 = time.time()
    
    collector = Collector(solver, collect_cfg.folder_path, sim.configs_container)
    
    print("Iniciando simulação")
    prog = progress.Continuos(end_time)
    while solver.time < cfg["wait_time"]:
        solver.update()
        prog.update(solver.time)
    print("Tempo de espera finalizado")
    
    count = 0
    while solver.time < end_time:
        solver.update()
        collector.collect(count)
        prog.update(solver.time)
        count += 1

    t2 = time.time()
    
    collector.save()

    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))


def main(configs):
    collect_cfg: CollectDataCfg = configs["run_cfg"]

    flux_range = collect_cfg.func_cfg["flux_range"]
    np.save(os.path.join(collect_cfg.folder_path, "flux.npy"), flux_range)

    for id, flux in enumerate(flux_range):
        configs["other_cfgs"]["stokes"].flux_force = flux
        configs["run_cfg"].func_cfg["id"] = id
        sim = Simulation(**configs)
        sim.run()