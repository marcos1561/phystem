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
from enum import Flag, Enum, auto
import yaml, os

def load_cfg(cfg_path, is_recursive=False):
    with open(cfg_path, "r") as f:
        cfgs = yaml.unsafe_load(f)
    
    checkpoint: CheckpointCfg = cfgs["run_cfg"].checkpoint 
    if checkpoint and not is_recursive:
        checkpoint_cfg_path = os.path.join(checkpoint.folder_path, "config.yaml")
        if os.path.exists(checkpoint_cfg_path):
            checkpoint.configs = load_cfg(checkpoint_cfg_path, is_recursive=True)    
        else:
            checkpoint.configs = "configurações não encontradas"    

    return cfgs

class RunType(Flag):
    COLLECT_DATA = auto()
    REAL_TIME = auto()
    SAVE_VIDEO = auto()
    REPLAY_DATA = auto()

class SolverType(Enum):
    '''
    Tipo do solver a ser utilizado.
    '''
    PYTHON = auto()
    CPP = auto()

class CheckpointCfg:
    def __init__(self, folder_path: str, override_cfgs: bool = False) -> None:
        '''
        Parameters:
            folder_path:
                Caminho da pasta que contém o checkpoint.
            
            override_cfgs:
                Se for 'True', as configurações salvas no checkpoint serão ignoradas.
        '''
        self.folder_path = folder_path
        self.override_cfgs = override_cfgs

        self.configs: dict = None

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

class UiSettings:
    def __init__(self, window_scale=0.83, dpi=190, left_pannel_size=0.3) -> None:
        self.window_scale = window_scale
        self.dpi = dpi
        self.left_pannel_size = left_pannel_size

class RunCfg:
    '''
    Base para as configurações do mode de execução.
    
    Attributes:
    ----------
        id:
            Id identificando qual é o mode de execução .
    '''
    id: RunType
    def __init__(self, int_cfg: IntegrationCfg, checkpoint: CheckpointCfg = None) -> None:
        '''
        Parameters:
        -----------
            int_cfg:
                Configurações relacionadas a integração do sistema.
            
            checkpoint:
                Configurações para carregar um checkpoint. Caso seja 'none', o checkpoint
                não é carregado.
        '''
        self.int_cfg = int_cfg
        self.checkpoint = checkpoint
        
        if checkpoint is not None:
            # Carrega as configurações utilizadas nos dados salvos.
            with open(os.path.join(checkpoint.folder_path, "config.yaml"), "r") as f:
                self.checkpoint.configs = yaml.unsafe_load(f)
                
class CollectDataCfg(RunCfg):
    '''
    Modo de coleta de dados sem renderização ou informações
    não relevantes para a integração do sistema.
    '''
    id = RunType.COLLECT_DATA
    def __init__(self, int_cfg: IntegrationCfg, tf: float, folder_path: str, func_cfg=None, func: callable=None,
        func_id=None, get_func: callable=None, checkpoint: CheckpointCfg = None) -> None:
        '''
        Configurações da coleta de dados de acordo com um pipeline. A pipeline pode ser especificada de duas formas.

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
        self.folder_path = folder_path
        
        self.func = func
        self.func_id = func_id
        self.func_cfg = func_cfg 

        if func_id is not None:
            self.func = get_func(func_id) 

class RealTimeCfg(RunCfg):
    '''
    Renderização em tempo real da simulação.
    '''
    id = RunType.REAL_TIME
    def __init__(self, int_cfg: IntegrationCfg, num_steps_frame: int, fps: int, graph_cfg=None,
        ui_settings=UiSettings(), checkpoint: CheckpointCfg=None) -> None:
        '''
        Parameters:
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
        self.ui_settings = ui_settings
        self.num_steps_frame = num_steps_frame
        self.fps = fps
        self.graph_cfg = graph_cfg

class ReplayDataCfg(RealTimeCfg):
    '''
    Reproduz dados salvos utilizando a interface visual da renderização em tempo real.
    '''
    id = RunType.REPLAY_DATA

    def __init__(self, directory: str, data_dir="data", num_steps_frame=1, fps=30, 
        graph_cfg=None, solver_cfg=None,) -> None:
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
        # Carrega as configurações utilizadas nos dados salvos.
        cfg_path = os.path.join(directory, "config.yaml") 
        self.system_cfg = load_cfg(cfg_path)

        init_cfg = self.system_cfg["run_cfg"].int_cfg
        super().__init__(int_cfg=init_cfg, num_steps_frame=num_steps_frame, fps=fps, graph_cfg=graph_cfg)

        self.solver_cfg = solver_cfg
        self.directory = directory
        self.data_dir = os.path.join(directory, data_dir)
        
        self.system_cfg["run_cfg"] = self

class SaveCfg(RunCfg):
    '''
    Salva um vídeo da simulação.
    '''
    id = RunType.SAVE_VIDEO
    def __init__(self, int_cfg: IntegrationCfg, path:str, fps: int, speed: float=None, duration: float = None, 
        tf: float = None, ti=0, num_frames=None, graph_cfg=None, ui_settings=UiSettings(), checkpoint: CheckpointCfg=None,
        replay: ReplayDataCfg=None) -> None:  
        '''
        Salva um vídeo da simulação em `path`. Ao menos um dos seguintes parâmetros deve ser 
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
        super().__init__(int_cfg, checkpoint)
        self.ui_settings = ui_settings
        self.replay = replay

        if duration == None and tf == None:
            raise ValueError("Um dos parâmetros `duration` ou `tf` deve ser passado.")
        

        if speed == None: 
            if (duration is None or tf is None):
                raise ValueError(f"Se 'speed=None' então 'duration' e 'tf' devem ser passados.")

            speed = (tf - ti)/duration

        self.speed = speed
        self.path = path
        self.fps = fps
        self.graph_cfg = graph_cfg

        dt = self.int_cfg.dt
        self.set_num_steps_frame(speed, fps, dt)

        if duration != None:
            self.duration = duration
            self.num_frames = int(duration * fps)
            self.t = self.num_frames * self.num_steps_frame * dt
            # tf = s * d => s = tf/d  
        elif tf != None:
            self.t = tf - ti
            
            if num_frames is not None:
                self.num_frames = num_frames
                self.num_steps_frame = self.t/num_frames/dt
            else:
                self.num_frames = int(self.t / self.num_steps_frame / dt)

            self.duration = self.num_frames / self.fps

        print(self.duration)

    def set_num_steps_frame(self, speed, fps, dt):
        # n * dt * fps = t
        # n = t / (dt * fps)
        # s = t/d
        # n = (s * d) / (dt * fps)

        self.num_steps_frame = speed / fps / dt
        if self.num_steps_frame < 1:
            self.num_steps_frame = 1
            self.dt = self.speed/self.fps
        else:
            self.num_steps_frame = int(round(self.num_steps_frame))

