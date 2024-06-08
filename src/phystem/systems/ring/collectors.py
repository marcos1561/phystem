import numpy as np
import yaml

from phystem.systems.ring.solvers import CppSolver
from phystem.core import collectors, settings
from phystem.core.collectors import ColAutoSaveCfg

from pathlib import Path

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
    
    def __init__(self, solver: CppSolver, root_path: Path, configs: dict, file_names: FileNames=None) -> None:
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
        self.file_names = file_names

        self.root_path.mkdir(exist_ok=True, parents=True)
        
        if file_names is None:
            self.file_names = StateSaver.FileNames()

        self.file_paths = {}
        for name, file_name in self.file_names.values.items():
            if file_name is None:
                self.file_paths[name] = None
            else:
                self.file_paths[name] = self.root_path / file_name

        collectors.Collector.save_cfg(configs, self.root_path / "config.yaml")

    def save(self, directory=None, filenames: FileNames=None, continuos_ring=False, metadata: dict[str]=None) -> None:
        '''Salva o estado do sistema.'''
        if directory is None:
            directory = self.root_path
        else:
            directory = Path(directory)

        if filenames is None:
            filenames = self.file_names

        ##
        # Salvando metadados
        ##
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

class RingCol(collectors.Collector):
    '''Base para os coletores dos anéis.'''
    def __init__(self, solver: CppSolver, path: str | Path, configs: dict, autosave_cfg: ColAutoSaveCfg = None) -> None:
        super().__init__(solver, path, configs, autosave_cfg)

        if autosave_cfg is not None:
            self.state_col = StateSaver(self.solver, self.autosave_root_path, self.configs)

    def autosave(self):
        super().autosave()

        if self.autosave_cfg.to_save_state:
            self.state_col.save(metadata={settings.autosave_flag_name: True})

# class AreaCollector(collectors.Collector):
#     def __init__(self, solver: CppSolver, path: str, configs: list, tf: float, dt: float, num_points: int) -> None:
#         super().__init__(solver, path, configs)

#         self.areas = []
#         self.time = []

#         self.freq = int((tf/dt) / num_points)
#         if self.freq == 0:
#             self.freq = 1

#     def collect(self, count: int) -> None:
#         if count % self.freq == 0:
#             self.areas.append(list(self.solver.area_debug.area))
#             self.time.append(self.solver.time)

#     def save(self) -> None:
#         super().save()
#         path_area = os.path.join(self.path, "areas.npy")
#         path_time = os.path.join(self.path, "time.npy")
#         np.save(path_area, np.array(self.areas))
#         np.save(path_time, np.array(self.time))
    
# class StateCheckpoint(collectors.Collector):
#     def __init__(self, solver: CppSolver, path: str, configs: list, num_checkpoints: int, tf: float, to: float = 0) -> None:
#         super().__init__(solver, path, configs)
#         self.solver: CppSolver

#         freq = int(((tf-to)/solver.dt)/num_checkpoints)
#         if freq == 0:
#             freq = 1
#         self.freq = freq
#         print("save freq:", self.freq)
        
#         self.num_saves = 0

#         num_rings = self.solver.num_max_rings
#         num_particles = self.solver.num_particles

#         self.pos = np.zeros((num_rings, num_particles, 2), dtype=np.float64),
#         self.vel = np.zeros((num_rings, num_particles, 2), dtype=np.float64),
#         self.angle = np.zeros((num_rings, num_particles), dtype=np.float64),
#         self.metadata = {
#             "num_time_steps": 0,
#             "time": 0,
#         }

#         self.file_path = self.get_files_path(self.path)
#         self.save()
    
#     @staticmethod
#     def get_files_path(path):
#         return [
#             os.path.join(path, "pos.npy"),
#             os.path.join(path, "angle.npy"),
#             os.path.join(path, "metadata.pickle"),
#             os.path.join(path, "ids.npy"),
#             os.path.join(path, "uids.npy"),
#         ]

#     def collect(self, count: int) -> None:
#         if count % self.freq == 0:
#             self.pos = np.array(self.solver.pos)
#             self.angle = np.array(self.solver.self_prop_angle)
#             self.metadata["num_time_steps"] = self.solver.num_time_steps
#             self.metadata["time"] = self.solver.time
            
#             # print(f"Saving | t = {self.solver.time} | count = {count} | count/f = {count/self.freq}")
#             self.num_saves += 1

#             np.save(self.file_path[0], self.pos)
#             np.save(self.file_path[1], self.angle)
            
#             with open(self.file_path[2], "wb") as f:
#                 pickle.dump(self.metadata, f)                

#     @staticmethod
#     def load(path: str):
#         from phystem.systems.ring.creators import InitData

#         files_path = StateCheckpoint.get_files_path(path)
#         pos = np.load(files_path[0]) 
#         angle = np.load(files_path[1])
#         ids = np.load(files_path[3])
#         uids = np.load(files_path[4])
        
#         metadata = None
#         if os.path.exists(files_path[2]):
#             with open(files_path[2], "rb") as f:
#                 metadata = pickle.load(f)

#         init_data = InitData(pos, angle, uids)
#         return init_data, metadata

# class LastState(collectors.Collector):
#     '''
#     Coleta a posição no final da simulação. Para tal, apenas é necessário
#     rodar a simulação e chamar o método 'save' após sua finalização.
#     '''
#     solver: CppSolver

#     def __init__(self, solver: CppSolver, path: str, configs: list) -> None:
#         super().__init__(solver, path, configs)
#         self.ring_ids: np.ndarray = None

#     def collect(self, count: int) -> None:
#         pass

#     def save(self, pos_name="pos", angle_name="angle", ids_name="ids", directory=None, 
#             continuos_ring=False, metadata=None) -> None:
#         if directory is None:
#             directory = self.path

#         pos_path = os.path.join(directory, pos_name + ".npy")
#         angle_path = os.path.join(directory, angle_name + ".npy")
#         ids_path = os.path.join(directory, ids_name + ".npy")
#         metadata_path = os.path.join(directory, "metadata.yaml")

#         if metadata is None:
#             metadata = {
#                 "time": self.solver.time,
#                 "num_time_steps": self.solver.num_time_steps,
#             }
#         with open(metadata_path, "w") as f:
#             yaml.dump(metadata, f)

#         self.ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]
        
#         if continuos_ring:
#             np.save(pos_path, np.array(self.solver.pos_continuos)[self.ring_ids])
#         else:
#             np.save(pos_path, np.array(self.solver.pos)[self.ring_ids])
        
#         np.save(angle_path, np.array(self.solver.self_prop_angle)[self.ring_ids])
#         np.save(ids_path, np.array(self.solver.unique_rings_ids)[self.ring_ids])
