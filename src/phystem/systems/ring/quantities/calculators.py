import pickle
import numpy as np
from pathlib import Path
from abc import ABC, abstractmethod
from collections import namedtuple

from phystem.core import settings
from phystem.core.autosave import AutoSavable
from phystem.systems.ring import utils
from .datas import BaseData, DeltaData, DenVelData

class CalcAutoSaveCfg:
    def __init__(self, freq: int) -> None:
        self.freq = freq

class Calculator(AutoSavable, ABC):
    DataT: BaseData

    def __init__(self, data: BaseData, root_path: Path, autosave_cfg: CalcAutoSaveCfg=None, exist_ok=False) -> None:
        self.root_path = Path(root_path)
        if settings.IS_TESTING:
            self.root_path.mkdir(parents=True, exist_ok=True)
        else:
            self.root_path.mkdir(parents=True, exist_ok=exist_ok)

        super().__init__(root_path)
        self.autosave_cfg = autosave_cfg
        self.root_path = self.root_path.absolute().resolve()

        if type(data) != self.DataT:
            self.data = self.DataT(data)
        else:
            self.data = data

    @property
    def init_kwargs(self) -> dict[str]:
        '''Dicionário com os valores das configurações passadas
        no inicializador. Em subclasses, adicione novos items
        conforme necessário. Ex:

        ```
        values = super().init_kwargs 
        values[new_item_name] = self.new_value
        return value
        ```
        '''
        return {"data": self.data.root_path, "root_path": self.root_path}

    @abstractmethod
    def crunch_numbers(self):
        '''Calcula as quantidades relativas a esse calculador.
        Esse método deve ser capaz de continuar de um ponto salvo.
        '''
        pass

    def autosave(self):
        super().autosave()
        self.save_init_kwargs()

    def check_autosave(self, id):
        if id % self.autosave_cfg.freq == 0:
            self.exec_autosave()

    def save_init_kwargs(self):
        with open(self.autosave_root_path / "init_kwargs.pickle", "wb") as f:
            pickle.dump(self.init_kwargs, f)

    @staticmethod
    def load_init_kwargs(path: Path):
        with open(path / "init_kwargs.pickle", "rb") as f:
            kwargs = pickle.load(f)
        return kwargs

    @classmethod
    def from_checkpoint(cls, path: Path, autosave_cfg: CalcAutoSaveCfg=None):
        '''Carrega e retorna o checkpoint de um `Calculator` em `path` e passa 
        `autosave_cfg` para o mesmo.
        '''
        path = Path(path)
        obj = cls(**Calculator.load_init_kwargs(path), autosave_cfg=autosave_cfg)
        obj.load_autosave()
        return obj

class DeltaCalculator(Calculator):
    DataT = DeltaData

    def __init__(self, data: DeltaData, edge_k: float, 
        root_path: Path, autosave_cfg:CalcAutoSaveCfg=None, exist_ok=False,
        debug=False) -> None:
        '''Calcula o delta nos dados salvos em `path`.
        
        Parâmetros:
            edge_k:
                Define o valor máximo do comprimento dos links entre anéis

                'valor máximo do link' := 'Diâmetro do anel' * 'edge_k'
        '''
        super().__init__(data, root_path, autosave_cfg, exist_ok=exist_ok)
        self.data: DeltaData

        configs = self.data.configs
        ring_d = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        
        self.edge_k = edge_k
        self.debug = debug
        self.edge_tol = ring_d * self.edge_k

        self.current_id = 0
        self.deltas = []
        self.times = []

        if self.debug:
            self.debug_path = self.root_path / "debug"
            self.debug_path.mkdir(exist_ok=True)

    @property
    def vars_to_save(self):
        return [
            "current_id",
            "deltas",
            "times", 
        ]
    
    @property
    def init_kwargs(self):
        value = super().init_kwargs
        value["edge_k"] = self.edge_k
        return value

    def crunch_numbers(self, to_save=True, id_stop=None):
        for i in range(self.current_id, self.data.num_points_completed):
            if id_stop is not None and id_stop == i:
                break
            
            self.current_id = i
            pid = self.data.ids_completed[i]
            if pid >= self.data.init_times.size:
                continue

            if self.autosave_cfg:
                self.check_autosave(i)

            init_cms = self.data.init_cms[pid]

            if init_cms.shape[0] < 3:
                continue

            links, dists = utils.calc_edges(init_cms, self.edge_tol, return_dist=True)
            rings_links = utils.links_ids(links, init_cms.shape[0])
            neighbors = utils.neighbors_all(links, init_cms.shape[0])

            if self.debug:
                items = {
                    "links": links, "rings_links": rings_links, "neighbors": neighbors,
                }
                for name, value in items.items():
                    with open(self.debug_path / (name + f"_{i}" + ".pickle"), "wb") as f:
                        pickle.dump(value, f)

            init_uids = self.data.init_uids[pid]
            selected_ids = np.where(np.in1d(init_uids, self.data.init_selected_uids[pid]))[0]
            deltas = []
            for i in selected_ids:
                neighs = neighbors[i]
                if len(neighs) == 0:
                    continue
                
                final_cms = self.data.final_cms[pid]

                final_diffs = final_cms[neighs] - final_cms[i]
                final_dists_square = np.square(final_diffs).sum(axis=1)

                init_dists = dists[rings_links[i]]
                r_sum = (np.square(init_dists) / final_dists_square).sum()
                # delta = 1 - r_sum / len(neighs) 
                delta = r_sum / len(neighs) 
                
                deltas.append(delta)
            
            if len(deltas) > 0:
                self.deltas.append(sum(deltas)/len(deltas))
                self.times.append(self.data.init_times[pid])
        
        self.times = np.array(self.times)
        self.deltas = np.array(self.deltas)
        if to_save:
            np.save(self.root_path / "times.npy", self.times)
            np.save(self.root_path / "deltas.npy", self.deltas)

    @staticmethod
    def load_data(path: Path):
        path = Path(path)
        DeltaResults = namedtuple('DeltaResults', ['times', 'deltas'])

        times = np.load(path / "times.npy")
        deltas = np.load(path / "deltas.npy")
        return DeltaResults(times, deltas)
    
    @staticmethod
    def load_debug_data(path, id):
        names = ["links", "rings_links", "neighbors"]
        DebugDeltaData = namedtuple("DebugDeltaData", names)

        debug_path = Path(path) / "debug"
        items = {}
        for name in names:
            with open(debug_path / (name + f"_{id}.pickle"), "rb") as f:
                items[name] = pickle.load(f)

        return DebugDeltaData(**items)

class DenVelCalculator(Calculator):
    DataT = DenVelData

    def __init__(self, data: DenVelData, root_path: Path, autosave_cfg: CalcAutoSaveCfg=None, exist_ok=False) -> None:
        super().__init__(data, root_path, autosave_cfg, exist_ok=exist_ok)
        self.data: DenVelData

    def crunch_numbers(self, to_save=False):
        self.vel_order_par = self.calc_velocity_order_par()
        self.den_eq = self.calc_density_eq()

        if to_save:
            np.save(self.root_path / "vel_order_par.npy", self.vel_order_par)
            np.save(self.root_path / "vel_time.npy", self.data.vel_time)
            np.save(self.root_path / "den_eq.npy", self.den_eq)
            np.save(self.root_path / "den_time.npy", self.data.den_time)

    def calc_velocity_order_par(self):
        data = self.data

        vel_par_order = np.zeros(data.num_vel_points, dtype=float)
        for fid in range(0, data.vel_num_files):
            vels_cms = data.vel_data.get_file(fid)
            vels_cms.strip()

            vels = (vels_cms.data[:,:,2:] - vels_cms.data[:,:,:2])/data.vel_frame_dt
            speeds = np.sqrt((vels**2).sum(axis=2))

            is_zero_speed = speeds == 0
            speeds[is_zero_speed] = 1

            vels_norm = vels / speeds.reshape(vels.shape[0], -1, 1)
            vels_norm_mean = (vels_norm).sum(axis=1) / vels_cms.point_num_elements.reshape(-1, 1)
            vel_par_order_i = ((vels_norm_mean**2).sum(axis=1))**.5

            init_id = fid * data.num_data_points_per_file
            final_id = init_id + vels_cms.num_points
            vel_par_order[init_id: final_id] = vel_par_order_i

        return vel_par_order
    
    def calc_density_eq(self):
        data = self.data
        density_eq = np.zeros(data.num_den_points, dtype=float)
        for fid in range(0, data.den_num_files):
            den_cms = data.den_data.get_file(fid)
            den_cms.strip()
            
            density_eq_i = den_cms.point_num_elements / data.density_eq

            init_id = fid * data.num_data_points_per_file
            final_id = init_id + den_cms.num_points
            
            density_eq[init_id: final_id] = density_eq_i

        return density_eq

    @staticmethod
    def load_data(path: Path):
        DenResults = namedtuple('DenResults', ['times', 'den_eq'])
        VelResults = namedtuple('VelResults', ['times', 'vel_par'])

        vel_order_par = np.load(path / "vel_order_par.npy")
        vel_time = np.load(path / "vel_time.npy")
        den_eq = np.load(path / "den_eq.npy")
        den_time = np.load(path / "den_time.npy")

        return DenResults(den_time, den_eq), VelResults(vel_time, vel_order_par)
