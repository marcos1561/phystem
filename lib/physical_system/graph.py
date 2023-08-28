import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle
from matplotlib.text import Text

import numpy as np

from physical_system.solver import VicsekSolver, CppSolver
from physical_system.particles import Particles
from physical_system.configs import *
from ic_utils.timer import TimeIt

class ParticlesGraph:
    def __init__(self, ax: Axes, particles: Particles, space_cfg: SpaceCfg, dynamic_cfg: SelfPropellingCfg, graph_cfg: GraphCfg) -> None:
        self.ax = ax
        self.particles = particles
        self.space_cfg = space_cfg
        self.dynamic_cfg = dynamic_cfg
        self.graph_cfg = graph_cfg

        self.graph: PatchCollection = None
    
        self.circles: list[Circle]
        self.circles_col: PatchCollection

    def init(self):
        r = self.space_cfg.size/2
        r_scale = 1
        self.ax.set_ylim(-r_scale*r, r_scale*r)
        self.ax.set_xlim(-r_scale*r, r_scale*r)

        self.ax.set_aspect(1)

        self.ax.plot([-r, r], [-r, -r], color="black")
        self.ax.plot([-r, r], [r, r], color="black")
        self.ax.plot([r, r], [-r, r], color="black")
        self.ax.plot([-r, -r], [-r, r], color="black")

        x, y = self.particles.plot()
        self.graph = self.ax.scatter(x, y, color="Black")

        self.circles = []
        for x_i, y_i in zip(x, y):
            self.circles.append(Circle((x_i, y_i), self.dynamic_cfg.r_eq, fill=False))
        
        self.circles_col = PatchCollection(self.circles, match_original=True)
        if not self.graph_cfg.show_circles:
            self.circles_col.set_paths([])

        self.ax.add_collection(self.circles_col)

    def update(self):
        pos = np.array(self.particles.plot())

        if self.graph_cfg.show_circles:
            for id in range(pos.shape[1]):
                self.circles[id].center = (pos[0][id], pos[1][id])
            self.circles_col.set_paths(self.circles)
        else:
            self.circles_col.set_paths([])

        self.graph.set_offsets(pos.transpose())

        return self.graph, self.circles_col

class MeanVelGraph:
    def __init__(self, ax: Axes, solver: CppSolver) -> None:
        self.solver = solver
        self.ax = ax

        self.vel_vec = ax.quiver(0, 0, 1, 1, angles='xy', scale_units='xy', scale=1)

        ax.set_aspect(1)
        self.ax.set_xlim(-1.1, 1.1)
        self.ax.set_ylim(-1.1, 1.1)

    def update(self):
        self.vel_vec.set_UVC(*self.solver.mean_vel_vec())

class Info:
    def __init__(self, ax: Axes, solver: VicsekSolver, time_it: TimeIt, 
        self_propelling_cfg: SelfPropellingCfg, create_cfg: CreateCfg, space_cfg: SpaceCfg) -> None:
        self.ax = ax
        self.solver = solver
        self.time_it = time_it

        self.text: Text = None
        
        self.cfg_info = self_propelling_cfg.info() + "\n" f"N = {create_cfg.n}\nL = {space_cfg.size}\n" 


    def get_info(self):
        sim_info = (
            f"$\Delta$T (ms): {self.time_it.mean_time():.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.3f}\n"
            f"<V> = {self.solver.mean_vel():.3f}\n"
        )

        return sim_info + "\n" + self.cfg_info
    
    def init(self):
        # self.ax.axis('off')
        # self.text = self.ax.text(0, 0, s, verticalalignment="top")
        
        s = self.get_info()
        self.text = self.ax.text(0.01, 1-0.01, s,
            horizontalalignment='left',
            verticalalignment='top',
            transform=self.ax.transAxes)


    def update(self):
        s = self.get_info()
        self.text.set_text(s)


