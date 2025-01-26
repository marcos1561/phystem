import pickle
import numpy as np
from pathlib import Path
from abc import ABC, abstractmethod
from collections import namedtuple
import yaml

from shapely.geometry import Polygon, Point

from phystem.core import settings
from phystem.core.autosave import AutoSavable
from phystem.systems import ring
from phystem.systems.ring import utils
from .datas import *

class CalcAutoSaveCfg:
    def __init__(self, freq: int) -> None:
        self.freq = freq

class Calculator(AutoSavable, ABC):
    DataT: BaseData

    def __init__(self, data: BaseData, root_path: Path, autosave_cfg: CalcAutoSaveCfg=None, exist_ok=False) -> None:
        '''
        Base dos calculadores de quantidades.

        Parâmetros:
        -----------
        data:
            Objeto contendo os dados do cálculo ou o caminho onde esses dados estão.
        
        root_path:
            Caminho onde os resultados serão salvos.
        
        autosave_cfg:
            Configurações de auto-salvamento. Se for `None` não será feito auto-salvamentos.

        exist_ok:
            Parâmetro passado para as chamadas de `Path.mkdir()`.
        '''
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

        self.metadata = {}

        '''
        Dicionário com os valores das configurações passadas
        no inicializador. Em subclasses, adicione novos items
        conforme necessário. Ex:

        ```
        self.init_kwargs[new_item_name] = self.new_value
        ```
        '''
        self.init_kwargs = {
            "data": self.data.root_path,
            "root_path": self.root_path,
            "autosave_cfg": self.autosave_cfg,
        }

    # @property
    # def init_kwargs(self) -> dict[str]:
    #     '''
    #     Dicionário com os valores das configurações passadas
    #     no inicializador. Em subclasses, adicione novos items
    #     conforme necessário. Ex:

    #     ```
    #     values = super().init_kwargs 
    #     values[new_item_name] = self.new_value
    #     return value
    #     ```
    #     '''
    #     return {
    #         "data": self.data.root_path, 
    #         "root_path": self.root_path
    #     }

    @abstractmethod
    def calc_quantity(self):
        '''
        Calcula a quantidade em questão. Esse função deve ser capaz
        de iniciar a partir do ponto salvo.
        '''
        pass
    
    @abstractmethod
    def save_data(self):
        pass

    def crunch_numbers(self, to_save=True, **kwargs):
        '''
        Calcula as quantidades relativas a esse calculador.
        Método que de fato é chamado pelos usuários.
        '''
        if to_save:
            self.save_value("init_kwargs", self.init_kwargs)

        self.calc_quantity(**kwargs)

        if to_save:
            self.save_value("metadata", self.metadata)
            self.save_data()

    def check_autosave(self, id):
        if id % self.autosave_cfg.freq == 0:
            self.exec_autosave()

    def save_value(self, name, value):
        with open(self.root_path / f"{name}.yaml", "w") as f:
            yaml.dump(value, f)

    @staticmethod
    def load_init_kwargs(path: Path):
        with open(path / "init_kwargs.yaml", "rb") as f:
            kwargs = yaml.unsafe_load(f)
        return kwargs

    @classmethod
    def from_checkpoint(cls, path: Path, autosave_cfg: CalcAutoSaveCfg=None):
        '''
        Carrega e retorna o checkpoint de um `Calculator` em `path` e passa 
        `autosave_cfg` para o mesmo.
        '''
        path = Path(path)

        init_kwargs = Calculator.load_init_kwargs(path)
        if autosave_cfg is not None:
            init_kwargs["autosave_cfg"] = autosave_cfg

        obj = cls(**init_kwargs)
        obj.load_autosave()
        return obj

class DeltaCalculator(Calculator):
    DataT = DeltaData

    def __init__(self, data: DeltaData, edge_k: float, 
        root_path: Path, autosave_cfg:CalcAutoSaveCfg=None, exist_ok=False,
        debug=False) -> None:
        '''
        Calcula o delta nos dados salvos em `path`.
        
        Parâmetros:
            edge_k:
                Define o valor máximo do comprimento dos links entre anéis

                'valor máximo do link' := 'Diâmetro do anel' * 'edge_k'
        '''
        super().__init__(data, root_path, autosave_cfg, exist_ok=exist_ok)
        self.data: DeltaData

        configs = self.data.configs
        ring_d = utils.ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_particles) * 2
        
        self.edge_k = edge_k
        self.debug = debug
        self.edge_tol = ring_d * self.edge_k

        self.current_id = 0
        self.deltas = []
        self.times = []

        if self.debug:
            self.debug_path = self.root_path / "debug"
            self.debug_path.mkdir(exist_ok=True)

        self.init_kwargs["edge_k"] = self.edge_k
    
    @property
    def vars_to_save(self):
        return [
            "current_id",
            "deltas",
            "times", 
        ]
    
    # @property
    # def init_kwargs(self):
    #     value = super().init_kwargs
    #     value["edge_k"] = self.edge_k
    #     return value

    def calc_quantity(self, id_stop=None):
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

    def save_data(self):
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
    data: DenVelData
    # def __init__(self, data: DenVelData, root_path: Path, autosave_cfg: CalcAutoSaveCfg=None, exist_ok=False) -> None:
    #     super().__init__(data, root_path, autosave_cfg, exist_ok=exist_ok)
    #     self.data: DenVelData

    def calc_quantity(self):
        self.vel_order_par = self.calc_velocity_order_par()
        self.den_eq = self.calc_density_eq()

    def save_data(self):
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

            init_id = fid * data.total_num_data_points_per_file
            final_id = init_id + vels_cms.num_points
            vel_par_order[init_id: final_id] = vel_par_order_i

        return vel_par_order
    
    def calc_density_eq(self):
        data = self.data
        density_eq = np.zeros(data.num_den_points, dtype=float)
        for fid in range(0, data.den_num_files):
            den_cms = data.den_data.get_file(fid)
            den_cms.strip()
            
            density_eq_i = den_cms.point_num_elements / data.density_eq - 1

            init_id = fid * data.total_num_data_points_per_file
            final_id = init_id + den_cms.num_points
            
            density_eq[init_id: final_id] = density_eq_i

        return density_eq

    @staticmethod
    def load_data(path: Path):
        path = Path(path)

        DenResults = namedtuple('DenResults', ['times', 'den_eq'])
        VelResults = namedtuple('VelResults', ['times', 'vel_par'])

        vel_order_par = np.load(path / "vel_order_par.npy")
        vel_time = np.load(path / "vel_time.npy")
        den_eq = np.load(path / "den_eq.npy")
        den_time = np.load(path / "den_time.npy")

        return DenResults(den_time, den_eq), VelResults(vel_time, vel_order_par)


class VelocityCalculator(Calculator):
    DataT = VelData
    data: VelData

    def __init__(self, data: VelData, root_path: Path, grid: utils.RegularGrid, autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(data, root_path, autosave_cfg, exist_ok)
        self.grid = grid

        self.cell_vel_mean = np.zeros((*self.grid.shape_mpl_t, 2), dtype=float)
        self.num_points = 0
        self.next_file_id = 0

        self.grid.save_configs(self.root_path / "grid_configs.yaml")

        self.init_kwargs["grid"] = grid

    def calc_quantity(self):
        data = self.data
        cms_vel_data = data.vel
        while self.next_file_id < cms_vel_data.num_files:
            vels_cms = cms_vel_data.get_file(self.next_file_id)
            vels_cms.strip()

            cms1 = vels_cms.data[:,:,:2]
            cms2 = vels_cms.data[:,:,2:]
            vels = (cms2 - cms1)/data.frame_dt
            
            coords = self.grid.coords(cms1)
            
            if vels.shape[0] == 1:
                vels = self.grid.simplify_shape(vels)
            
            cell_vel = self.grid.mean_by_cell(vels, coords, end_id=vels_cms.point_num_elements)

            self.cell_vel_mean += cell_vel.sum(axis=0)
            self.num_points += cell_vel.shape[0]
            self.next_file_id += 1

        self.cell_vel_mean = self.grid.remove_cells_out_of_bounds(self.cell_vel_mean)
        self.cell_vel_mean /= self.num_points
        self.metadata["num_points"] = self.num_points

    def save_data(self):
        np.save(self.root_path / "vels.npy", self.cell_vel_mean)

    @staticmethod
    def load_data(path):
        path = Path(path)
        
        class VelResults:
            def __init__(self, grid: utils.RegularGrid, cell_vel: np.ndarray, metadata: dict) -> None:
                self.grid = grid
                self.cell_vel = cell_vel
                self.metadata = metadata  

        grid = utils.RegularGrid.load(path / "grid_configs.yaml")
        cell_vel = np.load(path / "vels.npy")
        
        with open(path / "metadata.yaml") as f:
            metadata = yaml.unsafe_load(f)

        return VelResults(grid, cell_vel, metadata)

# class VelocityCalculator(Calculator):
#     DataT = DenVelData
#     data: DenVelData

#     def __init__(self, data: DenVelData, root_path: Path, grid: utils.RegularGrid, autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
#         super().__init__(data, root_path, autosave_cfg, exist_ok)
#         self.grid = grid

#         self.cell_vel_mean = np.zeros((*self.grid.shape_mpl_t, 2), dtype=float)
#         self.num_points = 0
#         self.next_file_id = 0

#         self.grid.save_configs(self.root_path / "grid_configs.yaml")

#         self.init_kwargs["grid"] = grid

#     def calc_quantity(self):
#         data = self.data
#         cms_vel_data = data.vel_data
#         while self.next_file_id < data.vel_num_files:
#             vels_cms = cms_vel_data.get_file(self.next_file_id)
#             vels_cms.strip()

#             cms1 = vels_cms.data[:,:,:2]
#             cms2 = vels_cms.data[:,:,2:]
#             vels = (cms2 - cms1)/data.vel_frame_dt
            
#             coords = self.grid.coords(cms1)
            
#             if vels.shape[0] == 1:
#                 vels = self.grid.simplify_shape(vels)
            
#             cell_vel = self.grid.mean_by_cell(vels, coords, end_id=vels_cms.point_num_elements)

#             self.cell_vel_mean += cell_vel.sum(axis=0)
#             self.num_points += cell_vel.shape[0]
#             self.next_file_id += 1

#         self.cell_vel_mean = self.grid.remove_cells_out_of_bounds(self.cell_vel_mean)
#         self.cell_vel_mean /= self.num_points
#         self.metadata["num_points"] = self.num_points

#     def save_data(self):
#         np.save(self.root_path / "vels.npy", self.cell_vel_mean)

#     @staticmethod
#     def load_data(path):
#         path = Path(path)
        
#         class VelResults:
#             def __init__(self, grid: utils.RegularGrid, cell_vel: np.ndarray, metadata: dict) -> None:
#                 self.grid = grid
#                 self.cell_vel = cell_vel
#                 self.metadata = metadata  

#         grid = utils.RegularGrid.load(path / "grid_configs.yaml")
#         cell_vel = np.load(path / "vels.npy")
        
#         with open(path / "metadata.yaml") as f:
#             metadata = yaml.unsafe_load(f)

#         return VelResults(grid, cell_vel, metadata)


class DensityCalculator(Calculator):
    DataT = CmsData
    data: CmsData

    def __init__(self, data: CmsData, root_path: Path,
        grid: utils.RegularGrid, den_eq: float=None,
        autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(data, root_path, autosave_cfg, exist_ok)
        self.grid = grid
        self.den_eq = den_eq

        self.sim_configs = ring.run_config.load_configs(self.data.root_path / settings.system_config_fname)
        self.stokes_cfg: ring.configs.StokesCfg = self.sim_configs["other_cfgs"].get("stokes", None)

        self.cell_den_mean = np.zeros(self.grid.shape_mpl_t, dtype=float)
        self.num_points = 0
        self.next_file_id = 0

        self.grid.save_configs(self.root_path / "grid_configs.yaml")
        
        self.init_kwargs["grid"] = self.grid
        self.init_kwargs["den_eq"] = self.den_eq

    def calc_quantity(self):
        while self.next_file_id < self.data.cms.num_files:
            cms = self.data.cms.get_file(self.next_file_id)
            cms.strip()

            coords = self.grid.coords(cms.data)
            count = self.grid.count(coords, end_id=cms.point_num_elements)

            self.cell_den_mean += count.sum(axis=0)
            self.num_points += count.shape[0]
            self.next_file_id += 1

        self.cell_den_mean = self.grid.remove_cells_out_of_bounds(self.cell_den_mean)
        self.cell_den_mean /= self.num_points

        if self.den_eq is not None:
            den_eq = self.grid.cell_area * self.den_eq 
            self.cell_den_mean = self.cell_den_mean / den_eq - 1
        else:
            if self.stokes_cfg is None:
                self.cell_den_mean /= self.grid.cell_area
            else:
                obs_center = (self.stokes_cfg.obstacle_x, self.stokes_cfg.obstacle_x)
                obs_r = self.stokes_cfg.obstacle_r
                intersect_mask = self.grid.circle_mask(
                    radius=self.stokes_cfg.obstacle_r,
                    center=obs_center,
                    mode="intersect",
                )

                x = self.grid.meshgrid[0][intersect_mask] 
                y = self.grid.meshgrid[1][intersect_mask] 
                
                dx = self.grid.cell_size[0]/2
                dy = self.grid.cell_size[1]/2

                p1 = np.array([x + dx, y - dy]).T
                p2 = np.array([x + dx, y + dy]).T
                p3 = np.array([x - dx, y + dy]).T
                p4 = np.array([x - dx, y - dy]).T

                intersect_areas = []
                for idx in range(p1.shape[0]):
                    square = Polygon([p1[idx], p2[idx], p3[idx], p4[idx]])
                    circle = Point(obs_center).buffer(obs_r, resolution=100)
                    area = square.difference(circle).area
                    intersect_areas.append(area)

                cell_areas = np.full_like(self.cell_den_mean, self.grid.cell_area)
                cell_areas[intersect_mask] = intersect_areas

                self.cell_den_mean /= cell_areas

        self.metadata["num_points"] = self.num_points
        self.metadata["den_eq"] = self.den_eq
    
    def save_data(self):
        np.save(self.root_path / "den.npy", self.cell_den_mean)

    @staticmethod
    def load_data(path):
        path = Path(path)
        
        class DenResults:
            def __init__(self, grid: utils.RegularGrid, cell_den: np.ndarray, metadata: dict) -> None:
                self.grid = grid
                self.cell_den = cell_den
                self.metadata = metadata  

        grid = utils.RegularGrid.load(path / "grid_configs.yaml")
        cell_vel = np.load(path / "den.npy")
        
        with open(path / "metadata.yaml") as f:
            metadata = yaml.unsafe_load(f)

        return DenResults(grid, cell_vel, metadata)

# class DensityCalculator(Calculator):
#     DataT = DenVelData
#     data: DenVelData

#     def __init__(self, data: DenVelData, root_path: Path,
#         grid: utils.RegularGrid, den_eq: float=None,
#         autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
#         super().__init__(data, root_path, autosave_cfg, exist_ok)
#         self.grid = grid
#         self.den_eq = den_eq

#         self.sim_configs = ring.run_config.load_configs(self.data.root_path / settings.system_config_fname)
#         self.stokes_cfg: ring.configs.StokesCfg = self.sim_configs["other_cfgs"].get("stokes", None)

#         self.cell_den_mean = np.zeros(self.grid.shape_mpl_t, dtype=float)
#         self.num_points = 0
#         self.next_file_id = 0

#         self.grid.save_configs(self.root_path / "grid_configs.yaml")
        
#         self.init_kwargs["grid"] = self.grid
#         self.init_kwargs["den_eq"] = self.den_eq

#     def calc_quantity(self):
#         data = self.data
#         cms_vel_data = data.vel_data
#         while self.next_file_id < data.vel_num_files:
#             vels_cms = cms_vel_data.get_file(self.next_file_id)
#             vels_cms.strip()

#             cms = vels_cms.data[:,:,:2]
#             coords = self.grid.coords(cms)
#             count = self.grid.count(coords, end_id=vels_cms.point_num_elements)

#             self.cell_den_mean += count.sum(axis=0)
#             self.num_points += count.shape[0]
#             self.next_file_id += 1

#         self.cell_den_mean = self.grid.remove_cells_out_of_bounds(self.cell_den_mean)
#         self.cell_den_mean /= self.num_points

#         if self.den_eq is not None:
#             den_eq = self.grid.cell_area * self.den_eq 
#             self.cell_den_mean = self.cell_den_mean / den_eq - 1
#         else:
#             if self.stokes_cfg is None:
#                 self.cell_den_mean /= self.grid.cell_area
#             else:
#                 obs_center = (self.stokes_cfg.obstacle_x, self.stokes_cfg.obstacle_x)
#                 obs_r = self.stokes_cfg.obstacle_r
#                 intersect_mask = self.grid.circle_mask(
#                     radius=self.stokes_cfg.obstacle_r,
#                     center=obs_center,
#                     mode="intersect",
#                 )

#                 x = self.grid.meshgrid[0][intersect_mask] 
#                 y = self.grid.meshgrid[1][intersect_mask] 
                
#                 dx = self.grid.cell_size[0]/2
#                 dy = self.grid.cell_size[1]/2

#                 p1 = np.array([x + dx, y - dy]).T
#                 p2 = np.array([x + dx, y + dy]).T
#                 p3 = np.array([x - dx, y + dy]).T
#                 p4 = np.array([x - dx, y - dy]).T

#                 intersect_areas = []
#                 for idx in range(p1.shape[0]):
#                     square = Polygon([p1[idx], p2[idx], p3[idx], p4[idx]])
#                     circle = Point(obs_center).buffer(obs_r, resolution=100)
#                     area = square.difference(circle).area
#                     intersect_areas.append(area)

#                 cell_areas = np.full_like(self.cell_den_mean, self.grid.cell_area)
#                 cell_areas[intersect_mask] = intersect_areas

#                 self.cell_den_mean /= cell_areas

#         self.metadata["num_points"] = self.num_points,
#         self.metadata["den_eq"] = self.den_eq,
    
#     def save_data(self):
#         np.save(self.root_path / "den.npy", self.cell_den_mean)

#     @staticmethod
#     def load_data(path):
#         path = Path(path)
        
#         class DenResults:
#             def __init__(self, grid: utils.RegularGrid, cell_den: np.ndarray, metadata: dict) -> None:
#                 self.grid = grid
#                 self.cell_den = cell_den
#                 self.metadata = metadata  

#         grid = utils.RegularGrid.load(path / "grid_configs.yaml")
#         cell_vel = np.load(path / "den.npy")
        
#         with open(path / "metadata.yaml") as f:
#             metadata = yaml.unsafe_load(f)

#         return DenResults(grid, cell_vel, metadata)
    

class PolarityCalculator(Calculator):
    DataT = PolData
    data: PolData

    def __init__(self, data: PolData, root_path: Path,
        grid: utils.RegularGrid,
        autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(data, root_path, autosave_cfg, exist_ok)
        self.grid = grid

        self.cell_pol_mean: np.ndarray = None

        self.cell_pol_sum = np.zeros(*self.grid.shape_mpl, dtype=float)
        self.num_points = 0
        self.next_file_id = 0

        self.grid.save_configs(self.root_path / "grid_configs.yaml")
        
        self.init_kwargs["grid"] = self.grid

    def calc_quantity(self):
        data = self.data
        while self.next_file_id < data.pol_data.num_files:
            pols = data.pol_data.get_file(self.next_file_id).strip()
            cms = data.cms_data.get_file(self.next_file_id).strip()

            coords = self.grid.coords(cms)

            cell_pol = self.grid.mean_by_cell(pols.data, coords, end_id=cms.point_num_elements)
            self.cell_pol_sum += cell_pol.sum(axis=0)
            self.num_points += cell_pol.shape[0]
            self.next_file_id += 1

        self.cell_pol_mean = self.cell_pol_sum /  self.num_points
        self.metadata["num_points"] = self.num_points

    def save_data(self):
        np.save(self.root_path / "pol.npy", self.cell_den_mean)

    @staticmethod
    def load_data(path):
        path = Path(path)
        
        class PolResults:
            def __init__(self, grid: utils.RegularGrid, cell_pol: np.ndarray, metadata: dict) -> None:
                self.grid = grid
                self.cell_pol = cell_pol
                self.metadata = metadata  

        grid = utils.RegularGrid.load(path / "grid_configs.yaml")
        cell_vel = np.load(path / "pol.npy")
        
        with open(path / "metadata.yaml") as f:
            metadata = yaml.unsafe_load(f)

        return PolResults(grid, cell_vel, metadata)
    
class TextureCalc(Calculator):
    DataT = DenVelData
    data: DenVelData

    def __init__(self, data: DenVelData, root_path: Path, 
        grid, ring_diameter: float, 
        edge_k=1.4,
        autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
        super().__init__(data, root_path, autosave_cfg, exist_ok)
        self.grid = grid
        self.ring_diameter = ring_diameter
        self.edge_k = edge_k

        self.cell_texture_sum = np.zeros(grid.shape+(3,), dtype=np.float64)
        self.cell_count = np.zeros(grid.shape, np.int64)
        self.num_points = 0
        self.current_id = 0

        self.grid.save_configs(self.root_path / "grid_configs.yaml")

        self.init_kwargs["grid"] = self.grid
        self.init_kwargs["ring_diameter"] = self.ring_diameter
        self.init_kwargs["edge_k"] = self.edge_k

    def calc_quantity(self):
        import texture

        data = self.data
        cms_vel_data = data.vel_data
        
        for idx in range(self.current_id, len(cms_vel_data)):
            cms = cms_vel_data[idx][:, :2]
            edges = utils.calc_edges(cms, self.ring_diameter, self.edge_k)

            sumw, count = texture.texture.bin_texture(cms, edges, self.grid)
            self.cell_texture_sum += sumw
            self.cell_count += count

        cell_count_non_zero = np.maximum(1, self.cell_count)
        self.texture_mean = self.cell_texture_sum / cell_count_non_zero[..., None]
        self.metadata["num_points"] = len(cms_vel_data)

    def save_data(self):
        np.save(self.root_path / "texture.npy", self.texture_mean)
    
    @staticmethod
    def load_data(path):
        path = Path(path)
        
        class TextureResults:
            def __init__(self, grid: utils.RegularGrid, texture: np.ndarray, metadata: dict) -> None:
                self.grid = grid
                self.texture = texture
                self.metadata = metadata  

        import texture
        grid = texture.grid.GridWrapper.load(path / "grid_configs.yaml")
        texture = np.load(path / "texture.npy")
        
        with open(path / "metadata.yaml") as f:
            metadata = yaml.unsafe_load(f)

        return TextureResults(grid, texture, metadata)

class AreaCalculator(Calculator):
    DataT = AreaData
    data: AreaData

    def __init__(self, data: AreaData, root_path: Path,
        grid: utils.RegularGrid, start_id=0,
        autosave_cfg: CalcAutoSaveCfg = None, exist_ok=False) -> None:
        "Calcula a área média dos anéis dentro das células da grade `grid`."
        super().__init__(data, root_path, autosave_cfg, exist_ok)
        self.grid = grid

        self.next_frame_id = 0
        self.num_points = start_id
        self.cell_area_mean = np.zeros(self.grid.shape_mpl_t, dtype=float)
        
        self.grid.save_configs(self.root_path / "grid_configs.yaml")

        self.init_kwargs["grid"] = grid
        self.init_kwargs["start_id"] = start_id

    def calc_quantity(self):
        for idx in range(self.num_points, len(self.data.areas)):
            areas = self.data.areas[idx]
            cms = self.data.pos[idx]
            
            coords = self.grid.coords(cms, simplify_shape=True)
            cell_area = self.grid.mean_by_cell(areas, coords, simplify_shape=True)

            self.cell_area_mean += cell_area
            self.num_points += 1
            self.next_frame_id += 1

        self.cell_area_mean = self.grid.remove_cells_out_of_bounds(self.cell_area_mean)
        self.cell_area_mean /= self.num_points
        self.metadata["num_points"] = self.num_points

    def save_data(self):
        np.save(self.root_path / "areas.npy", self.cell_area_mean)
    
    @staticmethod
    def load_data(path):
        path = Path(path)
        
        class AreaResults:
            def __init__(self, grid: utils.RegularGrid, cell_area: np.ndarray, metadata: dict) -> None:
                self.grid = grid
                self.cell_area = cell_area
                self.metadata = metadata  

        grid = utils.RegularGrid.load(path / "grid_configs.yaml")
        cell_area = np.load(path / "areas.npy")
        
        with open(path / "metadata.yaml") as f:
            metadata = yaml.unsafe_load(f)

        return AreaResults(grid, cell_area, metadata)
