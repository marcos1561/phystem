from abc import ABC, abstractmethod
import numpy as np

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import Circle
from matplotlib import cm

from phystem.systems.ring.solvers import CppSolver, SolverReplay
from phystem.systems.ring.configs import SpaceCfg, StokesCfg

from .graphs_cfg import SimpleGraphCfg, ReplayGraphCfg

from matplotlib.figure import Figure
from .graph_components import *


class BaseGraph(ABC):
    @abstractmethod
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs: dict, graph_cfg=None):
        self.fig = fig
        self.ax = ax
        self.solver = solver
        self.sim_configs = sim_configs
        self.graph_cfg = graph_cfg
        self.space_cfg: SpaceCfg = sim_configs["space_cfg"]

        self.ax.set_aspect(1)

    def borders(self, r_scale=1):
        h = self.space_cfg.height/2
        l = self.space_cfg.length/2
        self.ax.set_ylim(-r_scale*h, r_scale*h)
        self.ax.set_xlim(-r_scale*l, r_scale*l)

        self.ax.plot([-l, -l], [ h, -h], color="black")
        self.ax.plot([ l,  l], [ h, -h], color="black")
        self.ax.plot([ l, -l], [ h,  h], color="black")
        self.ax.plot([ l, -l], [-h, -h], color="black")

    def stokes_obstacle(self, zorder=3):
        stokes_cfg: StokesCfg = self.sim_configs["other_cfgs"]["stokes"] 
        self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=False,  zorder=zorder))

    @abstractmethod
    def update(self):
        pass

class SimpleGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs, graph_cfg: SimpleGraphCfg=None):
        super().__init__(fig, ax, solver, sim_configs, graph_cfg)
        if self.graph_cfg is None:
            self.graph_cfg = SimpleGraphCfg()

        num_particles = self.sim_configs["creator_cfg"].num_p
        self.active_rings = ActiveRings(num_particles, solver)

        self.ax.set(**self.graph_cfg.ax_kwargs)
        self.borders()
        if sim_configs["other_cfgs"]["stokes"]:
            self.stokes_obstacle(zorder=3)
        
        self.components: dict[str, GraphComponent] = {
            "scatter": ParticlesScatter(ax, self.active_rings, 
                zorder = 2, 
                scatter_kwargs = self.graph_cfg.rings_kwargs),
            "circles": ParticleCircles(ax, self.active_rings, 
                radius = sim_configs["dynamic_cfg"].diameter/2,
                cfg = self.graph_cfg.circles_cfg),
            "density": Density(ax, self.active_rings,
                cell_shape = self.graph_cfg.cell_shape, 
                sim_configs = sim_configs,
                artist_kwargs = self.graph_cfg.density_kwargs,),
            "springs": RingSprings(ax, self.active_rings,
                solver = self.solver,
                dynamic_cfg = sim_configs["dynamic_cfg"]),
            "f_springs": RingForce(ax, self.active_rings,
                solver_forces = self.solver.spring_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.spring],
                show_cfg_name = "show_f_springs"),
            "f_vol": RingForce(ax, self.active_rings,
                solver_forces = self.solver.vol_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.vol],
                show_cfg_name = "show_f_vol"),
            "f_area": RingForce(ax, self.active_rings,
                solver_forces = self.solver.area_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.area],
                show_cfg_name = "show_f_area"),
            "f_format": RingForce(ax, self.active_rings,
                solver_forces = self.solver.format_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.format],
                show_cfg_name ="show_f_format"),
            "f_obs": RingForce(ax, self.active_rings,
                solver_forces = self.solver.obs_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.obs],
                show_cfg_name = "show_f_obs"),
            "f_invasion": RingForce(ax, self.active_rings,
                solver_forces = self.solver.invasion_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.invasion],
                show_cfg_name = "show_f_invasion"),
            "f_total": RingForce(ax, self.active_rings,
                solver_forces = self.solver.total_forces,
                color = self.graph_cfg.force_color[SimpleGraphCfg.ForceName.total],
                show_cfg_name = "show_f_total"),
            "center_mass": CenterMass(ax, self.active_rings), 
            "invasion_points": InvasionPoints(ax, self.solver), 
            "ith_points": IthPoints(ax, self.active_rings,
                zorder = 3),
        }

        self.update()

    def update(self):
        self.active_rings.reset_updated_flags()
        
        for comp in self.components.values():
            to_show = getattr(self.graph_cfg, comp.show_cfg_name)
            comp.update(to_show)

class ReplayGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: SolverReplay, sim_configs: dict, graph_cfg: ReplayGraphCfg=None):
        if type(solver) != SolverReplay:
            raise Exception("Tipo de solver incompatível. 'ReplayGraph' apenas aceita 'SolverReplay'.")

        self.ax = ax
        self.solver = solver
        
        self.graph_cfg = graph_cfg
        if graph_cfg is None:
            self.graph_cfg = ReplayGraphCfg()

        space_cfg: SpaceCfg = sim_configs["space_cfg"]

        h = space_cfg.height/2
        l = space_cfg.length/2
        r_scale = 1
        self.ax.set_ylim(-r_scale*h, r_scale*h)
        
        if self.graph_cfg.x_lims is None:
            self.ax.set_xlim(-r_scale*l, r_scale*l)
        else:
            self.ax.set_xlim(*self.graph_cfg.x_lims)

        self.ax.set_aspect(1)

        # Borders
        self.ax.plot([-l, -l], [ h, -h], color="black")
        self.ax.plot([ l,  l], [ h, -h], color="black")
        self.ax.plot([ l, -l], [ h,  h], color="black")
        self.ax.plot([ l, -l], [-h, -h], color="black")

        if sim_configs["other_cfgs"] is not None:
            stokes_cfg = sim_configs["other_cfgs"]["stokes"]
            self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=False, zorder=3))

        if self.graph_cfg.show_rings:
            if self.graph_cfg.vel_colors:
                self.points = self.ax.scatter(*self.get_pos().T, zorder=2, **self.graph_cfg.scatter_kwargs, cmap=cm.hsv, 
                    c=self.get_colors(), vmin=-np.pi, vmax=np.pi)
                
                fig.colorbar(self.points, label="(rad)", **self.graph_cfg.colorbar_kwargs)
            else:
                self.points = self.ax.scatter(*self.get_pos().T, zorder=2, **self.graph_cfg.scatter_kwargs)

        if self.graph_cfg.show_density:
            self.density = ax.pcolormesh(*self.solver.grid.edges, self.solver.ring_count, shading='flat',
                zorder=1, **self.graph_cfg.density_kwargs)
            fig.colorbar(self.density)
        if self.graph_cfg.show_cm:
            cm_s = graph_cfg.scatter_kwargs.get("s", None)
            if cm_s is not None:
                cm_s *= 3
            self.cm = self.ax.scatter(*self.solver.cm.T, zorder=3, c="black", s=cm_s)
    
    def get_pos(self):
        pos = self.solver.pos
        return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])

    def get_colors(self):
        vel_cm = self.solver.vel_cm_dir
        return (np.zeros((self.solver.num_particles, vel_cm.size), dtype=np.float32) + vel_cm).T.flatten()

    def update(self):
        if self.graph_cfg.show_rings:
            self.points.set_offsets(self.get_pos())
            if self.graph_cfg.vel_colors:
                self.points.set_array(self.get_colors())
        
        if self.graph_cfg.show_cm:
            self.cm.set_offsets(self.solver.cm)

        if self.graph_cfg.show_density:
            self.density.set_array(self.solver.ring_count)
