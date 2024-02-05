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

class InvaginationCreator(CreatorCore):
    def __init__(self, num_rings: int, num_p: int, height: int, length: int, diameter: float,
        rng_seed: int = None) -> None:
        super().__init__(rng_seed)

        self.num_rings = num_rings
        self.height = height
        self.length = length
        self.diameter = diameter

        self.num_p = num_p
        

    def create(self) -> None:
        pos = np.zeros((self.num_rings, self.num_p, 2))
        # self_prop_angle = np.zeros((self.num_rings, self.num_p))
        self_prop_angle = np.random.random((self.num_rings, self.num_p)) * 2 * np.pi

        base_pos = np.zeros((self.num_p, 2))
        
        start_id = 0
        end_id = start_id + self.height
        base_pos[start_id:end_id, 0] = 0
        base_pos[start_id:end_id, 1] = np.linspace(1, 0, self.height)
        
        start_id = end_id-1
        end_id = start_id + self.length
        base_pos[start_id:end_id, 0] = np.linspace(0, 1, self.length)
        base_pos[start_id:end_id, 1] = 0
        
        start_id = end_id-1
        end_id = start_id + self.height
        base_pos[start_id:end_id, 0] = 1
        base_pos[start_id:end_id, 1] = np.linspace(0, 1, self.height)
        
        start_id = end_id-1
        end_id = start_id + self.length -1
        base_pos[start_id:end_id, 0] = np.linspace(1, 0, self.length)[:-1]
        base_pos[start_id:end_id, 1] = 1
        
        ring_length = (self.length - 1) * self.diameter
        ring_height = (self.height - 1) * self.diameter
        
        scale_matrix = np.array([[ring_length, 0], [0, ring_height]]) 
        base_pos = scale_matrix.dot(base_pos.T).T

        for i in range(self.num_rings):
            displacement = np.array([
                (ring_length + self.diameter) * i, 
                0, 
            ])

            pos[i] = base_pos + displacement

        center = np.array([self.num_rings * (ring_length + self.diameter) / 2 - self.diameter / 2 ,ring_height/2])
        pos -= center

        return InitData(pos, self_prop_angle)


class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    creator = InvaginationCreator(3, 4, 5, 1)

    pos = creator.create()
    for ring in pos:
        plt.scatter(*ring.T)

    plt.show()


