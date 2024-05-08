import time, os, copy, pickle
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.utils import progress
from phystem.core.run_config import CollectDataCfg
from phystem.core import collectors
from phystem.systems.ring.simulation import Simulation
from phystem.systems.ring.collectors import LastState
from phystem.systems.ring import utils

class State(Flag):
    starting = auto()
    waiting = auto()

class Neighbors:
    def __init__(self, num_max_rings, num_max_neighs):
        self._rings_neighs = np.zeros((num_max_rings, num_max_neighs), dtype=int)
        self._dists = np.zeros((num_max_rings, num_max_neighs), dtype=np.float64)
        self.neigh_count = np.zeros(num_max_rings, dtype=int)

        self.row_mask = np.full(num_max_rings, False)
        self.num_rows = 0

    def rings_neighs(self, i):
        return self._rings_neighs[i][:self.neigh_count[i]]
    
    def dists(self, i):
        return self._dists[i][:self.neigh_count[i]]

    def update(self, i, neighs, dists):
        n = len(neighs)
        self._rings_neighs[i][:n] = neighs
        self._dists[i][:n] = dists
        self.neigh_count[i] = n
        
        self.row_mask[i] = True
        self.num_rows += 1

    def reset(self):
        self.num_rows = 0
        self.row_mask[:] = False

class Collector(collectors.Collector):
    def __init__(self, wait_time, xlims, edge_k, solver: collectors.SolverCore, path: str, configs: dict,
                 to_debug=False) -> None:
        super().__init__(solver, path, configs)

        self.data_path = Path(self.path) / "data"
        if not self.data_path.exists():
            os.mkdir(self.data_path)

        self.to_debug = to_debug    
        if to_debug:    
            self.debug = Debug(self.path, self)

        d = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        self.ring_d = d
        
        self.wait_time = wait_time
        self.xlims = xlims
        self.xlims_extended = (xlims[0] - 2*d, xlims[1] + 2*d)
        
        # self.xlims[0] = xlims[0] 
        # self.xlims[1] = xlims[1]
        
        self.state = State.starting 
        self.init_time = -1

        h = configs["space_cfg"].height
        w = self.xlims_extended[1] - self.xlims_extended[0]
        num_max_rings = int(h*w / (np.pi * (d/2)**2) * 2)
        num_max_neighs = 10
        self.rings_neighs = Neighbors(num_max_rings, num_max_neighs)
        self.mask: np.ndarray = None
        self.in_center: np.ndarray = None
        
        num_total_rings = np.array(self.solver.center_mass).shape[0]
        self.mask_active: np.ndarray = np.full(num_total_rings, False)

        self.edge_tol = d * edge_k
        self.deltas = []
        self.times = []

    def collect(self):
        if self.state is State.waiting:
            if self.solver.time - self.init_time > self.wait_time:
                self.finish()
                self.state = State.starting
            return
        
        if self.state is State.starting:
            if self.start():
                self.init_time = self.solver.time
                self.times.append(self.init_time)
                self.state = State.waiting

    def start(self):
        ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        
        self.mask_active[:] = False
        self.mask_active[ring_ids] = True

        cm = np.array(self.solver.center_mass)
        self.mask = (cm[:, 0] > self.xlims_extended[0]) & (cm[:, 0] < self.xlims_extended[1])
        self.mask = self.mask & self.mask_active

        cm = cm[self.mask]
        self.in_center = (cm[:, 0] > self.xlims[0]) & (cm[:, 0] < self.xlims[1])

        if not self.in_center.any():
            return False

        links, dists = utils.calc_edges(cm, self.edge_tol, return_dist=True)
        rings_links = utils.links_ids(links, cm.shape[0])
        neighbors = utils.neighbors_all(links, cm.shape[0])

        for i, neighs in enumerate(neighbors):
            self.rings_neighs.update(i, 
                neighs, 
                dists[rings_links[i]],                    
            )

        if self.to_debug:
            self.debug.save_init(cm)

        return True

    def finish(self):
        cm = np.array(self.solver.center_mass)[self.mask]
        delta_total = 0
        
        deltas_arr = np.zeros(self.in_center.sum(), dtype=np.float64)
        delta_id = 0

        for i in range(cm.shape[0]):
            if not self.in_center[i]:
                continue

            diff = cm[self.rings_neighs.rings_neighs(i)] - cm[i]
            dist_square = np.square(diff).sum(axis=1)

            r_sum = (np.square(self.rings_neighs.dists(i)) / dist_square).sum()

            deltas_arr[delta_id] = 1 - r_sum / self.rings_neighs.neigh_count[i] 
            delta_total += deltas_arr[delta_id]

            delta_id += 1
        
        self.deltas.append(delta_total/self.in_center.sum())
        self.rings_neighs.reset()

        if self.to_debug:
            self.debug.save_finish(cm, deltas_arr)

    def save(self):
        np.save(self.data_path / "times.npy", np.array(self.times))
        np.save(self.data_path / "deltas.npy", np.array(self.deltas))

class Debug:
    def __init__(self, path, collector: Collector) -> None:
        self.root_path = Path(path) / "debug"

        if not self.root_path.exists():
            os.mkdir(self.root_path)

        self.count = 0
        self.collector = collector

    def save_init(self, cm):
        self.dir = self.root_path / f"point_{self.count}"
        self.dir_state = self.dir / "state"

        for d in [self.dir, self.dir_state]:
            if not d.exists():
                os.mkdir(d)
        
        self.save(cm, "i")
    
    def save_finish(self, cm, deltas):
        self.save(cm, "f")
        np.save(self.dir/"deltas.npy", deltas)
        np.save(self.dir/"in_center.npy", self.collector.in_center)
        self.count += 1

    def save(self, cm: np.ndarray, suffix):
        dir_state = self.dir_state

        cm_path = self.dir / f"cm_{self.count}_{suffix}.npy"
        links_path = self.dir / f"links_{self.count}_{suffix}.npy"
        
        rings_neighs = self.collector.rings_neighs
        links = []
        for idx in range(cm.shape[0]):
            neighs_ids = rings_neighs.rings_neighs(idx)
            neighs = cm[neighs_ids]
            links.append(neighs)

        np.save(cm_path, cm)
        with open(links_path, "wb") as f:
            pickle.dump(links, f)

        cp_collector = LastState(self.collector.solver, dir_state, self.collector.configs)
        cp_collector.save(
            pos_name=f"pos_{suffix}",
            angle_name=f"angle_{suffix}",
            ids_name=f"ids_{suffix}",
        )


def collect_pipeline(sim: Simulation, cfg):
    collect_cfg: CollectDataCfg = sim.run_cfg
    solver = sim.solver
    
    print("\nIniciando simulação")
    t1 = time.time()

    collector = Collector(cfg["delta_wait_time"], cfg["xlims"], cfg["edge_k"],
        solver, collect_cfg.folder_path, sim.configs_container,
        to_debug=cfg["debug"])

    end_time = collect_cfg.tf
    prog = progress.Continuos(end_time)
    
    while solver.time < end_time:
        solver.update()
        collector.collect()
        prog.update(solver.time)

    collector.save()

    t2 = time.time()
    from datetime import timedelta
    print("Elapsed time:", timedelta(seconds=t2-t1))