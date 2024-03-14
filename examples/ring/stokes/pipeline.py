import time, os, yaml, shutil
import numpy as np
from enum import Enum, auto

from phystem.core.run_config import CollectDataCfg

from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState
from phystem.systems.ring.solvers import CppSolver

from phystem.utils import progress

class SaveType(Enum):
    checkpoint = auto()
    snapshot = auto()

class PipelineCfg:
    def __init__(self, checkpoint_period: float, snapshot_period: float, save_type: SaveType) -> None:
        self.checkpoint_period = checkpoint_period
        self.snapshot_period = snapshot_period
        self.save_type = save_type

class CollectorSnaps:
    def __init__(self, directory, solver, period) -> None:
        self.solver = solver

        self.count = -1    
        self.times = []    
        self.save_vel = False
        self.last_time = solver.time
        self.period = period

        self.dir = directory
        self.data_dir = os.path.join(self.dir, "data")
        self.time_path = os.path.join(self.dir, "time")
        self.metadata_path = os.path.join(self.dir, "metadata.yaml")

        self.pos_vel = None
        self.ids = None
        self.ring_ids = None

        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
            os.mkdir(self.data_dir)

    def save(self):
        pass
    
    def save_data(self):
        self.last_time = self.solver.time
        self.count += 1

        self.times.append(self.solver.time)
        pos_name, angle_name = f"pos_{self.snapshot_count}", f"angle_{self.snapshot_count}" 
        ids_name = f"ids_{self.snapshot_count}"
        super().save(pos_name, angle_name, ids_name, self.snaps_data_dir)
        
        pos_path = os.path.join(self.data_dir, pos_name + ".npy")
        angle_path = os.path.join(self.data_dir, angle_name + ".npy")
        ids_path = os.path.join(self.data_dir, ids_name + ".npy")

        ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        np.save(pos_path, np.array(self.solver.pos)[ring_ids])
        np.save(angle_path, np.array(self.solver.self_prop_angle)[ring_ids])
        np.save(ids_path, np.array(self.solver.unique_rings_ids)[ring_ids])

        
        times_path = os.path.join(self.snapshot_dir, "times.npy")
        np.save(times_path, np.array(self.snapshot_times))

        with open(self.snaps_metadata_path, "w") as f:
            yaml.dump({
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
                "count": self.snapshot_count,
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
    
    collector = Collector(solver, collect_cfg.folder_path, sim.configs, cfg.checkpoint_period, 
        cfg.snapshot_period, cfg.save_type)

    t1 = time.time()
    
    prog = progress.Continuos(collect_cfg.tf, solver.cpp_solver.sim_time)
    while solver.time < collect_cfg.tf:
        collector.save()
        solver.update()
        prog.update(solver.time)
    
    if cfg.save_type is SaveType.checkpoint:
        collector.save_checkpoint(is_finished=True)

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))
