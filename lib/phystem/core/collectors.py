from abc import ABC, abstractmethod
import os, yaml

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