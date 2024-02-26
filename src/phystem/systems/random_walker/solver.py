import random
from math import pi, cos, sin

from phystem.core.solvers import SolverCore

class Solver(SolverCore):
    def __init__(self, pos0: list[float], vel0: list[float], noise_strength: float, size: int, dt: float) -> None:
        super().__init__()
        self.size = size

        # Configuração inicial do sistema
        self.pos = pos0
        self.vel = vel0
        
        self.noise_strength = noise_strength

        # Tamanho do passo temporal
        self.dt = dt

        # Tempo da simulação
        self.time = 0

    def update(self) -> None:
        # Atualização da posição
        self.pos[0] += self.dt * self.vel[0]
        self.pos[1] += self.dt * self.vel[1]
        
        # Atualização da velocidade
        # Rotaciona a mesma pelo ângulo d_angle
        d_angle = self.noise_strength * pi * (random.random() * 2 - 1)
        new_vx = cos(d_angle) * self.vel[0] + sin(d_angle) * self.vel[1]
        new_vy = -sin(d_angle) * self.vel[0] + cos(d_angle) * self.vel[1]
        
        self.vel[0] = new_vx
        self.vel[1] = new_vy

        # Implementação das bordas periódicas
        for i in range(2):
            if self.pos[i] > self.size/2:
                self.pos[i] = -self.size/2
            elif self.pos[i] < -self.size/2:
                self.pos[i] = self.size/2

        self.time += self.dt