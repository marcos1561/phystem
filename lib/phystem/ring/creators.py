import numpy as np
from enum import Enum, auto

from phystem.core.creators import CreatorCore

class InitData:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, self_prop_angle: np.ndarray) -> None:
        '''
        Dados da configurações inicial.

        Parameters:
        -----------
            pos: ndarray (2, n)
                    Posição inicial das partículas (x, y)
                
            vel: ndarray (2, n)
                Velocidade inicial das partículas (vx, vy).
                
            self_prop_angle: ndarray (n)
                Ângulo inicial da direção da velocidade auto propulsora
        '''

        self.pos = pos
        self.vel = vel
        self.self_prop_angle = self_prop_angle
    
    def get_data(self):
        return {
            "pos": self.pos,
            "vel": self.vel,
            "self_prop_angle": self.self_prop_angle,
        }


class CreateType:
    NORMAL = auto()

class Creator(CreatorCore):
    def __init__(self, n: int, r: float, vo: float, angle: float, rng_seed: int = None) -> None:
        '''
        Cria a configuração inicial do anel em formato de círculo com as velocidades
        coincidindo com as velocidades autopropulsoras.

        A função `create` é responsável por gerar a configuração inicial. 
        
        Parameters:
        -----------
            n:
                Número de partículas no anel.
        
            r:
                Raio do anel.
            
            vo: 
                Magnitude da velocidade autopropulsora.

            angle:
                Ângulo inicial da velocidade auto propulsora.
            
            rng_seed:
                Seed utilizada na geração de número aleatório. Se for `None` é
                utilizado uma seed aleatória.
        '''
        super().__init__(rng_seed)

        self.n = n
        self.r = r
        self.vo = vo
        self.angle = angle

    # def create(self) -> InitData:
    #     trig_angle = np.pi/180*60
    #     pos = np.array([
    #         [0, 0],
    #         [self.r, 0],
    #         [np.cos(trig_angle)*self.r, np.sin(trig_angle)*self.r],
    #     ], dtype=np.float64)
    #     pos += np.array([2.5, 9])
    #     pos = pos.T

    #     size = 20
    #     pos = (pos + size/2) % 20 - 10

    #     self_prop_angle = self.angle * np.ones(3, dtype=np.float64)

    #     vel = self.vo * np.array([np.cos(self_prop_angle.copy()), np.sin(self_prop_angle.copy())])

    #     return InitData(pos, vel, self_prop_angle)

    def create(self) -> InitData:
        '''
        Cria a configuração inicial.
        
        Return:
        -------
            : InitData
                Dados da configuração inicial
        '''
        pos_angles = np.arange(0, np.pi*2, np.pi*2/self.n)
        
        if pos_angles.size != self.n:
            raise Exception(f"'pos_angle' tem tamanho '{pos_angles.size}', mas deveria ter '{self.n}'")

        pos = np.array([np.cos(pos_angles), np.sin(pos_angles)]) * self.r

        self_prop_angle = self.angle * np.ones(self.n, dtype=np.float64)

        vel = self.vo * np.array([np.cos(self_prop_angle.copy()), np.sin(self_prop_angle.copy())])

        return InitData(pos, vel, self_prop_angle)

class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass