from abc import ABC, abstractmethod
import pickle, yaml
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.data_utils.data_types import ArraySizeAware, MultFileList
from phystem.systems.ring.collectors.quantity_pos.collectors import (
    VelocityCfg, CmsCfg, PolarityCfg, AreaCfg
)

class BaseData(ABC):
    @abstractmethod
    def __init__(self, root_path: Path, data_dirname="data") -> None:
        self.root_path = Path(root_path).absolute().resolve()
        self.data_path = self.root_path / data_dirname


class DeltaData(BaseData):
    class Mode(Flag):
        init = auto()
        final = auto()

    def __init__(self, root_path: Path, debug=False) -> None:
        super().__init__(root_path)

        with open(self.root_path / "config.yaml") as f:
            self.configs = yaml.unsafe_load(f) 

        with open(self.data_path / "metadata.pickle", "rb") as f:
            self.num_init_points = pickle.load(f)["num_points"]
        self.ids_completed: list[int] = []

        temp_data = [0 for _ in range(self.num_init_points)] 
        self.init_cms = temp_data.copy()
        self.init_uids = temp_data.copy()
        self.init_selected_uids = temp_data.copy()

        self.final_cms = temp_data.copy()
        self.final_uids = temp_data.copy()
        
        self.load_data(self.data_path)
        self.init_times  = np.load(self.data_path / "init_times.npy")
        self.final_times  = np.load(self.data_path / "final_times.npy")



    @staticmethod
    def parse(file_path: Path):
        parts = file_path.stem.split("_") 
        id = int(parts[-2])
        if parts[-1] == "i":
            mode = DeltaData.Mode.init
        else:
            mode = DeltaData.Mode.final

        return mode, id

    def load_data(self, data_path: Path):
        for file_path in data_path.glob('**/cms_*.npy'):
            data = np.load(file_path)
            mode, id = self.parse(file_path)
            if id >= self.num_init_points-1:
                continue
            
            if mode is DeltaData.Mode.init:
                self.init_cms[id] = data
            else:
                self.ids_completed.append(id)
                self.final_cms[id] = data
        
        for file_path in data_path.glob('**/uids_*.npy'):
            data = np.load(file_path)
            mode, id = self.parse(file_path)
            if id >= self.num_init_points-1:
                continue

            if mode is DeltaData.Mode.init:
                self.init_uids[id] = data
            else:
                self.final_uids[id] = data
        
        for file_path in data_path.glob('**/selected-uids*.npy'):
            id = int(file_path.stem.split("_")[-2])
            if id >= self.num_init_points-1:
                continue

            self.init_selected_uids[id] = np.load(file_path)

        self.ids_completed.sort()
        self.num_points_completed = len(self.ids_completed)

class CreationRateData(BaseData):
    def __init__(self, root_path: Path) -> None:
        super().__init__(root_path)

        with open(self.data_path / "cr_metadata.yaml") as f:
            num_points = yaml.unsafe_load(f)["num_points"]

        self.time = np.load(self.data_path / "time.npy")[:num_points]
        self.num_created = np.load(self.data_path / "num_created.npy")[:num_points]
        self.num_active = np.load(self.data_path / "num_active.npy")[:num_points]


class CmsData(BaseData):
    def __init__(self, root_path: Path) -> None:
        '''
        Carrega os dados dos centros de massa coletados pelo coletor `QuantityPos`. 
        Para mais informações sobre o formato dos dados, leia a 
        documentação do respectivo coletor.
        '''
        super().__init__(root_path)
        self.time = np.load(self.data_path / "times.npy")
        self.cms = MultFileList[ArraySizeAware, np.ndarray](self.data_path, CmsCfg.name) 

class VelData(BaseData):
    def __init__(self, root_path: Path) -> None:
        '''
        Carrega os dados das velocidades coletados pelo coletor `QuantityPos`. 
        Para mais informações sobre o formato dos dados, leia a 
        documentação do respectivo coletor.
        '''
        super().__init__(root_path)
        self.time = np.load(self.data_path / "times.npy")
        self.vel = MultFileList[ArraySizeAware, np.ndarray](self.data_path, VelocityCfg.name) 
        self.cms = MultFileList[ArraySizeAware, np.ndarray](self.data_path, CmsCfg.name) 

        with open(self.data_path / f"{VelocityCfg.name}_metadata.yaml", "r") as f:
            metadata = yaml.unsafe_load(f)
            self.frame_dt = metadata["frame_dt"]    
            self.last_point_completed = metadata["last_point_completed"]    

class PolData(BaseData):
    def __init__(self, root_path: Path) -> None:
        '''
        Carrega os dados das polarizações coletados pelo coletor `QuantityPos`. 
        Para mais informações sobre o formato dos dados, leia a 
        documentação do respectivo coletor.
        '''
        super().__init__(root_path)
        self.time = np.load(self.data_path / "times.npy")
        self.pol = MultFileList[ArraySizeAware, np.ndarray](self.data_path, PolarityCfg.name) 
        self.cms = MultFileList[ArraySizeAware, np.ndarray](self.data_path, CmsCfg.name) 

class AreaData(BaseData):
    def __init__(self, root_path: Path) -> None:
        '''
        Carrega os dados das áreas coletados pelo coletor `QuantityPos`. 
        Para mais informações sobre o formato dos dados, leia a 
        documentação do respectivo coletor.
        '''
        super().__init__(root_path)
        self.time = np.load(self.data_path / "times.npy")
        self.area = MultFileList[ArraySizeAware, np.ndarray](self.data_path, AreaCfg.name) 
        self.cms = MultFileList[ArraySizeAware, np.ndarray](self.data_path, CmsCfg.name) 


class DenVelData(BaseData):
    def __init__(self, root_path: Path) -> None:
        '''
        Carrega os dados coletados pelo coletor `DensityVelCol`. Para mais informações
        sobre o formato dos dados, leia a documentação do respectivo coletor.
        '''
        super().__init__(root_path)

        self.vel_time = np.load(self.data_path / "vel_time.npy")
        try:
            self.vel2_time = np.load(self.data_path / "vel2_time.npy")
        except FileNotFoundError as e:
            self.vel2_time = None
        
        self.den_time = np.load(self.data_path / "den_time.npy")
        # self.pol_time = np.load(self.data_path / "pol_time.npy")

        self.den_data = MultFileList[ArraySizeAware, np.ndarray](self.data_path, "den_cms") 
        self.vel_data = MultFileList[ArraySizeAware, np.ndarray](self.data_path, "vel_cms")
        
        with open(self.data_path / "den_vel_metadata.yaml", "r") as f:
            metadata = yaml.unsafe_load(f)
            self.total_num_data_points_per_file = metadata["num_data_points_per_file"]
            self.vel_frame_dt = metadata["vel_frame_dt"]    
            self.density_eq = metadata["density_eq"]    

        self.vel_num_files = self.vel_data.num_files
        self.den_num_files = self.den_data.num_files
        self.num_vel_points = len(self.vel_data)
        self.num_den_points = len(self.den_data)

        # self.num_vel_points = self.total_num_data_points_per_file * (self.vel_num_files - 1) + self.vel_data.get_file(self.vel_num_files-1).num_points
        # self.num_den_points = self.total_num_data_points_per_file * (self.den_num_files - 1) + self.den_data.get_file(self.den_num_files-1).num_points

class AreaDataOld(BaseData):
    def __init__(self, root_path: Path, data_dirname="data") -> None:
        super().__init__(root_path, data_dirname)

        with open(self.data_path / "data.pickle", "rb") as f:
            data = pickle.load(f)
        
        self.times = data["times"]
        self.areas = data["areas"]
        self.pos = data["pos"]