import numpy as np
import yaml
from pathlib import Path

from .solvers import CppSolver
from phystem.core import collectors, settings

class StateData:
    def __init__(self, pos, angle, ids, uids) -> None:
        self.pos = pos
        self.angle = angle
        self.ids = ids
        self.uids = uids

    def get_init_date(self):
        from phystem.systems.ring.creators import InitData
        return InitData(self.pos, self.angle)
    
class StateSaver:
    class FileNames:
        def __init__(self, pos="pos", angle="angle", vel=None, ids="ids", uids="uids", metadata="metadata"):
            self.pos = self.get_name(pos)
            self.angle = self.get_name(angle)
            self.vel = self.get_name(vel)
            self.ids = self.get_name(ids)
            self.uids = self.get_name(uids)
            self.metadata = self.get_name(metadata, ext=".yaml")

        def get_name(self, value: str, ext=".npy"):
            if value is None:
                return None
            return value + ext

        @property
        def values(self): 
            return {
                "pos": self.pos, 
                "angle": self.angle, 
                "vel": self.vel, 
                "ids": self.ids,
                "uids": self.uids,
                "metadata": self.metadata,
            }
    
    def __init__(self, solver: CppSolver, root_path: Path, configs: dict, filenames: FileNames=None) -> None:
        '''Coletor para salvar o estado do sistema. O seu método `collect` não está implementado, para 
        salver o estado do sistema utilize `self.save`.
        
        Parâmetros:
            solver:
                Solver do sistema em questão.
            
            root_path:
                Caminho da pasta onde os dados serão salvos.

            file_names:
                Nome dos arquivos que serão salvos. Caso for `None` será utilizado
                os nomes padrões definidos em `FileNames`.
                
                Para não salvar algum dado, sete para `None` o nome do seu arquivo.
        '''
        self.solver = solver 
        self.root_path = Path(root_path)
        self.configs = configs
        self.filenames = filenames

        self.root_path.mkdir(exist_ok=True, parents=True)
        
        if filenames is None:
            self.filenames = StateSaver.FileNames()

        self.file_paths = {}
        for name, file_name in self.filenames.values.items():
            if file_name is None:
                self.file_paths[name] = None
            else:
                self.file_paths[name] = self.root_path / file_name

        collectors.Collector.save_cfg(configs, self.root_path / settings.system_config_fname)

    def save(self, directory=None, filenames: FileNames=None, continuos_ring=False, metadata: dict[str]=None) -> None:
        '''Salva o estado do sistema.'''
        if directory is None:
            directory = self.root_path
        else:
            directory = Path(directory)

        if filenames is None:
            filenames = self.filenames

        ##
        # Salvando metadados
        ##
        if filenames.metadata is not None:
            metadata_path = directory / filenames.metadata

            _metadata = {
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            }
            if metadata is not None:
                for key, value in metadata.items():
                    _metadata[key] = value 

            with open(metadata_path, "w") as f:
                yaml.dump(_metadata, f)

        ##
        # Salvando estado do sistema
        ##
        self.ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        
        if filenames.pos is not None:
            pos_path = directory / filenames.pos

            if continuos_ring:
                np.save(pos_path, np.array(self.solver.pos_continuos)[self.ring_ids])
            else:
                np.save(pos_path, np.array(self.solver.pos)[self.ring_ids])
        
        if filenames.angle is not None:
            angle_path = directory / filenames.angle
            np.save(angle_path, np.array(self.solver.self_prop_angle)[self.ring_ids])

        if filenames.uids is not None:
            uids_path = directory / filenames.uids
            np.save(uids_path, np.array(self.solver.unique_rings_ids)[self.ring_ids])
        
        if filenames.ids is not None:
            ids_path = directory / filenames.ids
            np.save(ids_path, self.ring_ids)

        if filenames.vel is not None:
            vel_path = directory / filenames.vel
            np.save(vel_path, np.array(self.solver.vel)[self.ring_ids])

    @staticmethod
    def load(path: Path, filenames: FileNames=None):
        path = Path(path)

        if filenames is None:
            filenames = StateSaver.FileNames()
        
        pos = np.load(path / filenames.pos)
        angle = np.load(path / filenames.angle)
        ids = np.load(path / filenames.ids)
        uids = np.load(path / filenames.uids)
        
        metadata = None
        metadata_path: Path = path / filenames.metadata
        if metadata_path.exists():
            with open(metadata_path, "rb") as f:
                metadata = yaml.unsafe_load(f)

        init_data = StateData(pos, angle, ids, uids)
        return init_data, metadata

