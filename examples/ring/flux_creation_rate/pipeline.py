import time, os, multiprocessing, copy
import numpy as np

from phystem.utils import progress
from phystem.core.run_config import CollectDataCfg
from phystem.core import collectors
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState

class Collector(collectors.Collector):
    def __init__(self, solver: collectors.SolverCore, path: str, configs: dict) -> None:
        super().__init__(solver, path, configs)

        collect_cfg: CollectDataCfg = configs["run_cfg"]
        cfg = collect_cfg.func_cfg

        self.root_dir = path
        self.data_dir = os.path.join(path, "data")
        self.checkpoints_dir = os.path.join(path, "checkpoints")

        if not os.path.exists(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

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

    def save_checkpoint(self):
        path = os.path.join(self.checkpoints_dir, f"cp_{self.id}")
        
        if not os.path.exists(path):
            os.mkdir(path)

        cp_collector = LastState(self.solver, path, self.configs)
        cp_collector.save()

    def save(self):
        np.save(os.path.join(self.data_dir, f"time_{self.id}.npy"), self.time_arr)
        np.save(os.path.join(self.data_dir, f"num_created_{self.id}.npy"), self.num_created_arr)
        np.save(os.path.join(self.data_dir, f"num_active_{self.id}.npy"), self.num_active_arr)

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
    
    collector.save_checkpoint()

    count = 0
    while solver.time < end_time:
        solver.update()
        collector.collect(count)
        prog.update(solver.time)
        count += 1

    collector.save()

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))

def calc_flux(args):
    id = args[0]
    configs = args[1]
    flux_range = args[2]

    configs_copy = copy.deepcopy(configs)
    configs_copy["other_cfgs"]["stokes"].flux_force = flux_range[id]
    configs_copy["run_cfg"].func_cfg["id"] = id
    sim = Simulation(**configs_copy)
    sim.run()

def main(configs):
    collect_cfg: CollectDataCfg = configs["run_cfg"]

    flux_range = collect_cfg.func_cfg["flux_range"]
    np.save(os.path.join(collect_cfg.folder_path, "flux.npy"), flux_range)
    
    # with multiprocessing.Pool(4) as p:
    #     args = [(i, configs, flux_range) for i in range(flux_range.size)]
    #     p.map(calc_flux, args)

    for id, flux in enumerate(flux_range):
        configs["other_cfgs"]["stokes"].flux_force = float(flux)
        configs["run_cfg"].func_cfg["id"] = id
        sim = Simulation(**configs)
        sim.run()