from phystem.core import run_config
from phystem.core.run_config import SolverType, UpdateType

class GraphCfg:
    '''
    Configurações do gráfico das partículas.
    '''
    def __init__(self, show_circles=False) -> None:
        self.show_circles = show_circles

class CollectDataCfg(run_config.CollectDataCfg):
    def __init__(self, tf: float, dt: float, folder_path: str, num_windows: int=None, func_cfg=None, 
        func: callable = None, func_id=None, get_func: callable = None, solver_type=SolverType.CPP, 
        update_type=UpdateType.NORMAL) -> None:
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
            
            num_windows:
                Número de janelas na qual o espaço é dividido. Aplicável se `update_type=Windows`. 

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
        if update_type == UpdateType.WINDOWS and num_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(tf, dt, folder_path, func_cfg, func, func_id, get_func, solver_type, update_type)

        self.num_windows = num_windows

class RealTimeCfg(run_config.RealTimeCfg):
    def __init__(self, dt: float, num_steps_frame: int, fps: int, num_windows: int=None, graph_cfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
        if update_type == UpdateType.WINDOWS and num_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")
        '''
        Parameters:
            dt:
                Passo temporal

            num_windows:
                Número de janelas na qual o espaço é dividido. Aplicável se `update_type=Windows`. 
                
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
        if update_type == UpdateType.WINDOWS and num_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(dt, num_steps_frame, fps, graph_cfg, solver_type, update_type)
        self.num_windows = num_windows

class SaveCfg(run_config.SaveCfg):
    def __init__(self, path: str, speed: float, fps: int, dt: float, num_windows:int=None, duration: float = None, tf: float = None, graph_cfg=None, solver_type=SolverType.CPP, update_type=UpdateType.NORMAL) -> None:
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
            
            num_windows:
                Número de janelas na qual o espaço é dividido. Aplicável se `update_type=Windows`. 

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
        if update_type == UpdateType.WINDOWS and num_windows is None:
            raise ValueError("'num_windows' deve ser especificado.")

        super().__init__(path, speed, fps, dt, duration, tf, graph_cfg, solver_type, update_type)
        self.num_windows = num_windows
