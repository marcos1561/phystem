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
    
    UpdateType:
        Tipo de atualização a ser utilizado pelo solver.

Outras configurações
--------------------
    CollectPlCfg:
'''
from enum import Flag, Enum, auto

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

class UpdateType(Enum):
    '''
    Modo de integração a ser utilizado pelo solver.

    Variants:
    ---------
        NORMAL:
            Integração normal, sem mágicas envolvidas.
        
        WINDOWS:
            Divide o espaço em janelas e mantém atualizado quem está em cada
            janela.
    '''
    NORMAL = auto()
    WINDOWS = auto()

class RunCfg:
    '''
    Base para as configurações do mode de execução.
    
    Attributes:
    ----------
        id:
            Id identificando qual é o mode de execução .
    '''
    id: RunType
    def __init__(self, dt: float, solver_type = SolverType.CPP, update_type = UpdateType.NORMAL) -> None:
        '''
        Parameters:
        -----------
            dt:
                Passo temporal
            
            solver_type:
                Tipo do solver a ser utilizado.
            
            update_type:
                Tipo de integração a ser utilizado pelo solver.
        '''
        self.dt = dt
        self.solver_type = solver_type
        self.update_type = update_type

class CollectDataCfg(RunCfg):
    '''
    Modo de coleta de dados sem renderização ou informações
    não relevantes para a integração do sistema.
    '''
    id = RunType.COLLECT_DATA
    def __init__(self, tf: float, dt: float, folder_path: str, func_cfg=None, func: callable=None, func_id=None, 
        get_func: callable=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        '''
        Configurações da coleta de dados de acordo com um pipeline. A pipeline pode ser especificada de duas formas.

        * Diretamente especificando o parâmetro `func`.

        * Passando o id de uma pipeline (`func_id`) e uma função que retorna a pipeline por id (`get_func`).  

        A preferência é para pipelines passadas por id.
        
        Parameters:
        -----------
            tf:
                Tempo final da integração.    
        
            dt:
                Passo temporal
            
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
                
            solver_type:
                Tipo do solver a ser utilizado.
            
            update_type:
                Tipo de integração a ser utilizado pelo solver.
        '''
        if func_id is None and func is None:
            raise ValueError("'func_id' e 'func' não podem ser ambos nulos.")
        
        super().__init__(dt, solver_type, update_type)
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
    def __init__(self, dt: float, num_steps_frame: int, fps: int, graph_cfg=None,
        solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        '''
        Parameters:
            dt:
                Passo temporal

            num_steps_frame:
                Quando passos temporais são dados por frame.
            
            fps:
                Determina o intervalo de tempo entre os frames.

            graph_cfg:
                Configurações passadas para o gerenciador do gráfico da simulação.
                
            solver_type:
                Tipo do solver a ser utilizado.
            
            update_type:
                Tipo de integração a ser utilizado pelo solver.
        '''
        super().__init__(dt, solver_type, update_type)
        self.num_steps_frame = num_steps_frame
        self.fps = fps
        self.graph_cfg = graph_cfg

class ReplayDataCfg(RealTimeCfg):
    '''
    Reproduz dados salvos utilizando a interface visual da renderização em tempo real.
    '''
    id = RunType.REPLAY_DATA

    def __init__(self, directory: str, system_cfg: dict, num_steps_frame=1, frequency=0, fps=30, graph_cfg=None) -> None:
        '''
        Parameters:
        -----------
            directory:
                Pasta que contém os dados salvos.

            system_cfg:
                Lista das configurações relativas ao sistema que vão ser atualizadas com as 
                configurações utilizadas nos dados salvos. As configurações são as seguintes:\n
            
                -> create_cfg\n
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
        import yaml, os

        # Carrega as configurações utilizadas nos dados salvos.
        with open(os.path.join(directory, "config.yaml"), "r") as f:
            cfg = yaml.unsafe_load(f)
        collect_cfg: CollectDataCfg = cfg["run_cfg"]

        dt = collect_cfg.dt
        super().__init__(dt=dt, num_steps_frame=num_steps_frame, fps=fps, graph_cfg=graph_cfg)

        # Seta as configurações da simulação com aquelas salvas nos dados.
        cfg_names = ("create_cfg", "dynamic_cfg", "space_cfg")
        for name in cfg_names:
            system_cfg[name].set(cfg[name])
        
        self.frequency = frequency
        self.directory = directory
        
class SaveCfg(RunCfg):
    '''
    Salva um vídeo da simulação.
    '''
    id = RunType.SAVE_VIDEO
    def __init__(self, path:str, speed: float, fps: int, dt: float, duration: float = None, tf: float = None, 
        graph_cfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:  
        '''
        Salva um vídeo da simulação em `path`. Ao menos um dos seguintes parâmetros deve ser 
        especificado:

        * duration
        * tf

        Quando um é especificado o outro é calculado automaticamente.
        Caso os dois sejam especificados, a prioridade é para `duration`.

        Parameters:
        -----------
            path:
                Local completo para salvar o vídeo.
            
            speed:
                Velocidade com que acontece a simulação no vídeo. Por exemplo, `speed=2`
                significa que 1 segundo no vídeo corresponde a 2 unidades de tempo na simulação.
                OBS: Para valores muito pequenos, é possível que o `dt` seja modificado.
            
            fps:
                fps do vídeo.
            
            dt:
                Passo temporal da simulação.

            duration:
                Duração do vídeo em segundos.
            
            tf:
                Tempo final da simulação.
            
            graph_cfg:
                Configurações passadas para o gerenciador do gráfico da simulação.
                
            solver_type:
                Tipo do solver a ser utilizado.
            
            update_type:
                Tipo de integração a ser utilizado pelo solver.
        '''
        super().__init__(dt, solver_type, update_type)
        if duration == None and tf == None:
            raise ValueError("Um dos parâmetros `duration` ou `tf` deve ser passado.")
        self.speed = speed
        self.path = path
        self.fps = fps
        self.dt = dt
        self.graph_cfg = graph_cfg

        self.num_steps_frame = speed / fps / dt
        if self.num_steps_frame < 1:
            self.num_steps_frame = 1
            self.dt = self.speed/self.fps
        else:
            self.num_steps_frame = int(round(self.num_steps_frame))

        if duration != None:
            self.duration = duration
            self.num_frames = int(duration * fps)
            self.tf = self.num_frames * self.num_steps_frame * self.dt
        elif tf != None:
            self.tf = tf
            self.num_frames = int(self.tf / self.num_steps_frame / self.dt)
            self.duration = self.num_frames / self.fps
