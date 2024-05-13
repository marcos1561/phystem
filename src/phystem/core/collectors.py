from abc import ABC, abstractmethod
import os, yaml, copy, pickle
from pathlib import Path
import numpy as np

from phystem.core.solvers import SolverCore

class AutoSaveCfg:
    def __init__(self, freq_dt: float=None, root_dir: str="autosave", to_save_state: bool = True) -> None:
        self.root_dir = Path(root_dir)
        self.freq_dt = freq_dt
        self.to_save_state = to_save_state

        self.data_path = self.root_dir / "data"
    
class Collector(ABC):
    '''
    Responsável pela coleta de dados gerados pelo solver.
    '''
    def __init__(self, solver: SolverCore, path: str, configs: dict, autosave_cfg: AutoSaveCfg=None) -> None:
        '''
        Parameters:
        -----------
            solver:
                Solver do sistema em que será coletado os dados.
            path:
                Caminho da pasta que vai conter os dados coletados.
            
            config:
                Lista com todas as configurações da simulação.\n
                Apenas utilizado para salver as configurações no fim da coleta,
                na mesma pasta dos dados com o nome 'config.yaml'.

            autosave_cfg:
                Configurações do auto-salvamento:
                
                * root_dir:
                    Diretório relativo a `path` onde será guardado os salvamentos automáticos.
                
                * freq_dt:
                    Frequência temporal em que é feito o auto-salvamento.
                
                * to_save_state:
                    Se é para salvar o estado do sistema.
        '''
        self.solver = solver
        self.configs = configs
        self.path = path
        self.config_path = os.path.join(self.path, "config.yaml")
        
        paths_check = [Path(self.path)]

        if autosave_cfg is not None:
            self.autosave_cfg = autosave_cfg
            self.autosave_path = Path(self.path) / autosave_cfg.root_dir
            self.autosave_data_path = Path(self.path) / autosave_cfg.data_path
            paths_check.append(self.autosave_path)
            paths_check.append(self.autosave_data_path)

        for p in paths_check:
            p.mkdir(parents=True, exist_ok=True)
        
        self.save_cfg()

    @abstractmethod
    def collect(self, count: int) -> None:
        '''
        Realiza a coleta dos dados no instante atual.

        Parameters:
        -----------
            count:
                Contador do número de passos temporais que já foram dados.
        '''
        pass

    @property
    def vars_to_save(self):
        raise Exception("'vars_to_save' não foi definido.")

    def get_vars_to_save(self):
        return {name: getattr(self, name) for name in self.vars_to_save}
    
    def set_vars_to_save(self, values: dict):
        for name, value in values.items():
            setattr(self, name, value)

    def check_autosave(self):
        if self.solver.time - self.autosave_last_time > self.autosave_dt:
            self.autosave_last_time = self.solver.time
            self.autosave()

    def autosave(self):
        with open(self.autosave_path / self.save_name, "wb") as f:
            pickle.dump(self.get_vars_to_save(), f)

        if self.autosave_cfg.to_save_state:
            self.state_col.save(metadata={
                "is_autosave": True,
                "time": self.solver.time,
                "num_time_steps": self.solver.num_time_steps,
            })
    
    def load_autosave(self):
        with open(self.autosave_path / self.save_name, "rb") as f:
            saved_vars = pickle.load(f)
            self.set_vars_to_save(saved_vars)

    def save_cfg(self) -> None:
        '''Salva as configurações da simulação.'''
        configs = copy.deepcopy(self.configs)
        configs["run_cfg"].func = "nao salvo"
        
        # Impede o salvamento de todos os checkpoints utilizados
        # caso seja salvado um checkpoint que foi carregado de outro checkpoint.
        if configs["run_cfg"].checkpoint:
            configs["run_cfg"].checkpoint.configs = "nao salvo"
        
        with open(self.config_path, "w") as f:
            yaml.dump(configs, f)
    
class State(Collector):
    def __init__(self, solver: SolverCore, path: str, configs: dict, tf: float, dt: float, to=0.0, 
        num_points:int=None) -> None:
        '''
        Coleta todas as informações do estado do sistema. A coleta começa em t=to e vai até
        t=tf, com o número de pontos coletados podendo ser explicitamente informado, caso contrário,
        em cada passo temporal a coleta é feita.

        Parameters:
        -----------
            solver:
                Referência ao `solver` que está integrando o sistema.
            
            path:
                Caminho da pasta que vai conter os dados coletados.
            
            config:
                Lista com todas as configurações da simulação.\n
                Apenas utilizado para salver as configurações no fim da coleta,
                na mesma pasta dos dados com o nome 'config.yaml'.
            
            to:
                Tempo inicial da coleta de dados. 
            
            tf:
                Tempo final da coleta de dados.
            
            dt:
                Passo temporal da simulação.
            
            num_points:
                Número de pontos a serem coletados.
        '''
        super().__init__(solver, path, configs)

        collect_all_steps = num_points is None

        if num_points is None:
            if tf is None or dt is None:
                raise ValueError("Como 'num_points = None', 'tf' e 'dt' devem ser passados.")
            num_points = int((tf-to)/dt)

        if not os.path.exists(path):
            raise ValueError("O caminho especificado não existe.")

        if collect_all_steps:
            freq = 1
        else:
            freq = int(((tf-to)/dt)/num_points)
            if freq == 0:
                freq = 1

        self.num_points = num_points
        self.dt = dt
        self.to = to
        self.tf = tf
        self.freq = freq

        self.data_count = 0

        self.data_vars: dict[str, np.ndarray] = {}
        self.generate_data_vars()

    @abstractmethod
    def generate_data_vars(self) -> None:
        '''
        Dicionário com o nome da variável a ser salva e a variável que armazena seus valores.
        A variável interna que contém esses dados é `data_vars`.
        '''
        pass

    @abstractmethod
    def collect_vars(self) -> None:
        '''
        Coleta das variáveis do solver para o ponto experimental de índice `self.data_count`.
        '''
        pass

    def collect(self, count: int):
        time = count * self.dt
        if time < self.to or time > self.tf:
            return

        if count % self.freq == 0 and self.data_count < self.num_points:
            self.collect_vars()
            self.data_count += 1
    
    def save(self):
        super().save()
        for var_name, var_data in self.data_vars.items():
            np.save(os.path.join(self.path, var_name + ".npy"), var_data)

        with open(os.path.join(self.path, "metadata.yaml"), "w") as f:
            yaml.dump({"num_points": self.data_count}, f)        

    @staticmethod
    def load(path: str) -> dict:
        '''
        Carrega os dados salvos em `path`.
        '''
        data_list = {}
        for file_name in os.listdir(path):
            file_name, extension = file_name.split(".") 

            if extension == "npy":
                data_list[file_name] = np.load(os.path.join(path, file_name + "." + extension))

        return data_list
    
    @staticmethod
    def memory_needed(dt: float, to: float, tf: float, num_particles: int):
        '''
        Retorna a memória necessária em MB para todos os passos temporais de `to` até `tf`
        com `num_particles` partículas.
        '''
        raise Exception("Não implementado.")

# TODO: Esse checkpoint aqui tá uma porra. 
class Checkpoint(Collector, ABC):
    file_names: list[str] = None

    def __init__(self, solver: SolverCore, path: str, configs: dict, num_checkpoints: int, tf: float, to: float = 0) -> None:
        super().__init__(solver, path, configs)
        raise Exception("Não use o checkpoint agora.")

        self.check_file_names()

        freq = int(((tf-to)/solver.dt)/num_checkpoints)
        if freq == 0:
            freq = 1
        self.freq = freq

        self.file_paths = self.get_file_paths(self.path)
        self.data = {f_name: np.array([]) for f_name in Checkpoint.file_names}

        self.save()

    @staticmethod
    def check_file_names():
        if Checkpoint.file_names is None:
            raise Exception("A super classe de Checkpoint deve sobrescrever o campo 'file_names'")

    @staticmethod
    def get_file_paths(path):
        Checkpoint.check_file_names()
        return {f_name: os.path.join(path, f_name + ".npy") for f_name in Checkpoint.file_names}
    
    @abstractmethod
    def collect_checkpoint(self):
        pass

    def collect(self, count: int) -> None:
        if count % self.freq == 0:
            self.collect_checkpoint()

            for f_name in Checkpoint.file_names:
                np.save(self.file_paths[f_name], self.data[f_name])
            
    @staticmethod
    def load(path: str):
        file_paths = Checkpoint.get_file_paths(path)
        return {name: np.load(path) for name, path in file_paths.items()}
        
if __name__ == "__main__":
    class CpTeste(Checkpoint):
        Checkpoint.file_names = ["opa", "Noice"]
        # file_names = ["opa", "Noice"]
        
        def collect_checkpoint(self):
            pass
    
    class CpTeste2(Checkpoint):
        Checkpoint.file_names = ["opa2", "Noice2"]
        # file_names = ["opa", "Noice"]
        
        def collect_checkpoint(self):
            pass

    print(CpTeste.get_file_paths("caraio"))