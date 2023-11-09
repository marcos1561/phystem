import numpy as np
from enum import Enum, auto

from phystem.core.creators import CreatorCore

class InitData:
    def __init__(self, pos: np.ndarray, vel: np.ndarray, self_prop_angle: np.ndarray) -> None:
        '''
        Dados da configurações inicial.

        Parameters:
        -----------
            pos: ndarray (num_rings, 2, num_particles)
                    Posição inicial das partículas (x, y)
                
            vel: ndarray (num_rings, 2, num_particles)
                Velocidade inicial das partículas (vx, vy).
                
            self_prop_angle: ndarray (num_rings, n)
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
    def __init__(self, num_rings: int, num_p: int, r: list[float], vo: list[float], angle: list[float], center: list, state_folder: str=None, rng_seed: int = None) -> None:
        '''
        Cria a configuração inicial do anel em formato de círculo com as velocidades
        coincidindo com as velocidades autopropulsoras.

        OBS: A função `create` é responsável por gerar a configuração inicial. 
        
        Parameters:
        -----------
            num_rings:
                Número de anéis.
            
            num_p:
                Número de partículas no anel.
        
            r:
                Raio do anel.
            
            vo: 
                Magnitude da velocidade autopropulsora.

            angle:
                Ângulo inicial da velocidade auto propulsora.

            center:
                Centro da posição inicial do anel.
            
            state_folder:
                Caminho para a pasta contendo os dados do estado do sistema no qual a configuração inicial 
                será setada.  

            rng_seed:
                Seed utilizada na geração de número aleatório. Se for `None` é
                utilizado uma seed aleatória.
        '''
        super().__init__(rng_seed)

        self.num_rings = num_rings
        self.num_p = num_p
        self.r = r
        self.vo = vo
        self.angle = angle
        self.center = center
        self.state_path = state_folder

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
        if self.state_path:
            init_data = self.from_state()
            return init_data
        
        pos = []
        vel = []
        self_prop_angle = []

        for ring_id in range(self.num_rings):
            ring_pos_angles = np.arange(0, np.pi*2, np.pi*2/self.num_p)
            
            if ring_pos_angles.size != self.num_p:
                raise Exception(f"'pos_angle' tem tamanho '{ring_pos_angles.size}', mas deveria ter '{self.num_p}'")

            ring_pos = np.array([np.cos(ring_pos_angles), np.sin(ring_pos_angles)]) * self.r[ring_id]

            ring_pos[0] += self.center[ring_id][0]
            ring_pos[1] += self.center[ring_id][1]

            ring_self_prop_angle = self.angle[ring_id] * np.ones(self.num_p, dtype=np.float64)

            ring_vel = self.vo[ring_id] * np.array([np.cos(ring_self_prop_angle.copy()), np.sin(ring_self_prop_angle.copy())])

            pos.append(ring_pos)
            vel.append(ring_vel)
            self_prop_angle.append(ring_self_prop_angle)

        return InitData(np.array(pos), np.array(vel), np.array(self_prop_angle))

    def from_state(self):
        # pos = np.load()
        pass

class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass