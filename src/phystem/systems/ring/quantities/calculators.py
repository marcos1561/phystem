import pickle
import numpy as np
from pathlib import Path

from phystem.systems.ring import utils
from phystem.core.autosave import AutoSavable
from .datas import DeltaData, BaseData
from abc import ABC, abstractmethod

class CalcAutoSaveCfg:
    def __init__(self, freq: int) -> None:
        self.freq = freq

class Calculator(AutoSavable):
    def __init__(self, data: str | DeltaData, root_dir: Path, autosave_cfg: CalcAutoSaveCfg=None) -> None:
        super().__init__(root_dir)
        self.autosave_cfg = autosave_cfg
        self.root_dir = Path(root_dir).absolute().resolve()

        if type(data) != DeltaData:
            self.data = DeltaData(data)
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
        return {"data": self.data.path, "root_dir": self.root_dir}

    def autosave(self):
        super().autosave()
        self.save_init_kwargs()

    def check_autosave(self, id):
        if id % self.autosave_cfg.freq == 0:
            self.autosave()

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
    def __init__(self, data: str | Path | DeltaData, edge_k: float, 
        root_dir: Path, autosave_cfg:CalcAutoSaveCfg=None) -> None:
        '''Calcula o delta nos dados salvos em `path`.
        
        Parâmetros:
            edge_k:
                Defino o valor máximo do comprimento dos links entre anéis

                'valor máximo do link' := 'Diâmetro do anel' * 'edge_k'
        '''
        super().__init__(data, root_dir, autosave_cfg)
        configs = self.data.configs
        ring_d = utils.get_ring_radius(
            configs["dynamic_cfg"].diameter, configs["creator_cfg"].num_p) * 2
        
        self.edge_k = edge_k
        self.edge_tol = ring_d * self.edge_k

        self.current_id = 0
        self.deltas = []
        self.times = []

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

    def calc(self, id_stop=None):
        for pid in range(self.current_id, self.data.num_points):
            if id_stop is not None and id_stop == pid:
                break
            
            self.current_id = pid
            if self.autosave_cfg:
                self.check_autosave(pid)

            init_cms = self.data.init_cms[pid]

            links, dists = utils.calc_edges(init_cms, self.edge_tol, return_dist=True)
            rings_links = utils.links_ids(links, init_cms.shape[0])
            neighbors = utils.neighbors_all(links, init_cms.shape[0])

            init_uids = self.data.init_uids[pid]
            selected_ids = np.where(np.in1d(init_uids, self.data.init_selected_uids[pid]))[0]
            deltas = []
            for i in selected_ids:
                neighs = neighbors[i]
                if len(neighs) == 0:
                    continue
                selc_uid = init_uids[i]
                
                final_cms = self.data.final_cms[pid].get(selc_uid, None)
                if final_cms is None:
                    continue

                final_diffs = final_cms[neighs] - final_cms[i]
                final_dists_square = np.square(final_diffs).sum(axis=1)

                init_dists = dists[rings_links[i]]
                r_sum = (np.square(init_dists) / final_dists_square).sum()
                delta = 1 - r_sum / len(neighs) 
                
                deltas.append(delta)
            
            if len(deltas) > 0:
                self.deltas.append(sum(deltas)/len(deltas))
                self.times.append(self.data.init_times[pid])

    # @staticmethod
    # def from_checkpoint(path: Path, autosave_cfg: CalcAutoSaveCfg=None):
    #     path = Path(path)
    #     with open(path / "kwargs.pickle", "rb") as f:
    #         kwargs = pickle.load(f)

    #     obj = DeltaCalculator(**kwargs, autosave_cfg=autosave_cfg)
    #     obj.load_autosave()
    #     return obj
