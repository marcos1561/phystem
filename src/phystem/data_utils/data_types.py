import numpy as np
import pickle
from pathlib import Path
from typing import TypeVar, Generic

class ArraySizeAware:
    def __init__(self, num_data_points: int, max_num_els: int, num_dims: int, dtype=np.float32) -> None:
        '''Array com shape (num_data_points, max_num_els, num_dims) que está ciente do 
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
        '''Adiciona um novo ponto de dados no array. `data` deve
        ter o shape (max_num_els, num_dims).
        '''
        self.update(self.current_id, data)
        self.current_id += 1

    def update(self, id, data: np.array):
        num_elements = data.shape[0]
        self.data[id,:num_elements] = data
        self.point_num_elements[id] = num_elements

    def reset(self):
        self.current_id = 0
        self.point_num_elements[:] = 0
        self.data[:] = 0

    def strip(self):
        '''Remove os pontos de dados ainda não preenchidos'''
        self.data = self.data[:self.num_points]
        self.point_num_elements = self.point_num_elements[:self.num_points]

    def __getitem__(self, key):
        return self.data[key][:self.point_num_elements[key]]

    @property
    def num_points(self):
        return self.current_id

    def __len__(self):
        return self.num_points

    @property
    def is_full(self):
        return self.current_id >= self.data.shape[0]

ListT = TypeVar('ListT')
ItemT = TypeVar('ItemT')
class MultFileList(Generic[ListT, ItemT]):
    def __init__(self, root_path: Path, name: str, num_files, num_data_points_per_file) -> None:
        '''Iterador e indexador de uma lista de dados que está distribuída em vários arquivos.

        Os arquivos devem estar no caminho `root_path` e o nome do i-ésimo arquivo 
        deve ser "{name}_{i}.pickle". Cada arquivo deve conter uma fatia da lista
        com `num_data_points_per_file` elementos.
        '''
        self.num_files = num_files
        self.root_path = root_path
        self.name = name
        self.num_data_points_per_file = num_data_points_per_file
        
        self._id = 0
        self._file_id = 0
        self.data = self._load_file(0)

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
        self.file_id = fid

        if self.file_id == (self.num_files - 1) and pid >= len(self.data):
            self._reset()
            raise StopIteration

        item = self.data[pid]
        self._id += 1
        return item