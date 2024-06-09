from abc import ABC, abstractmethod
import pickle, yaml
import numpy as np
from enum import Flag, auto
from pathlib import Path

from phystem.systems.ring.collectors.data_types import ArraySizeAware, MultFileList

class BaseData(ABC):
    @abstractmethod
    def __init__(self, root_path: str | Path, data_dirname="data") -> None:
        self.root_path = Path(root_path).absolute().resolve()
        self.data_path = self.root_path / data_dirname

class DeltaData(BaseData):
    class Mode(Flag):
        init = auto()
        final = auto()

    def __init__(self, root_path: str | Path) -> None:
        super().__init__(root_path)

        with open(self.root_path / "config.yaml") as f:
            self.configs = yaml.unsafe_load(f) 

        with open(self.data_path / "metadata.pickle", "rb") as f:
            self.num_points = pickle.load(f)["num_points"]
        
        temp_data = [0 for _ in range(self.num_points)] 
        self.init_cms = temp_data.copy()
        self.init_uids = temp_data.copy()
        self.init_selected_uids = temp_data.copy()

        self.final_cms = [{} for _ in range(self.num_points)]
        self.final_uids = [{} for _ in range(self.num_points)]
        
        self.load_data(self.data_path)
        self.init_times  = np.load(self.data_path / "init_times.npy")
        with open(self.data_path / "final_times.pickle", "rb") as f:
            self.final_times  = pickle.load(f)

    @staticmethod
    def parse(file_path: Path):
        parts = file_path.stem.split("_") 
        if parts[-1] == "i":
            mode = DeltaData.Mode.init
            id = int(parts[-2])
            return mode, id, None
        else:
            mode = DeltaData.Mode.final
            id = int(parts[-2])
            uid = int(parts[-1])
            return mode, id, uid

    def load_data(self, data_path: Path):
        for file_path in data_path.glob('**/cms_*.npy'):
            data = np.load(file_path)
            mode, id, uid = self.parse(file_path)
            if mode is DeltaData.Mode.init:
                self.init_cms[id] = data
            else:
                self.final_cms[id][uid] = data
        
        for file_path in data_path.glob('**/uids_*.npy'):
            data = np.load(file_path)
            mode, id, uid = self.parse(file_path)
            if mode is DeltaData.Mode.init:
                self.init_uids[id] = data
            else:
                self.final_uids[id][uid] = data
        
        for file_path in data_path.glob('**/selected-uids*.npy'):
            id = int(file_path.stem.split("_")[-2])
            self.init_selected_uids[id] = np.load(file_path)

class CreationRateData(BaseData):
    def __init__(self, root_path: str | Path) -> None:
        super().__init__(root_path)

        with open(self.data_path / "cr_metadata.yaml") as f:
            num_points = yaml.unsafe_load(f)["num_points"]

        self.time = np.load(self.data_path / "time.npy")[:num_points]
        self.num_created = np.load(self.data_path / "num_created.npy")[:num_points]
        self.num_active = np.load(self.data_path / "num_active.npy")[:num_points]

class DenVelData(BaseData):
    def __init__(self, root_path: str | Path) -> None:
        '''Carrega os dados coletados pelo coletor `DensityVelCol`. Para mais informações
        sobre o formato dos dados, leia a documentação do respectivo coletor.
        '''
        super().__init__(root_path)

        self.vel_time = np.load(self.data_path / "vel_time.npy")
        self.den_time = np.load(self.data_path / "den_time.npy")

        with open(self.data_path / "den_vel_metadata.yaml", "r") as f:
            metadata = yaml.unsafe_load(f)
            self.vel_num_files = metadata["vel_num_files"]
            self.den_num_files = metadata["den_num_files"]
            self.num_data_points_per_file = metadata["num_data_points_per_file"]
            self.vel_frame_dt = metadata["vel_frame_dt"]    
            self.density_eq = metadata["density_eq"]    

        self.den_data = MultFileList[ArraySizeAware, np.ndarray](self.data_path, "den_cms", self.den_num_files, self.num_data_points_per_file) 
        self.vel_data = MultFileList[ArraySizeAware, np.ndarray](self.data_path, "vel_cms", self.vel_num_files, self.num_data_points_per_file)

        self.num_vel_points = self.num_data_points_per_file * (self.vel_num_files - 1) + self.vel_data.get_file(self.vel_num_files-1).num_points
        self.num_den_points = self.num_data_points_per_file * (self.den_num_files - 1) + self.den_data.get_file(self.den_num_files-1).num_points
