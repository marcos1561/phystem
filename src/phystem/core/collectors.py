from abc import ABC, abstractmethod
import yaml, copy
from pathlib import Path

from phystem.core.solvers import SolverCore
from .autosave import AutoSavable

class ColAutoSaveCfg:
    def __init__(self, freq_dt: float, to_save_state=True) -> None:
        self.freq_dt = freq_dt
        self.to_save_state = to_save_state
    
class Collector(AutoSavable, ABC):
    '''Responsável pela coleta de dados gerados pelo solver.'''
    def __init__(self, solver: SolverCore, path: str | Path, configs: dict, autosave_cfg: ColAutoSaveCfg=None, data_dirname="data") -> None:
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
        super().__init__(path)
        
        self.solver = solver
        self.configs = configs
        self.path = Path(path)

        # Caminho do arquivo que contém as configurações utilizadas na simulação.
        self.configs_path = self.path / "config.yaml"
        self.data_path = self.path / data_dirname

        self.autosave_cfg = autosave_cfg
        self.autosave_last_time = self.solver.time
        
        # Caminho da pasta do auto-salvamento que contém os dados coletados. 
        self.autosave_data_path = self.autosave_root_path / "data"

        for p in [self.data_path, self.autosave_data_path]:
            p.mkdir(parents=True, exist_ok=True)
        
        self.save_cfg(self.configs, self.configs_path)

    @abstractmethod
    def collect(self) -> None:
        '''Realiza a coleta dos dados no instante atual.

        Parameters:
        -----------
            count:
                Contador do número de passos temporais que já foram dados.
        '''
        pass

    # @property
    # def vars_to_save(self) -> list[str]:
    #     '''Nome dos atributos para serem salvas no auto-salvamento'''
    #     raise Exception("'vars_to_save' não foi definido.")

    # def get_vars_to_save(self):
    #     return {name: getattr(self, name) for name in self.vars_to_save}
    
    # def set_vars_to_save(self, values: dict):
    #     for name, value in values.items():
    #         setattr(self, name, value)

    def check_autosave(self):
        '''Realiza o auto-salvamento de acordo com a frequência definida.'''
        if self.solver.time - self.autosave_last_time > self.autosave_cfg.freq_dt:
            self.autosave_last_time = self.solver.time
            self.autosave()

    # def autosave(self):
    #     super().autosave()
    
    #     if self.autosave_cfg.to_save_state:
    #         self.state_col.save(metadata={
    #             "is_autosave": True,
    #             "time": self.solver.time,
    #             "num_time_steps": self.solver.num_time_steps,
    #         })


    # def autosave(self):
    #     '''Salva o seu estado atual. Também pode salvar o estado do sistema se,
    #     nas configurações de auto-salvamento, o coletor for configurado para tal.
    #     '''
    #     super().autosa
    #     # super().auto
    #     # with open(self.autosave_state_path / self.save_name, "wb") as f:
    #     #     pickle.dump(self.get_vars_to_save(), f)

    #     if self.autosave_cfg.to_save_state:
    #         self.state_col.save(metadata={
    #             "is_autosave": True,
    #             "time": self.solver.time,
    #             "num_time_steps": self.solver.num_time_steps,
    #         })
    
    # def load_autosave(self):
    #     with open(self.autosave_state_path / self.save_name, "rb") as f:
    #         saved_vars = pickle.load(f)
    #         self.set_vars_to_save(saved_vars)

    @staticmethod
    def save_cfg(configs: dict[str], configs_path: str | Path) -> None:
        '''Salva as configurações da simulação.'''
        configs = copy.deepcopy(configs)
        configs["run_cfg"].func = "nao salvo"
        
        # Impede o salvamento de todos os checkpoints utilizados
        # caso seja salvado um checkpoint que foi carregado de outro checkpoint.
        if configs["run_cfg"].checkpoint:
            configs["run_cfg"].checkpoint.configs = "nao salvo"
        
        with open(configs_path, "w") as f:
            yaml.dump(configs, f)
