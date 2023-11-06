from copy import deepcopy
from abc import ABC, abstractmethod

from ic_utils.timer import TimeIt
from phystem.core.run_config import RunType, RunCfg, CollectDataCfg
from phystem.core.creators import CreatorCore
from phystem.core.solvers import SolverCore

class SimulationCore(ABC): 
    '''
    Sistema base que controla a simulação do sistema físico para todos os modos de execução.
    '''
    def __init__(self, create_cfg, dynamic_cfg, space_cfg, run_cfg: RunCfg, rng_seed: float=None) -> None:
        '''
        Parameters:
        -----------
            create_cfg:
                Configurações relacionadas a criação da configuração inicial.
            
            dynamic_cfg:
                Configurações relacionadas a dinâmica entre os elementos do sistema.
            
            space_cfg:
                Configurações relacionadas ao espaço em que se encontram os elementos do sistema.
            
            run_cfg:
                Configurações relacionados ao modo de execução da integração do sistema.

            rng_seed:
                Seed para os geradores de números aleatórios.
        '''
        self.create_cfg = create_cfg
        self.space_cfg = space_cfg
        self.dynamic_cfg = dynamic_cfg
        self.run_cfg = run_cfg

        self.time_it = TimeIt(num_samples=200)

        self.rng_seed = rng_seed

        # Coleção contendo as configurações utilizadas para salvá-las.
        self.configs = {
            "create_cfg": deepcopy(create_cfg),
            "dynamic_cfg": deepcopy(dynamic_cfg),
            "space_cfg": deepcopy(space_cfg),
            "run_cfg": deepcopy(run_cfg),
            "rng_seed": deepcopy(rng_seed),
        }
        if run_cfg.id is RunType.COLLECT_DATA:
            # Como a configuração 'func' é uma função, ela não é salva.
            self.configs["run_cfg"].func = "nao salvo"

        self.init_sim()    

    @abstractmethod
    def get_creator(self) -> CreatorCore:
        pass

    @abstractmethod
    def get_solver(self) -> SolverCore:
        pass

    def init_sim(self) -> None:
        '''
        Inicializa a simulação realizando as seguintes tarefas:
        * Instanciar o `creator` e criar a configuração inicial.
        * Instanciar o `solver`.
        '''
        self.creator = self.get_creator()
        self.creator.create()

        self.solver = self.get_solver()

    def run(self):
        if self.run_cfg.id in RunType.REAL_TIME | RunType.SAVE_VIDEO | RunType.REPLAY_DATA:
            self.run_real_time()
        elif self.run_cfg.id is RunType.COLLECT_DATA:
            self.run_only_sim()

    def run_real_time(self):
        raise Exception("Mode de execução 'real_time' não implementado.")
    
    def run_only_sim(self):
        run_cfg: CollectDataCfg = self.run_cfg
        run_cfg.func(self, run_cfg.func_cfg)