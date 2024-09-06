
from abc import ABC, abstractmethod

import numpy as np
from phystem.systems.ring.solvers import CppSolver
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.colorbar import Colorbar

class CustomColors(ABC):
    "Classe base para calcular as cores dos anéis."
    
    def __init__(self, cmap, colorbar_kwargs=None) -> None:
        if colorbar_kwargs is None:
            colorbar_kwargs = {}
        
        self.cmap = cmap
        self.colorbar_kwargs = colorbar_kwargs
        self.colorbar: Colorbar = None

    @abstractmethod
    def update(self):
        "Atualiza `self.colors_value` e `self.colors_rgb`"
        pass

    def add_colorbar(self, ax: Axes):
        if self.colorbar is None:
            self.colorbar = ax.figure.colorbar(self.cmap, ax=ax, **self.colorbar_kwargs)
            self.ax = ax
    def remove_colorbar(self):
        if self.colorbar is not None:
            self.colorbar.remove()
            self.ax.set_anchor("C")
            self.colorbar = None

class ActiveRings:
    def __init__(self, num_particles: int, solver: CppSolver, custom_colors:CustomColors=None, use_custom_colors=False):
        self.solver = solver
        self.custom_colors = custom_colors
        
        self.use_custom_colors = use_custom_colors

        self.num_particles = num_particles
        self.total_num_particles = num_particles * solver.num_max_rings

        total_num_particles = solver.num_max_rings * num_particles
        self._pos = np.empty((total_num_particles, 2), dtype=float)
        self._ids = np.empty(solver.num_max_rings, dtype=int)
        
        self.cmap = cm.tab20
        self._colors_value, self._colors_rgb = self.create_colors(solver.num_max_rings, num_particles, self.cmap)

        self.has_updated_ids = False
        self.has_updated_pos = False
        self.has_updated_cms = False
        self.has_updated_pos_continuos = False

    def create_colors(self, num_rings, num_particles, cmap):
        c = np.zeros((num_rings, num_particles), dtype=int)
        color_id = np.random.choice(range(len(cmap.colors)), num_rings)
        for i in range(num_rings):
            c[i] = color_id[i]
        c = c / (len(cmap.colors) - 1)

        rgb = cmap(c)
        return c, rgb

    @property
    def num_active(self):
        return self.solver.num_active_rings

    @property
    def num_particles_active(self):
        return self.solver.num_active_rings * self.num_particles

    @property
    def pos(self):
        if self.has_updated_pos:
            return self._pos
        self.has_updated_pos = True
        
        pos = np.array(self.solver.pos)[self.ids]
        self._pos = pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])
        return self._pos

    @property
    def ids(self):
        if self.has_updated_ids:
            return self._ids
        self.has_updated_ids = True
        
        self._ids = self.solver.rings_ids[:self.num_active]
        return self._ids
    
    @property
    def pos_continuos(self):
        if self.has_updated_pos_continuos:
            return self._pos_continuos
        self.has_updated_pos_continuos = True
        
        pos = np.array(self.solver.pos_continuos)[self.ids]
        self._pos_continuos = pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])
        return self._pos_continuos

    @property
    def cms(self):
        if self.has_updated_cms:
            return self._cms
        self.has_updated_cms = True
        
        self._cms = np.array(self.solver.center_mass)[self.ids]
        return self._cms

    @property
    def colors_value(self):
        if self.use_custom_colors:
            return self.custom_colors.colors_value
        return self._colors_value[self.ids].flatten()
    
    @property
    def colors_rgb(self):
        if self.use_custom_colors:
            return self.custom_colors.colors_rgb
        return self._colors_rgb[self.ids].reshape(-1, 4)
    
    def reset_updated_flags(self):
        self.has_updated_pos = False
        self.has_updated_pos_continuos = False
        self.has_updated_ids = False
        self.has_updated_cms = False
        self.has_updated_colors = False

        if self.use_custom_colors:
            self.custom_colors.update()

