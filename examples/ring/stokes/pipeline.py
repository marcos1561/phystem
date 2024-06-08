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

class Collector(LastState):
    def __init__(self, solver: CppSolver, path: str, configs: list, checkpoint_period: float,
        snapshot_period: float, save_type: SaveType) -> None:
        super().__init__(solver, path, configs)

        self.save_count = 0
        self.init_time = solver.time
        self.cp_period = checkpoint_period

        self.snapshot_count = -1    
        self.snapshot_times = []    
        self.snapshot_save_vel = False
        self.snapshot_last_time = solver.time
        self.snapshot_period = snapshot_period
        self.snaps_metadata = {}

        self.snapshot_dir = os.path.join(self.path, "snapshots")
        self.snaps_data_dir = os.path.join(self.snapshot_dir, "data")
        self.snaps_time_path = os.path.join(self.snapshot_dir, "time")
        self.snaps_metadata_path = os.path.join(self.snapshot_dir, "metadata.yaml")

        if not os.path.exists(self.snapshot_dir):
            os.mkdir(self.snapshot_dir)
            os.mkdir(self.snaps_data_dir)

        self.cp_dir = os.path.join(path, "checkpoint")
        self.last_invasion_path = os.path.join(self.cp_dir, "last_invasion.npy")
        self.cp_metadata_path = os.path.join(self.cp_dir, "metadata.yaml")
        
        if not os.path.exists(self.cp_dir):
            os.mkdir(self.cp_dir)

        self.save_type = save_type
        
        if self.save_type is SaveType.checkpoint:
            shutil.copy2(self.configs_path, self.cp_dir)
        elif self.save_type is SaveType.snapshot:
            shutil.copy2(self.configs_path, self.snapshot_dir)
        
        self.save_func = {
            SaveType.checkpoint: self.save_checkpoint,
            SaveType.snapshot: self.save_snapshots,
        }

    def save(self):
        self.save_func[self.save_type]()

    def save_snapshots(self):
        if self.snapshot_save_vel:
            self.snapshot_save_vel = False
            vel_path = os.path.join(self.snaps_data_dir, f"vel_{self.snapshot_count}")
            np.save(vel_path, np.array(self.solver.vel)[self.ring_ids])
            
            with open(self.snaps_metadata_path, "w") as f:
                yaml.dump(self.snaps_metadata, f)

        if (self.solver.time - self.snapshot_last_time) < self.snapshot_period:
            return
        
        self.snapshot_last_time = self.solver.time
        self.snapshot_count += 1
        self.snapshot_save_vel = True

        self.snapshot_times.append(self.solver.time)
        pos_name, angle_name = f"pos_{self.snapshot_count}", f"angle_{self.snapshot_count}" 
        ids_name = f"ids_{self.snapshot_count}"
        super().save(pos_name, angle_name, ids_name, self.snaps_data_dir)
        
        times_path = os.path.join(self.snapshot_dir, "times.npy")
        np.save(times_path, np.array(self.snapshot_times))

        # with open(self.snaps_metadata_path, "w") as f:
        #     yaml.dump({
        #         "time": self.solver.time,
        #         "num_time_steps": self.solver.num_time_steps,
        #         "count": self.snapshot_count,
        #     }, f)
        self.snaps_metadata = {
            "time": self.solver.time,
            "num_time_steps": self.solver.num_time_steps,
            "count": self.snapshot_count,
        }

    def save_checkpoint(self, is_finished=False):
        if not is_finished:
            if (self.solver.time - self.init_time) // self.cp_period != (self.save_count+1):
                return
        
        self.save_count += 1
        print(f"Salvando: {self.save_count}")

        super().save(directory=self.cp_dir)
        
        n = self.solver.in_pol_checker.num_inside_points
        if n > 0:
            np.save(self.last_invasion_path, np.array(self.solver.in_pol_checker.inside_points[:n]))
        else:
            np.save(self.last_invasion_path, np.array([]))

        with open(self.cp_metadata_path, "w") as f:
            yaml.dump({
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            }, f)

    def load_from_snapshot(self):
        with open(self.snaps_metadata_path, "r") as f:
            metadata = yaml.unsafe_load(f)
        self.snapshot_count = metadata["count"]
        self.frame = metadata["frame"]

def collect_pipeline(sim: Simulation, cfg: PipelineCfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    if collect_cfg.checkpoint:
        path = os.path.join(collect_cfg.checkpoint.folder_path, "metadata.yaml")
        with open(path, "r") as f:
            metadata = yaml.unsafe_load(f)
        solver.cpp_solver.sim_time = metadata["time"] 
        solver.cpp_solver.num_time_steps = metadata["num_time_steps"] 
    
    collector = Collector(solver, collect_cfg.folder_path, sim.init_configs, cfg.checkpoint_period, 
        cfg.snapshot_period, cfg.save_type)

    t1 = time.time()
    
    prog = progress.Continuos(collect_cfg.tf, solver.cpp_solver.sim_time)
    print(solver.time, collect_cfg.tf)
    while solver.time < collect_cfg.tf:
        collector.save()
        solver.update()
        prog.update(solver.time)
    
    if cfg.save_type is SaveType.checkpoint:
        collector.save_checkpoint(is_finished=True)

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))
