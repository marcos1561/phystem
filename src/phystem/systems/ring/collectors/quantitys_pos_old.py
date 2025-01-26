import numpy as np
from dataclasses import dataclass, field
from abc import abstractmethod, ABC
import pickle, yaml

from phystem.systems.ring.collectors import RingCol, ColAutoSaveCfg
from phystem.systems.ring.configs import RingCfg, SpaceCfg
from phystem.systems.ring.solvers import CppSolver

from phystem.data_utils.data_types import ArraySizeAware


@dataclass
class RootState:
    col_last_time: int
    times: list[float] = field(default_factory=list)

@dataclass
class QuantityState:
    data: ArraySizeAware
    file_id:int = 0

class BaseQuantityCfg(ABC):
    @property
    @abstractmethod
    def num_dims(self) -> int:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

class QuantityPosCfg:
    def __init__(self, wait_time: float, collect_dt, xlims, ylims, 
        quantities_cfg: list[BaseQuantityCfg], autosave_cfg: ColAutoSaveCfg=None, memory_per_file=10*1e6):
        self.wait_time = wait_time
        self.collect_dt = collect_dt
        self.xlims = xlims
        self.ylims = ylims
        self.memory_per_file = memory_per_file
        self.quantities_cfg = quantities_cfg
        self.autosave_cfg = autosave_cfg

class QuantityCol(ABC):
    StateT = QuantityState
    
    def __init__(self, configs: BaseQuantityCfg, base_state: RootState, base_configs: QuantityPosCfg, 
            solver: CppSolver, num_max_rings, data_path):
        self.solver = solver
        self.configs = configs
        self.base_state = base_state
        self.base_configs = base_configs
        self.data_path = data_path
        self.num_data_points_per_file = int(self.base_configs.memory_per_file / (num_max_rings * configs.num_dims * 4))

        self.metadata = {}

        self.state = self.StateT(self.create_data(num_max_rings))

        self.init_metadata(self.metadata)

    def init_metadata(self, metadata: dict):
        pass

    def before_save_metadata(self, metadata: dict):
        pass

    def create_data(self, num_max_rings):
        return ArraySizeAware(self.num_data_points_per_file, num_max_rings, self.configs.num_dims)

    def to_collect(self, time_dt: int, is_time: bool) -> bool:
        return is_time

    @abstractmethod
    def collect(self, ids_in_region, cms_in_region):
        pass

    def save_data(self):
        filename = f"{self.configs.name}_{self.state.file_id}"
        file_path = self.data_path / (filename + ".pickle")
        with open(file_path, "wb") as f:
            pickle.dump(self.state.data, f)
    
    def save(self):
        self.save_data()

        self.before_save_metadata(self.metadata)
        with open(self.data_path / f"{self.configs.name}_metadata.yaml", "w") as f:
            yaml.dump(self.metadata, f)

class QuantityPosCol(RingCol):
    solver: CppSolver

    def __init__(self, col_cfg: QuantityPosCfg, solver: CppSolver, root_path, configs, 
        exist_ok=False, **kwargs):
        super().__init__(solver, root_path, configs, col_cfg.autosave_cfg, exist_ok, **kwargs)
        self.col_cfg = col_cfg
        self.col_cfg.quantities_cfg.append(CmsCfg())

        dynamic_cfg: RingCfg = configs["dynamic_cfg"]
        space_cfg: SpaceCfg = configs["space_cfg"]
        
        area_eq = dynamic_cfg.get_equilibrium_area()
        
        xlims, ylims = col_cfg.xlims, col_cfg.ylims
        l = xlims[1] - xlims[0]
        h = ylims[1] - ylims[0]
        
        if l > space_cfg.length:
            l = space_cfg.length
        if h > space_cfg.height:
            h = space_cfg.height
        
        num_max_rings = int(l * h / area_eq * 1.2)
        
        self.state = RootState(self.solver.num_time_steps)
        
        self.quantities: list[QuantityCol] = [
            quantity_cfg_to_col[type(q_cfg)](q_cfg, self.state, self.col_cfg, self.solver, num_max_rings, self.data_path)
            for q_cfg in self.col_cfg.quantities_cfg
        ]

        self.quantities_states = [q.state for q in self.quantities]
        
    @property
    def vars_to_save(self):
        v = super().vars_to_save
        v.extend([ 
            "state",
            "quantities_states",
        ])
        return v
    
    @staticmethod
    def get_kwargs_configs(cfg: QuantityPosCfg):
        if type(cfg) is not QuantityPosCfg:
            raise ValueError(f"A configuração deve ser do tipo `QuantityPosCfg`, mas seu tipo é {type(cfg)}.")

        return {"col_cfg": cfg}

    def get_is_time(self):
        return self.solver.num_time_steps - self.state.col_last_time > self.col_cfg.collect_dt

    def cms_in_region(self):
        num_active = self.solver.num_active_rings
        ids_active = self.solver.rings_ids[:num_active]
        cms = self.solver.center_mass
        
        cms_active = cms[ids_active]
        
        mask_in_region = (cms_active[:, 0] > self.col_cfg.xlims[0]) & (cms_active[:, 0] < self.col_cfg.xlims[1])
        
        ids_in_region = ids_active[mask_in_region]
        cms_in_region = cms_active[mask_in_region]
        return ids_in_region, cms_in_region

    def collect(self):
        time_dt = self.solver.num_time_steps
        is_time = self.get_is_time()

        ids_in_region, cms_in_region = None, None
        if is_time:
            ids_in_region, cms_in_region = self.cms_in_region() 

        for q in self.quantities:
            if q.to_collect(time_dt, is_time):
                q.collect(ids_in_region, cms_in_region)
        
            if q.state.data.is_full:
                q.save_data()
                q.state.file_id += 1
                q.state.data.reset()

        if is_time:
            self.state.times.append(self.solver.time)
            self.state.col_last_time = time_dt

        if self.autosave_cfg:
            self.check_autosave()

    def save(self):
        for q in self.quantities:
            q.save()

        np.save(self.data_path / "times.npy", np.array(self.state.times))

    def load_autosave(self, use_backup=False):
        r = super().load_autosave(use_backup)
        
        for q, s in zip(self.quantities, self.quantities_states):
            q.state = s

        return r

class CmsCfg(BaseQuantityCfg):
    name = "cms"
    num_dims = 2

class CmsCol(QuantityCol):
    def collect(self, ids_in_region, cms_in_region):
        self.state.data.add(cms_in_region)


class VelocityCfg:
    name = "vel_cms"
    num_dims = 4
    def __init__(self, frame_dt):
        self.frame_dt = frame_dt

@dataclass
class VelState(QuantityState):
    vel_frame: int = 0
    vel_point_data: np.array = None
    vel_point_ids: np.array = None 

class VelocityCol(QuantityCol):
    configs: VelocityCfg
    state: VelState
    StateT = VelState

    def init_metadata(self, metadata):
        metadata["frame_dt"] = self.configs.frame_dt

    def before_save_metadata(self, metadata):
        metadata["last_point_completed"] = self.state.vel_frame == 0 

    def to_collect(self, time_dt: int, is_time: bool):
        if self.state.vel_frame == 0:
            return is_time

        return time_dt - self.base_state.col_last_time >= self.configs.frame_dt

    def collect(self, ids_in_region, cms_in_region):
        if self.state.vel_frame == 0:
            self.state.vel_point_ids = ids_in_region
            self.state.vel_point_data = np.empty((cms_in_region.shape[0], 4), dtype=self.state.data.data.dtype)
            self.state.vel_point_data[:,:2] = cms_in_region
        else:
            self.state.vel_point_data[:,2:] = self.solver.center_mass[self.state.vel_point_ids]
            self.state.data.add(self.state.vel_point_data)
        
        if self.state.vel_frame == 0:
            self.state.vel_frame = 1
        else:
            self.state.vel_frame = 0


class PolarityCfg:
    num_dims = 1


quantity_cfg_to_col = {
    VelocityCfg: VelocityCol,
    CmsCfg: CmsCol,
}