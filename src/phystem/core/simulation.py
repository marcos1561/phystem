from copy import deepcopy
from abc import ABC, abstractmethod
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
import os, yaml

from phystem.utils.timer import TimeIt
from phystem.core.run_config import RunType, RunCfg, CollectDataCfg, SaveCfg, RealTimeCfg, save_configs, load_configs
from phystem.core.creators import CreatorCore
from phystem.core.solvers import SolverCore

from phystem.gui_phystem.application import AppCore
from phystem.gui_phystem import config_ui
from phystem.gui_phystem import control_ui

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
            checkpoint_cfgs = self.run_cfg.checkpoint.configs
            
            if not self.run_cfg.checkpoint.override_cfgs:
                self.run_cfg.int_cfg = checkpoint_cfgs["run_cfg"].int_cfg 
                if type(self.run_cfg) is CollectDataCfg and not self.run_cfg.checkpoint.override_func_cfg:
                     self.run_cfg.func_cfg = checkpoint_cfgs["run_cfg"].func_cfg

                self.creator_cfg = checkpoint_cfgs["creator_cfg"]
                self.space_cfg = checkpoint_cfgs["space_cfg"]
                self.dynamic_cfg = checkpoint_cfgs["dynamic_cfg"]
                self.other_cfgs = checkpoint_cfgs["other_cfgs"]
                self.rng_seed = checkpoint_cfgs["rng_seed"]
            else:
                # Mesmo sobrescrevendo as configurações, está sendo carregado um estado
                # que foi gerado com as configurações do checkpoint.
                self.creator_cfg = checkpoint_cfgs["creator_cfg"]

        self.adjust_configs()

        self.configs = {
            "creator_cfg": self.creator_cfg,
            "dynamic_cfg": self.dynamic_cfg,
            "space_cfg": self.space_cfg,
            "run_cfg": self.run_cfg,
            "other_cfgs": self.other_cfgs,
            "rng_seed": self.rng_seed,
        }

        # Cópia das configurações inciais.
        self.init_configs = {name: deepcopy(cfg) for name, cfg in self.configs.items()}

        if run_cfg.id is RunType.COLLECT_DATA:
            # Como a configuração 'func' é uma função, ela não é salva.
            self.init_configs["run_cfg"].func = "nao salvo"

        if run_cfg.checkpoint:
            # Impede o salvamento de todos os checkpoints utilizados
            # caso seja salvado um checkpoint que foi carregado de outro checkpoint.
            self.init_configs["run_cfg"].checkpoint.configs = "nao salvo"

        self.app: AppCore = None
        self.time_it = TimeIt(funcs_names=["solver", "graph"], num_samples=5)

        self.init_sim()    

    def adjust_configs(self):
        '''Função para ajustar os valores das configurações caso necessário.'''
        pass

    def save_configs(self, path):
        save_configs(self.configs, path)

    @classmethod
    def load_from_configs(cls, path: Path):
        cfgs = load_configs(path)
        return cls(**cfgs)

    @staticmethod
    def configs_from_checkpoint(run_cfg: RunCfg):
        cfgs = deepcopy(run_cfg.checkpoint.configs) 
        if run_cfg.int_cfg is None:
            run_cfg.int_cfg = cfgs["run_cfg"].int_cfg
        cfgs["run_cfg"] = run_cfg
        return cfgs

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
        
        if type(run_cfg.func) == str or run_cfg.func is None:
            raise Exception((
                "A função que executa a simulação não está setada! "
                "(Atributo 'func' da configuração 'CollectDataCfg')",
            ))
        
        run_cfg.func(self, run_cfg.func_cfg)

    def run_app(self, fig: Figure, update, title=None, ui_settings: config_ui.UiSettings=None):
        self.app = AppCore(fig, self.configs, self.solver, self.time_it, 
            update, title, ui_settings)
        self.app.run()

    def run_mpl_animation(self, fig: Figure, update):
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
        import time

        t1 = time.time()

        save_video_cfg: SaveCfg = self.run_cfg
        
        save_video_cfg.path.parent.mkdir(parents=True, exist_ok=True)
        
        # folder_path = save_video_cfg.path.split("/")[0]
        # video_name = save_video_cfg.path.split("/")[-1].split(".")[0]
        # folder_path = os.path.dirname(save_video_cfg.path)
        # video_name = os.path.splitext(os.path.basename(save_video_cfg.path))[0]
        # if not os.path.exists(folder_path):
        #     raise Exception(f"O caminho {folder_path} não existe.")

        frames = save_video_cfg.num_frames
        progress = Progress(frames, 10)
        ani = animation.FuncAnimation(fig, update, frames=frames)

        self.save_configs(save_video_cfg.path.parent / (save_video_cfg.path.stem + "_config"))
        ani.save(save_video_cfg.path, fps=save_video_cfg.fps, progress_callback=progress.update)

        t2 = time.time()
        from datetime import timedelta
        print("Elapsed time:", timedelta(seconds=t2-t1))