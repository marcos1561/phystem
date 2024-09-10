from abc import ABC, abstractmethod
import numpy as np

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.patches import Circle
from matplotlib import cm
from matplotlib.colors import Normalize

from phystem.systems.ring.solvers import CppSolver, SolverReplay
from phystem.systems.ring.configs import SpaceCfg, StokesCfg
from phystem.systems.ring import utils

from .graphs_cfg import SimpleGraphCfg, ReplayGraphCfg, ForceName

from matplotlib.figure import Figure
from .graph_components import *
from .active_rings import ActiveRings, CustomColors

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

        self.borders()
        if sim_configs["other_cfgs"].get("stokes") is not None:
            self.stokes_obstacle(zorder=3)

        num_particles = self.sim_configs["creator_cfg"].num_particles
        self.active_rings = ActiveRings(num_particles, solver)

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

    def update(self):
        self.active_rings.reset_updated_flags()
        
        for comp in self.components.values():
            to_show = getattr(self.graph_cfg, comp.show_cfg_name)
            comp.update(to_show)

class MainGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs, graph_cfg: SimpleGraphCfg=None):
        super().__init__(fig, ax, solver, sim_configs, graph_cfg)
        if self.graph_cfg is None:
            self.graph_cfg = SimpleGraphCfg()

        def onclick(event):
            ids = solver.cpp_solver.get_particle_id(event.xdata, event.ydata)
            ring_id, p_id = ids
            
            pos = solver.pos[ring_id][p_id]
            area_force = solver.area_forces[ring_id][p_id]
            spring_force = solver.spring_forces[ring_id][p_id]
            vol_force = solver.vol_forces[ring_id][p_id]
            self_prop_vel = solver.self_prop_vel[ring_id][p_id]
            area = solver.area_debug.area[ring_id]
            
            print("pos", pos)
            print("area_force", area_force)
            print("spring_force", spring_force)
            print("vol_force", vol_force)
            print("self_prop_vel", self_prop_vel)
            print("area", area)
            print("f_0", area/sim_configs["dynamic_cfg"].area0)
            print("f_eq", area/sim_configs["dynamic_cfg"].get_equilibrium_area(sim_configs["creator_cfg"].num_particles))
            print("invs", self.solver.in_pol_checker.collisions)
            print("self_prop_vel: ", self.solver.self_prop_vel[2])
            print(ids)

            print("==========")

        # row_id = 5
        # col_id = 5

        # windows_manager = self.solver.windows_manager

        # w = windows_manager.window_length
        # h = windows_manager.window_height

        # sh = sim_configs["space_cfg"].height
        # sw = sim_configs["space_cfg"].length

        # x1 = -sw/2 + w * (col_id)
        # x2 = x1 + w
        
        # y1 = -sh/2 + h * row_id
        # y2 = y1 + h

        # self.ax.plot(
        #     [x1, x2, x2, x1, x1],
        #     [y1, y1, y2, y2, y1],
        # )

        # def onclick(event):
        #     clicked_id = solver.cpp_solver.get_particle_id(event.xdata, event.ydata)
        #     ids = solver.windows_manager.get_window_elements(0, 10)
        #     print(ids)
        #     print("Clicada", clicked_id)

        fig.canvas.mpl_connect('button_press_event', onclick)

        self.ax.set(**graph_cfg.ax_kwargs)

        self.components: dict[str, GraphComponent] = {
            "scatter": ParticlesScatter(ax, self.active_rings, 
                zorder = 2, 
                scatter_kwargs = self.graph_cfg.scatter_kwargs),
            "circles": ParticleCircles(ax, self.active_rings, 
                radius = sim_configs["dynamic_cfg"].diameter/2,
                cfg = self.graph_cfg.circle_cfg),
            "density": Density(ax, self.active_rings,
                cell_shape = self.graph_cfg.cell_shape, 
                sim_configs = sim_configs,
                artist_kwargs = self.graph_cfg.density_kwargs,),
            "springs": RingSprings(ax, self.active_rings,
                solver = self.solver,
                dynamic_cfg = sim_configs["dynamic_cfg"]),
            "f_springs": RingForce(ax, self.active_rings,
                solver_forces = self.solver.spring_forces,
                color = self.graph_cfg.force_color[ForceName.spring],
                show_cfg_name = "show_f_springs"),
            "f_vol": RingForce(ax, self.active_rings,
                solver_forces = self.solver.vol_forces,
                color = self.graph_cfg.force_color[ForceName.vol],
                show_cfg_name = "show_f_vol"),
            "f_area": RingForce(ax, self.active_rings,
                solver_forces = self.solver.area_forces,
                color = self.graph_cfg.force_color[ForceName.area],
                show_cfg_name = "show_f_area"),
            "f_format": RingForce(ax, self.active_rings,
                solver_forces = self.solver.format_forces,
                color = self.graph_cfg.force_color[ForceName.format],
                show_cfg_name ="show_f_format"),
            "f_obs": RingForce(ax, self.active_rings,
                solver_forces = self.solver.obs_forces,
                color = self.graph_cfg.force_color[ForceName.obs],
                show_cfg_name = "show_f_obs"),
            "f_invasion": RingForce(ax, self.active_rings,
                solver_forces = self.solver.invasion_forces,
                color = self.graph_cfg.force_color[ForceName.invasion],
                show_cfg_name = "show_f_invasion"),
            "f_total": RingForce(ax, self.active_rings,
                solver_forces = self.solver.total_forces,
                color = self.graph_cfg.force_color[ForceName.total],
                show_cfg_name = "show_f_total"),
            "center_mass": CenterMass(ax, self.active_rings), 
            "invasion_points": InvasionPoints(ax, self.solver), 
            "ith_points": IthPoints(ax, self.active_rings,
                zorder = 3),
        }

        self.update()

class VelocityColor(CustomColors):
    def __init__(self, solver: SolverReplay, colorbar_kwargs=None):
        cmap = cm.ScalarMappable(
            norm=Normalize(-np.pi, np.pi),
            cmap=utils.roll_segmented_cmap(cm.hsv, amount=0.5),
        )
        super().__init__(cmap, colorbar_kwargs)
        
        self.solver = solver

        self.update()

    def update(self):
        _, vel_cm_dir = self.solver.get_vel_cm()
        self.colors_value = (np.zeros((self.solver.num_particles, vel_cm_dir.size), dtype=np.float32) + vel_cm_dir).T.flatten() 
        self.colors_rgb = self.cmap.to_rgba(self.colors_value)
        # return (np.zeros((self.solver.num_particles, vel_cm_dir.size), dtype=np.float32) + vel_cm_dir).T.flatten()

class ReplayGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: SolverReplay, sim_configs: dict, graph_cfg: ReplayGraphCfg=None):
        if type(solver) != SolverReplay:
            raise Exception("Tipo de solver incompatível. 'ReplayGraph' apenas aceita 'SolverReplay'.")

        super().__init__(fig, ax, solver, sim_configs, graph_cfg)

        if self.graph_cfg is None:
            self.graph_cfg = ReplayGraphCfg()
        
        if self.graph_cfg.x_lims is not None:
            self.ax.set_xlim(*self.graph_cfg.x_lims)

        self.ax.set(**self.graph_cfg.ax_kwargs)

        self.active_rings.custom_colors = VelocityColor(solver, graph_cfg.colorbar_kwargs)
        if self.graph_cfg.vel_colors:
            self.active_rings.use_custom_colors = True
            self.active_rings.custom_colors.add_colorbar(ax)

        print(self.active_rings.use_custom_colors)

        self.components: dict[str, GraphComponent] = {
            "scatter": ParticlesScatter(ax, self.active_rings, 
                zorder = 2, 
                scatter_kwargs = self.graph_cfg.scatter_kwargs),
            "circles": ParticleCircles(ax, self.active_rings, 
                radius = sim_configs["dynamic_cfg"].diameter/2,
                cfg = self.graph_cfg.circle_cfg),
            "density": Density(ax, self.active_rings,
                cell_shape = self.graph_cfg.cell_shape, 
                sim_configs = sim_configs,
                artist_kwargs = self.graph_cfg.density_kwargs,
                colorbar_kwargs=self.graph_cfg.colorbar_kwargs,),
            "center_mass": CenterMass(ax, self.active_rings), 
        }

        self.update()
        # fig.colorbar(self.components.get("density").artist)
        # space_cfg: SpaceCfg = sim_configs["space_cfg"]

        # h = space_cfg.height/2
        # l = space_cfg.length/2
        # r_scale = 1
        # self.ax.set_ylim(-r_scale*h, r_scale*h)
        
        # if self.graph_cfg.x_lims is None:
        #     self.ax.set_xlim(-r_scale*l, r_scale*l)
        # else:
        #     self.ax.set_xlim(*self.graph_cfg.x_lims)

        # self.ax.set_aspect(1)

        # Borders
        # self.ax.plot([-l, -l], [ h, -h], color="black")
        # self.ax.plot([ l,  l], [ h, -h], color="black")
        # self.ax.plot([ l, -l], [ h,  h], color="black")
        # self.ax.plot([ l, -l], [-h, -h], color="black")

    #     if sim_configs["other_cfgs"] is not None:
    #         stokes_cfg = sim_configs["other_cfgs"]["stokes"]
    #         self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=False, zorder=3))

    #     if self.graph_cfg.show_rings:
    #         if self.graph_cfg.vel_colors:
    #             self.points = self.ax.scatter(*self.get_pos().T, zorder=2, **self.graph_cfg.scatter_kwargs, cmap=cm.hsv, 
    #                 c=self.get_colors(), vmin=-np.pi, vmax=np.pi)
                
    #             fig.colorbar(self.points, label="(rad)", **self.graph_cfg.colorbar_kwargs)
    #         else:
    #             self.points = self.ax.scatter(*self.get_pos().T, zorder=2, **self.graph_cfg.scatter_kwargs)

    #     if self.graph_cfg.show_density:
    #         self.density = ax.pcolormesh(*self.solver.grid.edges, self.solver.ring_count, shading='flat',
    #             zorder=1, **self.graph_cfg.density_kwargs)
    #         fig.colorbar(self.density)
    #     if self.graph_cfg.show_cm:
    #         cm_s = graph_cfg.scatter_kwargs.get("s", None)
    #         if cm_s is not None:
    #             cm_s *= 3
    #         self.cm = self.ax.scatter(*self.solver.cm.T, zorder=3, c="black", s=cm_s)
    
    # def get_pos(self):
    #     pos = self.solver.pos
    #     return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])

    # def get_colors(self):
    #     vel_cm = self.solver.vel_cm_dir
    #     return (np.zeros((self.solver.num_particles, vel_cm.size), dtype=np.float32) + vel_cm).T.flatten()

    # def update(self):
    #     if self.graph_cfg.show_rings:
    #         self.points.set_offsets(self.get_pos())
    #         if self.graph_cfg.vel_colors:
    #             self.points.set_array(self.get_colors())
        
    #     if self.graph_cfg.show_cm:
    #         self.cm.set_offsets(self.solver.cm)

    #     if self.graph_cfg.show_density:
    #         self.density.set_array(self.solver.ring_count)
