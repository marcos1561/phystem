from matplotlib.collections import PatchCollection
from matplotlib.axes import Axes
from matplotlib.text import Text
import numpy as np

from physical_system.solver import VicsekSolver, CppSolver
from physical_system.particles import Particles
from physical_system.configs import *
from ic_utils.timer import TimeIt

class ParticlesGraph:
    def __init__(self, ax: Axes, particles: Particles, space_cfg: SpaceCfg) -> None:
        self.ax = ax
        self.particles = particles
        self.space_cfg = space_cfg

        self.graph: PatchCollection = None
    

    def init(self):
        r = self.space_cfg.size/2
        r_scale = 1.3
        self.ax.set_ylim(-r_scale*r, r_scale*r)
        self.ax.set_xlim(-r_scale*r, r_scale*r)

        self.ax.set_aspect(1)

        self.ax.plot([-r, r], [-r, -r], color="black")
        self.ax.plot([-r, r], [r, r], color="black")
        self.ax.plot([r, r], [-r, r], color="black")
        self.ax.plot([-r, -r], [-r, r], color="black")

        x, y = self.particles.plot()
        self.graph = self.ax.scatter(x, y, color="Black")
        
    def update(self):
        x, y = self.particles.plot()
        self.graph.set_offsets(np.array([x, y]).transpose())

class MeanVelGraph:
    def __init__(self, ax: Axes, solver: CppSolver) -> None:
        self.solver = solver
        self.ax = ax

        self.vel_vec = ax.quiver(0, 0, 1, 1, angles='xy', scale_units='xy', scale=1)

        ax.set_aspect(1)

    def update(self):
        mean_speed = self.solver.mean_vel()
        graph_lim = abs(self.ax.get_xlim()[0])

        # if mean_speed > graph_lim * 0.9:
        #     # self.ax.set_xlim(-mean_speed / 0.6, mean_speed / 0.6)
        #     # self.ax.set_ylim(-mean_speed / 0.6, mean_speed / 0.6)
        #     self.ax.set_xlim(-1.1*graph_lim, 1.1*graph_lim)
        #     self.ax.set_ylim(-1.1*graph_lim, 1.1*graph_lim)
        # elif mean_speed < graph_lim * 0.3:
        #     # self.ax.set_xlim(-mean_speed / 0.5, mean_speed / 0.5)
        #     # self.ax.set_ylim(-mean_speed / 0.5, mean_speed / 0.5)
        #     self.ax.set_xlim(-0.7*graph_lim, 0.7*graph_lim)
        #     self.ax.set_ylim(-0.7*graph_lim, 0.7*graph_lim)

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
        self.ax.axis('off')
        s = self.get_info()
        self.text = self.ax.text(0, 0, s, verticalalignment="top")

    def update(self):
        s = self.get_info()
        self.text.set_text(s)
