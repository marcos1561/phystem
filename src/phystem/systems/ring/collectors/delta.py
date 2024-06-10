import pickle
import numpy as np
from enum import Flag, auto

from phystem.core.collectors import ColAutoSaveCfg
from phystem.systems.ring import collectors, utils

class State(Flag):
    starting = auto()
    waiting = auto()

class TrackingList:
    def __init__(self) -> None:
        self.ids: list[np.ndarray] = []
        self.uids: list[np.ndarray] = []
        self.end_x: list[float] = []
        self.dp_id: list[int] = []
        self.ids_region: list[np.ndarray] = []

    def id_exists(self, id):
        for ids in self.ids:
            if id in ids:
                return True
        return False

    def add(self, id, uid, end_x, dp_id, ids_region):
        self.ids.append(id)
        self.uids.append(uid)
        self.end_x.append(end_x)
        self.dp_id.append(dp_id)
        self.ids_region.append(ids_region)

    def remove(self, indexes):
        for index in sorted(indexes, reverse=True):
            del self.ids[index]
            del self.uids[index]
            del self.end_x[index]
            del self.dp_id[index]
            del self.ids_region[index]

    def get(self, name, idx):
        return getattr(self, name)[idx]

    @property
    def size(self):
        return len(self.ids)

class DeltaCol(collectors.RingCol):
    def __init__(self, wait_dist, xlims, start_dt, check_dt,
        solver, root_path: str, configs: dict,
        autosave_cfg: ColAutoSaveCfg=None,  
        xtol=1, save_final_close=False, to_load_autosave=False, exist_ok=False) -> None:
        '''Coletor da quantidade delta.
        
        Parâmetros:
            wait_dist:
                Distância no eixo x que o anel precisa andar para ter seu delta recalculado.
            
            xlims:
                Limites no eixo x que delimitam a região inicial, onde os anéis
                começam a ser rastreados.

            xtol:
                Comprimento (em unidades de diâmetro do anel) em que `xlims` é
                expandido.
                
            check_dt:
                Intervalo de tempo para chegar se os anéis monitorados percorreram a distância necessária.

            start_dt:
                Intervalo de tempo para tentar começar a coleta de um novo ponto experimental. 

        '''
        super().__init__(solver, root_path, configs, autosave_cfg, exist_ok=exist_ok)

        ##
        # Configuration
        ##
        self.wait_dist = wait_dist
        self.xlims = xlims
        self.start_dt = start_dt
        self.check_dt = check_dt
        self.xtol = xtol
        self.save_final_close = save_final_close

        self.ring_diameter = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        self.xlims_extended = (xlims[0] - xtol*self.ring_diameter, xlims[1] + xtol*self.ring_diameter)
        
        ##
        # State attributes
        ##
        self.data_point_id = 0
        self.last_start_time = self.solver.time
        self.last_check_time = self.solver.time
        self.state = State.starting 
        self.tracking = TrackingList()
        self.init_times = []
        self.final_times = []

        if to_load_autosave:
            self.load_autosave()

    @property
    def vars_to_save(self):
        return [
            "data_point_id",
            "last_start_time",
            "last_check_time",
            "state",
            "tracking",
            "init_times",
            "final_times",
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
                self.state = State.waiting

        if self.autosave_cfg:
            self.check_autosave()

    def start(self):
        cms = self.get_cm()

        active_ids, cms_active, uids_active = self.get_active(cms)

        in_region_mask = (cms_active[:, 0] > self.xlims_extended[0]) & (cms_active[:, 0] < self.xlims_extended[1])
        
        if in_region_mask.sum() == 0:
            return False

        cms_region = cms_active[in_region_mask]
        uids_region = uids_active[in_region_mask]
        ids_region = active_ids[in_region_mask]

        in_center_mask = (cms_region[:, 0] > self.xlims[0]) & (cms_region[:, 0] < self.xlims[1])
        if in_center_mask.sum() == 0:
            return False
        
        possible_new_ids = ids_region[in_center_mask]
        possible_new_uids = uids_region[in_center_mask]

        new_indexes = []
        for count, id in enumerate(possible_new_ids):
            if self.tracking.id_exists(id):
                continue
            new_indexes.append(count)

        selected_uids = possible_new_uids[new_indexes]
        if len(selected_uids) == 0:
            return False

        selected_ids = possible_new_ids[new_indexes]
        end_x = cms[selected_ids][:, 0].mean() + self.wait_dist
        
        self.tracking.add(
            id=selected_ids, 
            uid=selected_uids,
            end_x=end_x,
            dp_id=self.data_point_id,
            ids_region=ids_region,
        )
        
        np.save(self.data_path / f"cms_{self.data_point_id}_i.npy", cms_region)
        np.save(self.data_path / f"uids_{self.data_point_id}_i.npy", uids_region)
        np.save(self.data_path / f"selected-uids_{self.data_point_id}_i.npy", np.array(selected_uids))
        self.init_times.append(self.solver.time)
        # self.final_times.append({})

        self.data_point_id += 1
        
        with open(self.data_path / "metadata.pickle", "wb") as f:
            pickle.dump({"num_points": self.data_point_id}, f) 

        return True

    def check(self):
        idx_to_remove = []
        cms = self.get_cm()
        has_calc_active = False
        for idx in range(self.tracking.size):
            t_id, end_x = self.tracking.get("ids", idx), self.tracking.get("end_x", idx)
            current_cm = cms[t_id]
            
            if current_cm[:, 0].mean() < end_x:
                continue

            idx_to_remove.append(idx)
            uids = np.array(self.solver.unique_rings_ids)

            current_uids = self.tracking.get("uids", idx)
            current_dp_id = self.tracking.get("dp_id", idx)
            
            if self.save_final_close:
                if not has_calc_active:
                    _, cms_active, uids_active = self.get_active(cms, uids)
                    has_calc_active=True
                
                max_xdist = self.ring_diameter * 5
                close_mask = (cms_active[:, 0] > current_cm[0] - max_xdist) & (cms_active[:, 0] < current_cm[0] + max_xdist) 
                cms_close = cms_active[close_mask]
                uids_close = uids_active[close_mask]

                np.save(self.data_path / f"final-cms-close_{current_dp_id}_{current_uids}.npy", cms_close)
                np.save(self.data_path / f"final-uids-close_{current_dp_id}_{current_uids}.npy", uids_close)
            
            ids_region = self.tracking.get("ids_region", idx) 
            cms_region = cms[ids_region]
            udis_region = uids[ids_region]
            np.save(self.data_path / f"cms_{current_dp_id}_f.npy", cms_region)
            np.save(self.data_path / f"uids_{current_dp_id}_f.npy", udis_region)

            self.final_times.append(self.solver.time)

        self.tracking.remove(idx_to_remove)

    def save(self):
        np.save(self.data_path / "init_times.npy", np.array(self.init_times))
        np.save(self.data_path / "final_times.npy", np.array(self.final_times))
        
    def get_active(self, cm, uids=None):
        active_ids = np.array(self.solver.rings_ids[:self.solver.num_active_rings])
        cms_active = cm[active_ids]
        
        if uids is None:
            uids_active = np.array(self.solver.unique_rings_ids)[active_ids] 
        else:
            uids_active = uids[active_ids] 

        return active_ids, cms_active, uids_active

    def get_cm(self):
        return np.array(self.solver.center_mass) 

# class Debug:
#     def __init__(self, path, collector: DeltaCol) -> None:
#         self.root_path = Path(path) / "debug"

#         if not self.root_path.exists():
#             os.mkdir(self.root_path)

#         self.count = 0
#         self.collector = collector

#     def save_init(self, cm):
#         self.dir = self.root_path / f"point_{self.count}"
#         self.dir_state = self.dir / "state"

#         for d in [self.dir, self.dir_state]:
#             if not d.exists():
#                 os.mkdir(d)
        
#         self.save(cm, "i")
    
#     def save_finish(self, cm, deltas):
#         self.save(cm, "f")
#         np.save(self.dir/"deltas.npy", deltas)
#         np.save(self.dir/"in_center.npy", self.collector.in_center)
#         self.count += 1

#     def save(self, cm: np.ndarray, suffix):
#         dir_state = self.dir_state

#         cm_path = self.dir / f"cm_{self.count}_{suffix}.npy"
#         links_path = self.dir / f"links_{self.count}_{suffix}.npy"
        
#         rings_neighs = self.collector.rings_neighs
#         links = []
#         for idx in range(cm.shape[0]):
#             neighs_ids = rings_neighs.rings_neighs(idx)
#             neighs = cm[neighs_ids]
#             links.append(neighs)

#         np.save(cm_path, cm)
#         with open(links_path, "wb") as f:
#             pickle.dump(links, f)

#         cp_collector = LastState(self.collector.solver, dir_state, self.collector.configs)
#         cp_collector.save(
#             pos_name=f"pos_{suffix}",
#             angle_name=f"angle_{suffix}",
#             ids_name=f"ids_{suffix}",
#         )

