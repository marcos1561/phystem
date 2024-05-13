import os, pickle
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.core import collectors
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

class DeltaCol(collectors.Collector):
    save_name = "col_state.pickle"

    def __init__(self, wait_time, wait_dist, xlims, edge_k, 
        solver: collectors.SolverCore, path: str, configs: dict,
        autosave_cfg: collectors.AutoSaveCfg=None,  to_debug=False) -> None:
        super().__init__(solver, path, configs, autosave_cfg)

        self.data_path = Path(self.path) / "data"
        for p in [self.data_path]:
            p.mkdir(exist_ok=True)

        self.data_names = {
            "times": "times.npy",
            "deltas": "deltas.npy"
        }

        if autosave_cfg is not None:
            self.state_col = LastState(self.solver, self.autosave_path, self.configs)
            self.autosave_last_time = self.solver.time

        self.to_debug = to_debug    
        if to_debug:    
            self.debug = Debug(self.path, self)

        d = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        self.ring_d = d
        
        self.wait_time = wait_time
        self.wait_dist = wait_dist
        self.xlims = xlims
        self.xlims_extended = (xlims[0] - 2*d, xlims[1] + 2*d)
        
        self.edge_tol = d * edge_k
        
        self.state = State.starting 
        self.init_time = -1

        h = configs["space_cfg"].height
        w = self.xlims_extended[1] - self.xlims_extended[0]
        num_max_rings = int(h*w / (np.pi * (d/2)**2) * 2)
        num_max_neighs = 10
        self.rings_neighs = Neighbors(num_max_rings, num_max_neighs)
        
        self.mask: np.ndarray = None
        self.in_center: np.ndarray = None
        self.num_in_center: np.ndarray = None

        num_total_rings = np.array(self.solver.center_mass).shape[0]
        self.mask_active: np.ndarray = np.full(num_total_rings, False)

        self.end_x = np.zeros(num_max_rings, dtype=np.float64)
        self.delta_done = np.full(num_max_rings, False)

        self.deltas_arr = np.zeros(num_max_rings, dtype=np.float64)
        
        self.deltas = []
        self.times = []

    @property
    def vars_to_save(self):
        return [
            "state",
            "init_time",
            "rings_neighs",
            "mask",
            "in_center",
            "num_in_center",
            "mask_active",
            "end_x",
            "delta_done",
            "deltas_arr",
            "deltas",
            "times",
        ]

    def collect(self):
        if self.state is State.waiting:
            all_done = self.finish_dist()
            if all_done:
                self.rings_neighs.reset()
                self.state = State.starting
            return

            ### Time based
            # if self.solver.time - self.init_time > self.wait_time:
            #     self.finish()
            #     self.state = State.starting
            # return
        
        if self.state is State.starting:
            if self.start():
                self.init_time = self.solver.time
                self.times.append(self.init_time)
                self.state = State.waiting
        
        
    def start(self):
        ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        
        self.delta_done[:] = False
        self.mask_active[:] = False
        self.mask_active[ring_ids] = True

        cm = np.array(self.solver.center_mass)
        self.mask = (cm[:, 0] > self.xlims_extended[0]) & (cm[:, 0] < self.xlims_extended[1])
        self.mask = self.mask & self.mask_active

        cm = cm[self.mask]
        self.in_center = (cm[:, 0] > self.xlims[0]) & (cm[:, 0] < self.xlims[1])
        self.num_in_center = self.in_center.sum()

        self.end_x[:cm.shape[0]] = cm[:, 0] + self.wait_dist

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

    def finish_dist(self):
        cm = np.array(self.solver.center_mass)[self.mask]
        all_done = True
        delta_id = -1
        for i in range(cm.shape[0]):
            if not self.in_center[i]:
                continue
            delta_id += 1

            if self.delta_done[i]:
                continue
            
            if cm[i][0] < self.end_x[i]:
                all_done = False
                continue
            
            self.deltas_arr[delta_id] = self.calc_delta(cm, i)
            self.delta_done[i] = True
        
        if all_done:
            if self.to_debug:
                self.debug.save_finish(cm, self.deltas_arr[:self.num_in_center])

            self.deltas.append(self.deltas_arr[:self.num_in_center].sum()/self.num_in_center)

        return all_done
    
    def finish_time(self):
        cm = np.array(self.solver.center_mass)[self.mask]
        delta_total = 0
        
        delta_id = 0
        for i in range(cm.shape[0]):
            if not self.in_center[i]:
                continue
            
            delta_i = self.calc_delta(cm, i)
            self.deltas_arr[delta_id] = delta_i
            delta_total += delta_i
            delta_id += 1
        
        self.deltas.append(delta_total/self.num_in_center)
        self.rings_neighs.reset()

        if self.to_debug:
            self.debug.save_finish(cm, self.deltas_arr[:self.num_in_center])

    def calc_delta(self, cm, i):
        diff = cm[self.rings_neighs.rings_neighs(i)] - cm[i]
        dist_square = np.square(diff).sum(axis=1)

        r_sum = (np.square(self.rings_neighs.dists(i)) / dist_square).sum()

        delta = 1 - r_sum / self.rings_neighs.neigh_count[i] 
        return delta

    def save(self, dir=None):
        if dir is None:
            dir = self.data_path

        np.save(dir / self.data_names["times"], np.array(self.times))
        np.save(dir / self.data_names["deltas"], np.array(self.deltas))

class Debug:
    def __init__(self, path, collector: DeltaCol) -> None:
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

