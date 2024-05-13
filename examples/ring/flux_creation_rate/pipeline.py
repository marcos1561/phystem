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
        self.autosave_dir = os.path.join(path, "autosave")
        self.autosave_data_dir = os.path.join(self.autosave_dir, "data")

        if not os.path.exists(self.checkpoints_dir):
            os.mkdir(self.checkpoints_dir)
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        if not os.path.exists(self.autosave_dir):
            os.mkdir(self.autosave_dir)
        if not os.path.exists(self.autosave_data_dir):
            os.mkdir(self.autosave_data_dir)

        self.id = cfg["id"]

        self.wait_time_done = False

        self.last_autosave = self.solver.time
        self.autosave_dt = cfg["autosave_dt"]
        
        self.collect_dt = cfg["collect_dt"]
        self.last_time = self.solver.time
        self.point_id = 0

        self.num_points = int(cfg["collect_time"]/self.collect_dt)

        self.time_arr = np.zeros(self.num_points, dtype=np.float32)
        self.num_created_arr = np.zeros(self.num_points, dtype=np.int32)
        self.num_active_arr = np.zeros(self.num_points, dtype=np.int32)

        if collect_cfg.checkpoint is not None:
            metadata = collect_cfg.checkpoint.get_metadata()
            if metadata.get("is_autosave", False):
                self.load_autosave(metadata)

    def check_autosave(self):
        if self.solver.time - self.last_autosave > self.autosave_dt:
            self.last_autosave = self.solver.time
            self.autosave()

    def collect(self) -> None:
        # if count < self.num_points:
            # self.time_arr[count] = self.solver.time
            # self.num_created_arr[count] = self.solver.num_created_rings   
            # self.num_active_arr[count] = self.solver.num_active_rings   

        if self.point_id > self.num_points-1:
            return

        self.check_autosave()

        self.num_created_arr[self.point_id] += self.solver.num_created_rings   
        
        if self.solver.time - self.last_time > self.collect_dt:
            self.last_time = self.solver.time
            self.time_arr[self.point_id] = self.solver.time
            self.num_active_arr[self.point_id] = self.solver.num_active_rings   
            self.point_id += 1

    def save_checkpoint(self):
        path = os.path.join(self.checkpoints_dir, f"cp_{self.id}")
        
        if not os.path.exists(path):
            os.mkdir(path)

        cp_collector = LastState(self.solver, path, self.configs)
        cp_collector.save()

    def autosave(self):
        print("Auto-save: Salvando")

        metadata = {
            "is_autosave": True,
            "time": self.solver.time,
            "num_time_steps": self.solver.num_time_steps,
            "wait_time_done": self.wait_time_done,
            "point_id": self.point_id,
            "last_time": self.last_time,
            "flux_id": self.id,
        }

        if self.autosave_cfg.to_save_state:
            self.state_col.save(metadata={
                "is_autosave": True,
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            })

        LastState(self.solver, self.autosave_dir, self.configs).save(
            metadata=metadata
        )
        self.save(self.autosave_data_dir)

    def load_autosave(self, metadata):
        self.solver.cpp_solver.sim_time = metadata["time"]
        self.solver.cpp_solver.num_time_steps = metadata["num_time_steps"]
        self.wait_time_done = metadata["wait_time_done"]
        self.point_id = metadata["point_id"]
        self.last_time = metadata["last_time"]
        
        self.last_autosave = self.solver.time

        self.time_arr = np.load(os.path.join(self.autosave_data_dir, f"time_{self.id}.npy"))
        self.num_created_arr = np.load(os.path.join(self.autosave_data_dir, f"num_created_{self.id}.npy"))
        self.num_active_arr = np.load(os.path.join(self.autosave_data_dir, f"num_active_{self.id}.npy"))
        
    def save(self, dir=None):
        if dir is None:
            dir = self.data_dir

            import yaml
            metadata = {"num_points": self.point_id}
            with open(os.path.join(dir, "metadata.yaml"), "w") as f:
                yaml.dump(metadata, f)

        np.save(os.path.join(dir, f"time_{self.id}.npy"), self.time_arr)
        np.save(os.path.join(dir, f"num_created_{self.id}.npy"), self.num_created_arr)
        np.save(os.path.join(dir, f"num_active_{self.id}.npy"), self.num_active_arr)

def collect_pipeline(sim: Simulation, cfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    end_time = cfg["wait_time"] + cfg["collect_time"]
    
    print("\nIniciando simulação")
    t1 = time.time()

    collector = Collector(solver, collect_cfg.folder_path, sim.configs_container)

    prog = progress.Continuos(end_time)
    if not collector.wait_time_done:
        while solver.time < cfg["wait_time"]:
            solver.update()
            collector.check_autosave()
            prog.update(solver.time)
        collector.wait_time_done = True
        collector.save_checkpoint()
    
    print("\nTempo de espera finalizado")
    
    while solver.time < end_time:
        solver.update()
        collector.collect()
        prog.update(solver.time)

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

def main(configs, rng_seed=None):
    collect_cfg: CollectDataCfg = configs["run_cfg"]

    flux_range = collect_cfg.func_cfg["flux_range"]
    np.save(os.path.join(collect_cfg.folder_path, "flux.npy"), flux_range)
    
    init_id = 0
    if collect_cfg.checkpoint is not None:
        metadata = collect_cfg.checkpoint.get_metadata()
        if metadata.get("is_autosave", False):
            init_id = metadata["flux_id"] 

    # with multiprocessing.Pool(4) as p:
    #     args = [(i, configs, flux_range) for i in range(flux_range.size)]
    #     p.map(calc_flux, args)

    for id, flux in enumerate(flux_range):
        if id < init_id:
            continue

        configs["other_cfgs"]["stokes"].flux_force = float(flux)
        configs["run_cfg"].func_cfg["id"] = id
        sim = Simulation(**configs, rng_seed=rng_seed)
        sim.run()