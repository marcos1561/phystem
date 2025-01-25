import numpy as np
import pickle
from pathlib import Path
from typing import TypeVar, Generic

class ArraySizeAware:
    def __init__(self, num_data_points: int, max_num_els: int, num_dims: int, dtype=np.float32) -> None:
        '''
        Array com shape (num_data_points, max_num_els, num_dims) que está ciente do 
        seu tamanho na segunda dimensão (max_num_els). 
        O valor `x = self.data[i]` é considerado o i-ésimo ponto de dados e o valor 
        `n = self.point_num_elements[i]` informa quantos elementos exitem nesse ponto, 
        ou seja, os dados reais do ponto são `x[:n]`. O array sempre é inicializado
        com zeros.

        Seus dados devem ser preenchidos ponto por ponto, utilizando `self.add`.
        
        Esse objeto pode ser indexado e o item retornado é `x[:n]`.
        '''
        self.data = np.zeros((num_data_points, max_num_els, num_dims), dtype=dtype)
        self.point_num_elements = np.zeros(num_data_points, dtype=int)
        self.current_id = 0

    def add(self, data: np.array):
        '''
        Adiciona um novo ponto de dados no array. `data` deve
        ter o shape (max_num_els, num_dims).
        '''
        self.update(self.current_id, data)
        self.current_id += 1

    def update(self, id, data: np.array):
        num_elements = data.shape[0]
        self.data[id,:num_elements] = data
        self.point_num_elements[id] = num_elements

    def add_multiple(self, data: np.ndarray, num_elements):
        '''
        Adiciona os múltiplos pontos em `data`.
        
        # Parâmetros
        ------------
        data:
            Array com shape (num_points, max_num_els, num_dims) contendo
            os pontes a serem salvos
        num_elements:
            Array com 1-D de tamanho num_points, contento quantos elementos
            cada ponto possui.
        '''
        num_points = data.shape[0]
        self.data[self.current_id:self.current_id + num_points] = data
        self.point_num_elements[self.current_id:self.current_id + num_points] = num_elements
        self.current_id += num_points

    def reset(self):
        self.current_id = 0
        self.point_num_elements[:] = 0
        self.data[:] = 0

    def strip(self):
        "Remove os pontos de dados ainda não preenchidos."
        self.data = self.data[:self.num_points]
        self.point_num_elements = self.point_num_elements[:self.num_points]

    def __getitem__(self, key):
        if key >= self.num_points:
            raise IndexError(f"Id {key} fora das bordas [0, {self.num_points}-1].")
        return self.data[key][:self.point_num_elements[key]]

    @property
    def num_points(self):
        return self.current_id
    
    @property
    def max_num_els(self):
        return self.data.shape[1]

    def __len__(self):
        return self.num_points

    @property
    def is_full(self):
        return self.current_id >= self.data.shape[0]

    @classmethod
    def empty(Cls):
        return Cls(0, 0, 0)

ListT = TypeVar('ListT')
ItemT = TypeVar('ItemT')
class MultFileList(Generic[ListT, ItemT]):
    def __init__(self, root_path: Path, name: str) -> None:
        '''
        Iterador e indexador de uma lista de dados que está distribuída em vários arquivos.

        Os arquivos devem estar no caminho `root_path` e o nome do i-ésimo arquivo 
        deve ser "{name}_{i}.pickle". Cada arquivo deve conter uma fatia da lista
        com um número fixo de elementos.
        '''
        self.root_path = Path(root_path)
        self.name = name
        self.num_files = len(list(self.root_path.glob(f"{self.name}_[0-9]*")))
        
        self.data = self._load_file(0)
        self.num_data_points_per_file = len(self.data)
        # self.num_data_points_per_file = self.data.data.shape[0]

        self._id = 0
        self._file_id = 0
        self._num_total_points = (self.num_files - 1) * self.num_data_points_per_file + len(self._load_file(self.num_files-1))

    def _reset(self):
        self._id = 0
        self.file_id = 0

    def _load_file(self, file_id) -> ListT:
        with open(self.root_path / f"{self.name}_{file_id}.pickle", "rb") as f:
            data = pickle.load(f)
        return data

    @property
    def file_id(self):
        '''Id do arquivo atualmente aberto.'''
        return self._file_id
    
    @file_id.setter
    def file_id(self, value):
        if value != self.file_id:
            self._file_id = value
            self.data = self._load_file(self.file_id)

    def get_file(self, file_id):
        self.file_id = file_id
        return self.data

    def _get_ids(self, id):
        file_id = id // self.num_data_points_per_file
        point_id = id - file_id * self.num_data_points_per_file
        return file_id, point_id

    def __getitem__(self, key) -> ItemT:
        fid, pid = self._get_ids(key)
        self.file_id = fid
        return self.data[pid]

    def __iter__(self):
        self._reset()
        return self

    def __next__(self) -> ItemT:
        fid, pid = self._get_ids(self._id)
        
        if fid < self.num_files:
            self.file_id = fid
        else:
            self._reset()
            raise StopIteration

        if self.file_id == (self.num_files - 1) and pid >= len(self.data):
            self._reset()
            raise StopIteration

        item = self.data[pid]
        self._id += 1
        return item
    
    def __len__(self):
        return self._num_total_points
    
if __name__ == "__main__":
    a = MultFileList[ArraySizeAware, np.ndarray](
        "/home/marcos/Documents/Programacao/IC/phystem/experiments/ring/density_profile/data/den_vel_test/den_vel/data",
        "den_cms")
    
    for idx, i in enumerate(a):
        print(idx, i.shape)