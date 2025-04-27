import numpy as np
from abc import  ABC, abstractmethod

class CreatorCore(ABC):
    '''
    Responsável pela criação da configurações inicial do sistema.
    '''
    def __init__(self, rng_seed: int=None) -> None:
        '''
        Parameters:
        -----------
            rng_seed:
                seed utilizada na geração de número aleatório. Se for `None` é
                utilizado uma seed aleatória.
        '''
        # Gerador de números aleatórios
        self.rng = np.random.default_rng(rng_seed)

        self.pos = None
        self.vel = None
    
    @abstractmethod
    def create(self) -> None:
        '''
        Deve criar a configurações inicial do sistema.
        '''
        pass
