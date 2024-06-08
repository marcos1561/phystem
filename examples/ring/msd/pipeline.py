import os, time, yaml
import numpy as np

from phystem.core.run_config import CollectDataCfg
from phystem.systems.ring.simulation import Simulation

from phystem.systems.ring.collectors import LastState
from phystem.systems.ring.solvers import CppSolver

from phystem.utils import progress

class Collector(LastState):
    def __init__(self, solver: CppSolver, path: str, configs: list, dt: float) -> None:
        super().__init__(solver, path, configs)

        self.times = []
        self.dt = dt
        
        self.data_dir = os.path.join(self.path, "data")
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        self.init_time = self.solver.time
        self.count = -1

    def collect(self, count: int) -> None:
        if (self.solver.time - self.init_time) // self.dt != (self.count+1):
            return
        self.count += 1

        pos_file = f"pos_{self.count}"
        ids_file = f"ids_{self.count}"
        angle_file = f"angle_{self.count}"
        self.times.append(self.solver.time)

        super().save(pos_file, angle_file, ids_file, self.data_dir, continuos_ring=True)    

    def save(self) -> None:
        self.times = np.array(self.times)

        path = os.path.join(self.path, "times.npy")
        np.save(path, np.array(self.times))

        metadata = {"count": self.times.size}
        metadata_path = os.path.join(self.path, "metadata.yaml")
        with open(metadata_path, "w") as f:
            yaml.dump(metadata, f)

def collect_pipeline(sim: Simulation, cfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    collector = Collector(solver, collect_cfg.folder_path, sim.init_configs, cfg["dt"])

    t1 = time.time()

    tf = cfg["wait_time"] + cfg["collect_time"]    
    prog = progress.Continuos(tf, solver.cpp_solver.sim_time)
    
    if collect_cfg.checkpoint is None:
        while solver.time < cfg["wait_time"]:
            solver.update()
            prog.update(solver.time)
    
    print("Coletando Dodos..")
    collector.init_time = solver.time
    while solver.time < tf:
        solver.update()
        collector.collect(-1)
        prog.update(solver.time)
    collector.save()

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))


