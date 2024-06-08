from abc import ABC, abstractmethod

import pickle, yaml
import numpy as np
from enum import Flag, auto
from pathlib import Path

class BaseData(ABC):
    @abstractmethod
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).absolute().resolve()

class DeltaData(BaseData):
    class Mode(Flag):
        init = auto()
        final = auto()

    def __init__(self, path: str | Path) -> None:
        super().__init__(path)

        with open(self.path / "config.yaml") as f:
            self.configs = yaml.unsafe_load(f) 

        data_path = self.path / "data"
        with open(data_path / "metadata.pickle", "rb") as f:
            self.num_points = pickle.load(f)["num_points"]
        
        temp_data = [0 for _ in range(self.num_points)] 
        self.init_cms = temp_data.copy()
        self.init_uids = temp_data.copy()
        self.init_selected_uids = temp_data.copy()

        self.final_cms = [{} for _ in range(self.num_points)]
        self.final_uids = [{} for _ in range(self.num_points)]
        
        self.load_data(data_path)
        self.init_times  = np.load(data_path / "init_times.npy")
        with open(data_path / "final_times.pickle", "rb") as f:
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
