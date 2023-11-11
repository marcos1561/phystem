from abc import ABC, abstractmethod

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.text import Text


class ParticlesGraph:
    def __init__(self, ax: Axes, pos, space_size: float) -> None:
        '''
        Gráfico para um conjunto de partículas. As partículas são
        representadas como pontos.

        OBS: É assumido que o espaço é um quadrado.

        Parâmetros:
        ------------
        ax:
            Axes na qual as partículas serão renderizadas.
        
        pos:
            Referência a posição das partículas. Deve possui a posição
            das partículas de forma sequencial, ou seja, pos[i] é a posição
            da i-ésima partícula.

        space_size:
            Lado do espaço.
        '''
        self.ax = ax
        self.space_size = space_size

        self.particles: PatchCollection = None
        
        self.pos = pos
    
    def init(self):
        r = self.space_size/2
        r_scale = 1
        self.ax.set_ylim(-r_scale*r, r_scale*r)
        self.ax.set_xlim(-r_scale*r, r_scale*r)

        self.ax.set_aspect(1)

        self.ax.plot([-r, r], [-r, -r], color="black")
        self.ax.plot([-r, r], [r, r], color="black")
        self.ax.plot([r, r], [-r, r], color="black")
        self.ax.plot([-r, -r], [-r, r], color="black")

        x, y = self.pos
        self.particles = self.ax.scatter(x, y, color="Black")

    def update(self):
        self.particles.set_offsets(np.array(self.pos).T)
        return self.particles,
    
class Info(ABC):
    def __init__(self, ax: Axes) -> None:
        self.ax = ax
        self.text: Text = None

    @abstractmethod    
    def get_info(self) -> str:
        pass

    def init(self):
        s = self.get_info()
        self.text = self.ax.text(0.01, 1-0.01, s,
            horizontalalignment='left',
            verticalalignment='top',
            transform=self.ax.transAxes)

    def update(self):
        s = self.get_info()
        self.text.set_text(s)
