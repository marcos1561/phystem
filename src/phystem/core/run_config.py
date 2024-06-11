'''
Configurações e enumerações utilizadas na execução da simulação que não
são particulares à dinâmica do sistema.

Configurações do modo de execução
--------------------
RealTimeCfg:
    Renderização em tempo real da simulação.

CollectDataCfg:
    Coleta de dados da simulação (não inclui nada de renderização
    ou informações adicionais irrelevantes para a integração do sistema).

ReplayDataCfg:
    Reproduz dados coletados utilizando o mode de renderização
    em tempo real.

SaveCfg:
    Salva um vídeo da simulação.


Enumerações
-----------
    RunType:
        Modo de execução, cujas configurações estão listadas na seção
        "Configurações de execução".

    SolverType:
        Tipo do solver a ser utilizado
'''
from pathlib import Path
from enum import Flag, Enum, auto
import yaml, os, copy
from phystem.gui_phystem import config_ui
from . import settings


def load_configs(path: Path, load_checkpoint_cfgs=False):
    path = Path(path)
    
    if path.suffix == "":
        path = path.with_suffix(".yaml")

    with open(path, "r") as f:
        cfgs = yaml.unsafe_load(f)
        
    checkpoint: CheckpointCfg = cfgs["run_cfg"].checkpoint 
    if load_checkpoint_cfgs and checkpoint:
        try:
            checkpoint.configs = load_configs(Path(checkpoint.root_path) / "config.yaml")    
        except FileNotFoundError as e:
            checkpoint.configs = "configurações não encontradas" 
    return cfgs

def save_configs(configs: dict, path: Path):
    path = Path(path)
    if path.suffix == "":
        path = path.with_suffix(".yaml")
    
    with open(path, "w") as f:
        yaml.dump(configs, f)

class RunType(Flag):
    COLLECT_DATA = auto()
    REAL_TIME = auto()
    SAVE_VIDEO = auto()
    REPLAY_DATA = auto()

class SolverType(Enum):
    '''Tipo do solver a ser utilizado.'''
    PYTHON = auto()
    CPP = auto()

class CheckpointCfg:
    def __init__(self, root_path: str, override_cfgs: bool = False,
                 override_func_cfg=True, ignore_autosave=False) -> None:
        '''
        Parameters:
            root_path:
                Caminho da pasta que contém o checkpoint.
            
            override_cfgs:
                Se for 'True', as configurações salvas no checkpoint serão ignoradas.
            
            override_func_cfg:
                Apenas se aplica se o modo de execução for `CollectDataCfg`.
                Se for 'True', as configurações da pipeline salvas no checkpoint (`func_cfg`) serão ignoradas.

            ignore_autosave:
                Se for `True`, o checkpoint não é interpretado como auto-salvamento mesmo se ele for.    
        '''
        self.root_path = Path(root_path)
        self.override_cfgs = override_cfgs
        self.override_func_cfg = override_func_cfg
        self.ignore_autosave = ignore_autosave

        self.configs: dict = load_configs(self.root_path / "config")
    
    def get_sim_configs(self, run_cfg=None):
        configs = copy.deepcopy(self.configs)
        if run_cfg is not None:
            configs["run_cfg"] = run_cfg
        return configs
    
    def get_metadata(self):
        with open(os.path.join(self.root_path, "metadata.yaml")) as f:
            metadata = yaml.unsafe_load(f)
        return metadata
    
    @property
    def is_autosave(self):
        if self.ignore_autosave:
            return False
        else:
            return self.get_metadata().get(settings.autosave_flag_name, False)

class IntegrationCfg:
    def __init__(self, dt: float, solver_type=SolverType.CPP) -> None:
        '''
        Parameters:
        -----------
            dt:
                Passo temporal
            
            solver_type:
                Tipo do solver a ser utilizado.
        '''
        self.dt = dt
        self.solver_type = solver_type

class RunCfg:
    '''Base para as configurações do mode de execução.
    
    Attributes:
    ----------
        id:
            Id identificando qual é o modo de execução .
    '''
    id: RunType
    def __init__(self, int_cfg: IntegrationCfg, checkpoint: CheckpointCfg = None) -> None:
        '''
        Parameters:
        -----------
            int_cfg:
                Configurações relacionadas a integração do sistema.
            
            checkpoint:
                Configurações para carregar um checkpoint.
        '''
        self.int_cfg = int_cfg
        self.checkpoint = checkpoint
                
class CollectDataCfg(RunCfg):
    '''Modo de coleta de dados sem renderização ou informações
    não relevantes para a integração do sistema.
    '''
    id = RunType.COLLECT_DATA
    def __init__(self, int_cfg: IntegrationCfg, tf: float, folder_path: str, func_cfg=None, func: callable=None,
        func_id=None, get_func: callable=None, checkpoint: CheckpointCfg = None) -> None:
        '''Configurações da coleta de dados de acordo com um pipeline. A pipeline pode ser especificada de duas formas.

        * Diretamente especificando o parâmetro `func`.

        * Passando o id de uma pipeline (`func_id`) e uma função que retorna a pipeline por id (`get_func`).  

        A preferência é para pipelines passadas por id.
        
        Parameters:
        -----------
            int_cfg:
                Configurações relacionadas a integração do sistema.
            
            tf:
                Tempo final da integração.    
        
            folder_path:
                Caminho para a pasta que vai conter os dados salvos.
            
            func_cfg:
                Configurações utilizadas para a pipeline de coleta de dados.

            func:
                Pipeline de coleta de dados.
            
            func_id:
                Id de uma pipeline de coleta de dados.

            get_func:
                Retorna uma pipeline de coleta de dados dado um id. \n
                    func = get_func(func_id)
            
            checkpoint:
                Configurações para carregar um checkpoint. Casa seja 'None', o checkpoint
                não é carregado.
        '''
        if func_id is None and func is None:
            raise ValueError("'func_id' e 'func' não podem ser ambos nulos.")
        
        super().__init__(int_cfg, checkpoint)
        self.tf = tf
        self.folder_path = Path(folder_path)
        # self.folder_path.mkdir(parents=True, exist_ok=True)
        
        self.func = func
        self.func_id = func_id
        self.func_cfg = func_cfg 

        if func_id is not None:
            self.func = get_func(func_id) 

        if self.is_autosave:
            self.folder_path = self.checkpoint.root_path.parent
            print(f"CollectCfg Warning: Alterando 'folder_path' para '{self.folder_path}'")

    @property
    def is_autosave(self):
        return self.checkpoint is not None  and self.checkpoint.is_autosave

class RealTimeCfg(RunCfg):
    '''Renderização em tempo real da simulação.'''
    id = RunType.REAL_TIME
    def __init__(self, int_cfg: IntegrationCfg, num_steps_frame: int, fps: int=60, graph_cfg=None,
        ui_settings: config_ui.UiSettings=None, checkpoint: CheckpointCfg=None) -> None:
        '''
        Parameters:
        -----------
            int_cfg:
                Configurações relacionadas a integração do sistema.

            num_steps_frame:
                Quando passos temporais são dados por frame.
            
            fps:
                Determina o intervalo de tempo entre os frames.

            graph_cfg:
                Configurações passadas para o gerenciador do gráfico da simulação.
                
            checkpoint:
                Configurações para carregar um checkpoint. Casa seja 'None', o checkpoint
                não é carregado.
        '''
        super().__init__(int_cfg, checkpoint)
        if ui_settings is None:
            ui_settings = config_ui.UiSettings()

        
        if self.checkpoint is not None and not self.checkpoint.override_cfgs and self.int_cfg is None:
            self.int_cfg = self.checkpoint.configs["run_cfg"].int_cfg

        self.ui_settings = ui_settings
        self.num_steps_frame = num_steps_frame
        self.fps = fps
        self.graph_cfg = graph_cfg

class ReplayDataCfg(RealTimeCfg):
    '''Reproduz dados salvos utilizando a interface visual da renderização em tempo real.'''
    id = RunType.REPLAY_DATA

    def __init__(self, root_path: Path, data_dirname="data", num_steps_frame=1, fps=30, 
        graph_cfg=None, solver_cfg=None,  ui_settings: config_ui.UiSettings=None) -> None:
        '''
        Parameters:
        -----------
            directory:
                Pasta que contém os dados salvos.

            system_cfg:
                Lista das configurações relativas ao sistema que vão ser atualizadas com as 
                configurações utilizadas nos dados salvos. As configurações são as seguintes:\n
            
                -> creator_cfg\n
                -> dynamic_cfg\n
                -> space_cfg
                
            num_steps_frame:
                Número de passos temporais por frame.
            
            frequency:
                Número de frames entre atualização dos passos temporais.

            fps:
                Determina o intervalo de tempo entre os frames.
                            
            graph_cfg:
                Configurações passadas para o gerenciador do gráfico da simulação.
        '''
        self.root_path = Path(root_path)
        self.solver_cfg = solver_cfg

        self.data_path = self.root_path / data_dirname
        
        # Carrega as configurações utilizadas nos dados salvos.
        self.system_cfg = load_configs(self.root_path / "config")

        init_cfg = self.system_cfg["run_cfg"].int_cfg
        super().__init__(int_cfg=init_cfg, num_steps_frame=num_steps_frame, fps=fps, 
                         graph_cfg=graph_cfg, ui_settings=ui_settings)

        self.system_cfg["run_cfg"] = self

class SaveCfg(RunCfg):
    '''Salva um vídeo da simulação.'''
    id = RunType.SAVE_VIDEO
    def __init__(self, int_cfg: IntegrationCfg, path:str, fps: int, speed: float=None, duration: float = None, 
        tf: float = None, ti=0, num_frames=None, graph_cfg=None, dt=None, 
        ui_settings: config_ui.UiSettings=None, checkpoint: CheckpointCfg=None, replay: ReplayDataCfg=None) -> None:  
        '''Salva um vídeo da simulação em `path`. Ao menos um dos seguintes parâmetros deve ser 
        especificado:

        * duration
        * tf

        Quando um é especificado o outro é calculado automaticamente.
        Caso os dois sejam especificados, a prioridade é para `duration`.

        Parameters:
        -----------
            int_cfg:
                Configurações relacionadas a integração do sistema.
        
            path:
                Local completo para salvar o vídeo.
            
            speed:
                Velocidade com que acontece a simulação no vídeo. Por exemplo, `speed=2`
                significa que 1 segundo no vídeo corresponde a 2 unidades de tempo na simulação.
                OBS: Para valores muito pequenos, é possível que o `dt` seja modificado.
            
            fps:
                fps do vídeo.

            duration:
                Duração do vídeo em segundos.
            
            tf:
                Tempo final da simulação.
            
            graph_cfg:
                Configurações passadas para o gerenciador do gráfico da simulação.

            checkpoint:
                Configurações para carregar um checkpoint. Caso seja 'none', o checkpoint
                não é carregado.
        '''
        if duration is not None and speed is not None:
            tf = speed * duration + ti
        elif tf is not None and duration is not None:
            speed = (tf - ti)/duration
        elif tf is not None and speed is not None:
            duration = (tf -ti)/speed
        else:
            raise Exception((
                "Nenhuma configuração de parâmetros aceitáveis encontrada.\n"
                "As seguintes opções são válidas.\n"
                "   -> duration, speed.\n"
                "   -> tf, speed.\n"
                "   -> tf, duration.\n"
            ))
        
        super().__init__(int_cfg, checkpoint)
        
        if ui_settings is None:
            ui_settings = config_ui.UiSettings()

        self.ui_settings = ui_settings
        self.replay = replay
        self.path = Path(path)
        self.graph_cfg = graph_cfg

        if self.replay and graph_cfg is None:
            self.graph_cfg = self.replay.graph_cfg

        if dt is None:
            self.dt = self.int_cfg.dt
        else:
            self.dt = dt

        self.fps = fps
        self.duration = duration
        self.speed = speed 
        self.t = tf - ti

        self.num_steps_frame = self.t / (self.fps * self.duration * self.dt)
        if self.num_steps_frame < 1:
            self.num_steps_frame = 1
            self.dt = self.speed/self.fps
        else:
            self.num_steps_frame = int(round(self.num_steps_frame))

        self.num_frames = int(duration * fps)

        print("num_steps_frame:", self.num_steps_frame)
        print("duration:", self.duration)
        print("t:", self.t)
        print("speed:", self.speed)
