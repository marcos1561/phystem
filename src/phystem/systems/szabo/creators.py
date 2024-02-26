import numpy as np

from phystem.core.creators import CreatorCore
from phystem.systems.szabo.configs import CreateType

class Particles(CreatorCore):
    def __init__(self, n: int, r: float, space_type: CreateType, rng_seed=None) -> None:
        '''
        Cria a configuração inicial das partículas, atribuindo de forma aleatório as posições
        e velocidades. O formato do espaço na qual as partículas são colocadas pode ser configurado
        em `space_type`.

        OBS: As velocidades possuem módulo 1 e direção aleatória.
        
        Parameters:
        -----------
            n:
                Número de partículas.
            
            r:
                Raio do espaço na qual as partículas serão colocadas.
            
            space_type: {CIRCLE, SQUARE}
                Tipo do espaço na qual as partículas serão colocadas.
            
            rng_seed:
                Seed utilizada na geração de número aleatório. Se for `None` é
                utilizado uma seed aleatória.
        '''
        super().__init__(rng_seed)

        self.n = n
        self.r = r
        self.space_type = space_type

        self.pos: np.ndarray
        self.vel: np.ndarray

        self.space_type_to_func = {
            CreateType.CIRCLE: self.circle,
            CreateType.SQUARE: self.square,
        }

    def create(self):
        self.space_type_to_func[self.space_type]()

    def square(self):
        r = self.r

        x, y = r * (self.rng.random((2, self.n)) * 2 - 1)
        self.pos = np.array([x, y], dtype=np.float64)

        theta = self.rng.random(self.n) * 2 *np.pi
        self.vel = np.array([np.cos(theta), np.sin(theta)], dtype=np.float64)

    def circle(self):
        r = self.r

        x, y = r* (self.rng.random((2, self.n*30)) * 2 - 1)
        filter = x**2 + y**2 < r
        self.pos = np.array([x[filter], y[filter]], dtype=np.float64)[:,:self.n]

        theta = self.rng.random(self.n) * 2 *np.pi
        self.vel = np.array([np.cos(theta), np.sin(theta)], dtype=np.float64)

class CreatorRD(CreatorCore):
    def create(self) -> None:
        pass