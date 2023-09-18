from abc import ABC, abstractmethod
import os, yaml
import numpy as np

from phystem.core.solvers import SolverCore

class Collector(ABC):
    '''
    Responsável pela coleta de dados gerados pelo solver.
    '''
    def __init__(self, path: str, configs: list) -> None:
        '''
        $\pi = 3.14$

        Parameters:
        -----------
            path:
                Caminho da pasta que vai conter os dados coletados.
            
            config:
                Lista com todas as configurações da simulação.\n
                Apenas utilizado para salver as configurações no fim da coleta,
                na mesma pasta dos dados com o nome 'config.yaml'.
        '''
        self.configs = configs
        self.path = path

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

    def save(self) -> None:
        '''
        Essa função deve salvar os dados coletados, por padrão ela salva 
        as configurações.
        '''
        config_path = os.path.join(self.path, "config.yaml")
        with open(config_path, "w") as f:
            yaml.dump(self.configs, f)

class State(Collector):
    def __init__(self, solver: SolverCore, path: str, configs: list, tf: float, dt: float, to=0.0, 
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
        super().__init__(path, configs)

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

        self.solver = solver

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