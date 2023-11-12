import numpy as np

from phystem.core.creators import CreatorCore

class InitData:
    def __init__(self, pos: np.ndarray, self_prop_angle: np.ndarray) -> None:
        '''
        Dados da configurações inicial.

        Parameters:
        -----------
            pos: ndarray (num_rings, num_particles, 2)
                    Posição inicial das partículas em cada anel.
                
            self_prop_angle: ndarray (num_rings, n)
                Ângulo inicial da direção da velocidade auto propulsora em cada anel.
        '''

        self.pos = pos
        self.self_prop_angle = self_prop_angle
    
    def get_data(self):
        return {
            "pos": self.pos,
            "self_prop_angle": self.self_prop_angle,
        }


class Creator(CreatorCore):
    def __init__(self, num_rings: int, num_p: int, r: list[float], angle: list[float], center: list, 
        rng_seed: int = None) -> None:
        '''
        Cria a configuração inicial do anel em formato de círculo com todas as 
        velocidades auto propulsoras iguais.

        OBS: A função `create` é responsável por gerar a configuração inicial. 
        
        Parameters:
        -----------
            num_rings:
                Número de anéis.
            
            num_p:
                Número de partículas no anel.
        
            r:
                Raio do anel.
            
            angle:
                Ângulo inicial da velocidade auto propulsora.

            center:
                Centro da posição inicial do anel.
            
            rng_seed:
                Seed utilizada na geração de número aleatório. Se for `None` é
                utilizado uma seed aleatória.
        '''
        super().__init__(rng_seed)

        self.num_rings = num_rings
        self.num_p = num_p
        self.r = r
        self.angle = angle
        self.center = center

    def create(self) -> InitData:
        '''
        Cria a configuração inicial.
        
        Return:
        -------
            : InitData
                Dados da configuração inicial
        '''
        pos = []
        self_prop_angle = []

        for ring_id in range(self.num_rings):
            ring_pos_angles = np.arange(0, np.pi*2, np.pi*2/self.num_p)
            
            if ring_pos_angles.size != self.num_p:
                raise Exception(f"'pos_angle' tem tamanho '{ring_pos_angles.size}', mas deveria ter '{self.num_p}'")

            ring_pos = np.array([np.cos(ring_pos_angles), np.sin(ring_pos_angles)]) * self.r[ring_id]

            ring_pos[0] += self.center[ring_id][0]
            ring_pos[1] += self.center[ring_id][1]

            ring_self_prop_angle = self.angle[ring_id] * np.ones(self.num_p, dtype=np.float64)

            pos.append(ring_pos.T)
            self_prop_angle.append(ring_self_prop_angle)

        return InitData(np.array(pos), np.array(self_prop_angle))

class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass