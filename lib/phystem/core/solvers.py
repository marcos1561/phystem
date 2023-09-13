from abc import ABC, abstractmethod

class SolverCore:
    '''
    Responsável pela integração do sistema.
    '''
    def __init__(self) -> None:
        self.dt: float
        self.time: float

    @abstractmethod
    def update(self) -> None:
        '''
        Deve avançar o sistema em um passo temporal
        '''
        pass