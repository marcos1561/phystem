from copy import deepcopy
from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
import os, yaml

from phystem.utils.timer import TimeIt
from phystem.core.run_config import RunType, RunCfg, CollectDataCfg, SaveCfg, RealTimeCfg
from phystem.core.creators import CreatorCore
from phystem.core.solvers import SolverCore

class SimulationCore(ABC): 
    '''
    Sistema base que controla a simulação do sistema físico para todos os modos de execução.
    '''
    def __init__(self, creator_cfg, dynamic_cfg, space_cfg, run_cfg: RunCfg, other_cfgs: dict=None, rng_seed: float=None) -> None:
        '''
        Parameters:
        -----------
            creator_cfg:
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
        self.creator_cfg = creator_cfg
        self.space_cfg = space_cfg
        self.dynamic_cfg = dynamic_cfg
        self.run_cfg = run_cfg
        self.other_cfgs = other_cfgs
        self.rng_seed = rng_seed
        
        if self.run_cfg.checkpoint:
            if not self.run_cfg.checkpoint.override_cfgs:
                checkpoint_cfgs = self.run_cfg.checkpoint.configs
                self.creator_cfg = checkpoint_cfgs["creator_cfg"]
                self.space_cfg = checkpoint_cfgs["space_cfg"]
                self.dynamic_cfg = checkpoint_cfgs["dynamic_cfg"]
                self.other_cfgs = checkpoint_cfgs["other_cfgs"]
                self.rng_seed = checkpoint_cfgs["rng_seed"]

        self.configs_container = {
            "creator_cfg": self.creator_cfg,
            "dynamic_cfg": self.dynamic_cfg,
            "space_cfg": self.space_cfg,
            "run_cfg": self.run_cfg,
            "other_cfgs": self.other_cfgs,
            "rng_seed": self.rng_seed,
        }


        # Coleção contendo as configurações utilizadas para salvá-las.
        self.configs = {name: deepcopy(cfg) for name, cfg in self.configs_container.items()}
        # self.configs = {
        #     "creator_cfg": deepcopy(creator_cfg),
        #     "dynamic_cfg": deepcopy(dynamic_cfg),
        #     "space_cfg": deepcopy(space_cfg),
        #     "run_cfg": deepcopy(run_cfg),
        #     "rng_seed": deepcopy(rng_seed),
        # }

        if run_cfg.id is RunType.COLLECT_DATA:
            # Como a configuração 'func' é uma função, ela não é salva.
            self.configs["run_cfg"].func = "nao salvo"

        self.time_it = TimeIt(num_samples=200)

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

    def run_animation(self, fig: Figure, update):
        '''
        Começa a animação em tempo rela da integração do sistema.

        Parâmetros:
            fig: 
                'Figure' do matplotlib.

            update:
                Função que atualiza um frame do vídeo.
        '''
        real_time_cfg: RealTimeCfg = self.run_cfg

        ani = animation.FuncAnimation(fig, update, interval=1/(real_time_cfg.fps)*1000, cache_frame_data=False)
        plt.show()

    def save_video(self, fig: Figure, update):
        '''
        Salva um vídeo da simulação de acordo com as configurações dadas.

        Parâmetros:
            fig: 
                'Figure' do matplotlib.

            update:
                Função que atualiza um frame do vídeo.
        '''
        from phystem.utils.progress import MplAnim as Progress
        
        save_video_cfg: SaveCfg = self.run_cfg
        
        folder_path = save_video_cfg.path.split("/")[0]
        video_name = save_video_cfg.path.split("/")[-1].split(".")[0]
        if not os.path.exists(folder_path):
            raise Exception(f"O caminho {folder_path} não existe.")

        frames = save_video_cfg.num_frames
        progress = Progress(frames, 10)
        ani = animation.FuncAnimation(fig, update, frames=frames)

        config_path = os.path.join(folder_path, f"{video_name}_config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(self.configs, f)
        ani.save(save_video_cfg.path, fps=save_video_cfg.fps, progress_callback=progress.update)
