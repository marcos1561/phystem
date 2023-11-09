from phystem.core.creators import CreatorCore
import random
from math import pi, cos, sin

class Creator(CreatorCore):
    def __init__(self, speed: float,  size: int, rng_seed: int = None) -> None:
        super().__init__(rng_seed)
        self.speed = speed # Rapidez do caminhante.
        self.size = size # Tamanho do lado do espaço do sistema.

    def create(self):
        # Posição inicial
        x = self.size/2 * (random.random() * 2 - 1)
        y = self.size/2 * (random.random() * 2 - 1)
        self.pos = [x, y]

        # Velocidade inicial
        angle = 2* pi * random.random()
        self.vel = [self.speed * cos(angle), self.speed * sin(angle)]

        config = [self.pos, self.vel]
        return config