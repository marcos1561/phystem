#pa
import os, pickle
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.core import collectors
from phystem.systems.ring.collectors import LastState, StateSaver
from phystem.systems.ring import utils
from phystem.utils.timer import TimerCount

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

class TrackingInfo:
    def __init__(self) -> None:
        self.ids = []
        self.uids = []
        self.end_x = []
        self.dp_id = []

    def add(self, id, uid, end_x, dp_id):
        self.ids.append(id)
        self.uids.append(uid)
        self.end_x.append(end_x)
        self.dp_id.append(dp_id)

    def remove(self, idx):
        self.ids.pop(idx)
        self.uids.pop(idx)
        self.end_x.pop(idx)
        self.dp_id.pop(idx)

    def get(self, name, idx):
        return getattr(name)[idx]

    @property
    def size(self):
        return len(self.ids)
    
class DeltaCol(collectors.Collector):
    save_name = "col_state.pickle"

    def __init__(self, wait_dist, xlims, start_dt, check_dt, solver: collectors.SolverCore, path: str, configs: dict,
        autosave_cfg: collectors.ColAutoSaveCfg=None,  to_debug=False) -> None:
        '''Coletor da quantidade delta.
        
        Parâmetros:
            wait_dist:
                Distância no eixo x que o anel precisa andar para ter seu delta recalculado.
            
            check_dt:
                Intervalo de tempo para chegar se os anéis monitorados percorreram a distância necessária.

            start_dt:
                Intervalo de tempo para tentar começar a coleta de um novo ponto experimental. 

        '''
        super().__init__(solver, path, configs, autosave_cfg)

        # Pasta onde são salvos os dados
        self.data_path = Path(self.path) / "data"
        for p in [self.data_path]:
            p.mkdir(exist_ok=True)


        self.to_debug = to_debug    
        if to_debug:    
            self.debug = Debug(self.path, self)

        self.ring_diameter = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        
        self.check_dt = check_dt
        self.start_dt = start_dt
        self.wait_dist = wait_dist
        self.xlims = xlims
        self.xlims_extended = (xlims[0] - 1*self.ring_diameter, xlims[1] + 1*self.ring_diameter)

        self.data_point_id = 0
        self.last_start_time = None
        self.last_check_time = None
        self.state = State.starting 
        self.tracking = TrackingInfo()
        self.times = []

        if autosave_cfg is not None:
            self.state_col = StateSaver(self.solver, self.autosave_state_path, configs)
            self.autosave_last_time = self.solver.time
            self.load_autosave()

    def vars_to_save(self):
        return [
            "data_point_id",
            "last_start_time",
            "last_check_time",
            "state",
            "tracking",
            "times",
        ]

    def collect(self):
        if self.state is State.waiting:
            if self.tracking.size == 0 or (self.solver.time > self.last_start_time + self.start_dt):
                self.state = State.starting
            else:
                if self.solver.time > self.last_check_time + self.check_dt:
                    self.last_check_time = self.solver.time
                    self.check()

        if self.state is State.starting:
            if self.start():
                self.last_start_time = self.solver.time
                self.times.append(self.last_start_time)
                self.state = State.waiting

    def start(self):
        cm = self.get_cm()

        active_ids, cm_active, uids_active = self.get_active(cm)

        in_region_mask = (cm_active[:, 0] > self.xlims_extended[0]) & (cm_active[:, 0] < self.xlims_extended[1])
        cm_region = cm_active[in_region_mask]
        uids_region = uids_active[in_region_mask]
        ids_region = active_ids[in_region_mask]

        in_center_mask = (cm_region[:, 0] > self.xlims[0]) & (cm_region[:, 0] < self.xlims[1])
        possible_new_ids = ids_region[in_center_mask]
        possible_new_uids = uids_region[in_center_mask]

        selected_uids = []
        for count, id in enumerate(possible_new_ids):
            if id not in self.tracking.ids:
                new_uid = possible_new_uids[count]
                
                self.tracking.add(
                    id=id, 
                    uid=new_uid,
                    end_x=cm[id, 0] + self.wait_dist,
                    dp_id=self.data_point_id,
                )
                selected_uids.append(new_uid)
                
        if len(selected_uids) == 0:
            return False
        
        np.save(self.data_path / f"cm_{self.data_point_id}_i.npy", cm_region)
        np.save(self.data_path / f"uids_{self.data_point_id}_i.npy", uids_region)
        np.save(self.data_path / f"selected_uids_{self.data_point_id}_i.npy", np.array(selected_uids))

        self.data_point_id += 1
        return True

    def check(self):
        idx_to_remove = []
        cm = self.get_cm()
        has_calc_active = False
        for idx in self.tracking.size:
            t_id, end_x = self.tracking.get("ids", idx), self.tracking.get("end_x", idx)
            current_cm = cm[t_id]
            if current_cm[0] < end_x:
                continue

            idx_to_remove.append(idx)
            
            if not has_calc_active:
                _, cm_active, uids_active = self.get_active(cm)
                has_calc_active=True

            max_xdist = self.ring_diameter * 5
            close_mask = (cm_active[:, 0] > current_cm[0] - max_xdist) & (cm_active[:, 0] < current_cm[0] + max_xdist) 

            cm_close = cm_active[close_mask]
            uids_close = uids_active[close_mask]
            
            current_uid = self.tracking.get("uids", idx)
            current_dp_id = self.tracking.get("dp_id", idx)
            np.save(self.data_path / f"cm_{current_dp_id}_{current_uid}.npy", cm_close)
            np.save(self.data_path / f"uids_{current_dp_id}_{current_uid}.npy", uids_close)

        for idx in idx_to_remove:
            self.tracking.remove(idx)

    def save(self):
        np.save(self.data_path / "times.npy", np.array(self.times))

    def get_active(self, cm):
        active_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        cm_active = cm[active_ids]
        uids_active = self.solver.unique_rings_ids[active_ids] 
        return active_ids, cm_active, uids_active

    def get_cm(self):
        return np.array(self.solver.center_mass) 

class DeltaColOld(collectors.Collector):
    save_name = "col_state.pickle"

    def __init__(self, wait_time, wait_dist, xlims, edge_k, 
        solver: collectors.SolverCore, path: str, configs: dict,
        autosave_cfg: collectors.ColAutoSaveCfg=None,  to_debug=False) -> None:
        '''Coletor da quantidade delta.
        
        Parâmetros:
            wait_time:
                Não use isso

            wait_dist:
                Distância no eixo x que o anel precisa andar para ter seu delta recalculado.
            
            edge_k:
                Defino o valor máximo do comprimento dos links entre anéis

                'valor máximo do link' := 'Diâmetro do anel' * 'edge_k'
        '''
        super().__init__(solver, path, configs, autosave_cfg)

        # Pasta onde são salvos os dados
        self.data_path = Path(self.path) / "data"
        for p in [self.data_path]:
            p.mkdir(exist_ok=True)

        self.data_names = {
            "times": "times.npy",
            "deltas": "deltas.npy"
        }

        self.data_point_id = 0

        if autosave_cfg is not None:
            self.state_col = StateSaver(self.solver, self.autosave_state_path, configs)
            self.autosave_last_time = self.solver.time

        self.to_debug = to_debug    
        if to_debug:    
            self.debug = Debug(self.path, self)

        self.ring_diameter = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        
        self.wait_time = wait_time
        self.wait_dist = wait_dist
        self.xlims = xlims
        self.xlims_extended = (xlims[0] - 1*self.ring_diameter, xlims[1] + 1*self.ring_diameter)
        
        self.tracking_ids = []
        self.tracking_uids = []

        # Valor máximo que o comprimento de um link pode ter
        self.edge_tol = self.ring_diameter * edge_k
        
        self.state = State.starting 
        self.init_time = -1

        h = configs["space_cfg"].height
        w = self.xlims_extended[1] - self.xlims_extended[0]
        num_max_rings = int(h*w / (np.pi * (self.ring_diameter/2)**2) * 1.5)
        num_max_neighs = 10
        self.rings_neighs = Neighbors(num_max_rings, num_max_neighs)
        
        self.mask: np.ndarray = None
        self.in_center: np.ndarray = None
        self.num_in_center: np.ndarray = None

        num_total_rings = np.array(self.solver.center_mass).shape[0]
        self.mask_active: np.ndarray = np.full(num_total_rings, False)

        self.end_x = np.zeros(num_max_rings, dtype=np.float64)
        self.delta_done = np.full(num_max_rings, False)

        self.tracking = TrackingInfo()

        self.deltas_arr = np.zeros(num_max_rings, dtype=np.float64)
        
        self.deltas = []
        self.times = []

        self.timer_count = TimerCount(["push_data"])

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

    def get_active(self, cm):
        active_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        cm_active = cm[active_ids]
        uids_active = self.solver.unique_rings_ids[active_ids] 
        return active_ids, cm_active, uids_active

    def start(self):
        ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        
        self.delta_done[:] = False
        self.mask_active[:] = False
        self.mask_active[ring_ids] = True

        cm = np.array(self.solver.center_mass)
        # cm = self.timer_count.update(
        #     lambda: np.array(self.solver.center_mass),
        #     "push_data",
        # )

        self.mask = (cm[:, 0] > self.xlims_extended[0]) & (cm[:, 0] < self.xlims_extended[1])
        self.mask = self.mask & self.mask_active

        cm = cm[self.mask]
        self.in_center = (cm[:, 0] > self.xlims[0]) & (cm[:, 0] < self.xlims[1])
        if not self.in_center.any():
            return False

        self.end_x[:cm.shape[0]] = cm[:, 0] + self.wait_dist

        links, dists = utils.calc_edges(cm, self.edge_tol, return_dist=True)
        rings_links = utils.links_ids(links, cm.shape[0])
        neighbors = utils.neighbors_all(links, cm.shape[0])
        
        for i, neighs in enumerate(neighbors):
            if len(neighs) == 0:
                self.in_center[i] = False
            
            self.rings_neighs.update(i, 
                neighs, 
                dists[rings_links[i]],                    
            )
        
        self.num_in_center = self.in_center.sum()
        if self.num_in_center == 0:
            return False

        if self.to_debug:
            self.debug.save_init(cm)

        return True

    def get_cm(self):
        return np.array(self.solver.center_mass) 

    def finish_dist(self):
        cm = self.get_cm()[self.mask]
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

