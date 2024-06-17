from abc import ABC, abstractmethod
import yaml, copy
from pathlib import Path

from phystem.core.solvers import SolverCore
from .autosave import AutoSavable
from . import settings

class ColAutoSaveCfg:
    def __init__(self, freq_dt: float, to_save_state=True) -> None:
        self.freq_dt = freq_dt
        self.to_save_state = to_save_state
    
class Collector(AutoSavable, ABC):
    '''Responsável pela coleta de dados gerados pelo solver.'''
    def __init__(self, solver: SolverCore, root_path: Path, configs: dict, 
        autosave_cfg: ColAutoSaveCfg=None, 
        data_dirname="data", exist_ok=False) -> None:
        '''
        Parameters:
        -----------
            solver:
                Solver do sistema em que será coletado os dados.
            
            path:
                Caminho da pasta raiz que irá conter todos os dados relativos
                a esse coletor. 
                
            config:
                Dicionário com todas as configurações da simulação.

            autosave_cfg:
                Configurações do auto-salvamento:
                
                * freq_dt:
                    Frequência temporal em que é feito o auto-salvamento.
                
                * to_save_state:
                    Se é para salvar o estado do sistema.
        '''
        self.root_path = Path(root_path)
        if settings.IS_TESTING:
            self.root_path.mkdir(parents=True, exist_ok=True)
        else:
            self.root_path.mkdir(parents=True, exist_ok=exist_ok)
        
        super().__init__(root_path)
        self.solver = solver
        self.configs = configs

        # Caminho do arquivo que contém as configurações utilizadas na simulação.
        self.configs_path = self.root_path / "config.yaml"

        self.data_path = None
        if data_dirname:
            self.data_path = self.root_path / data_dirname

        self.autosave_cfg = autosave_cfg
        self.autosave_last_time = self.solver.time
        
        # Caminho da pasta do auto-salvamento que contém os dados coletados. 
        self.autosave_data_path = self.autosave_root_path / "data"

        for p in [self.data_path, self.autosave_data_path]:
            if p:
                p.mkdir(parents=True, exist_ok=True)
        
        self.save_cfg(self.configs, self.configs_path)

    @property
    def vars_to_save(self):
        return [
            "autosave_last_time",
        ]

    @abstractmethod
    def collect(self) -> None:
        '''Realiza a coleta dos dados no instante atual.'''
        pass

    def check_autosave(self):
        '''Realiza o auto-salvamento de acordo com a frequência definida.'''
        if self.solver.time - self.autosave_last_time > self.autosave_cfg.freq_dt:
            self.autosave_last_time = self.solver.time
            self.exec_autosave()

    @staticmethod
    def save_cfg(configs: dict[str], configs_path: Path) -> None:
        '''Salva as configurações da simulação.'''
        configs = copy.deepcopy(configs)
        configs["run_cfg"].func = "nao salvo"
        
        # Impede o salvamento de todos os checkpoints utilizados
        # caso seja salvado um checkpoint que foi carregado de outro checkpoint.
        if configs["run_cfg"].checkpoint:
            configs["run_cfg"].checkpoint.configs = "nao salvo"
        
        with open(configs_path, "w") as f:
            yaml.dump(configs, f)

