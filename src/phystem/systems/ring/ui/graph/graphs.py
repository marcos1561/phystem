from abc import ABC, abstractmethod
import numpy as np
import random

import tkinter as tk
from tkinter import ttk

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

        # space_cfg = sim_configs["space_cfg"]
        # h, l = space_cfg.height, space_cfg.length
        # ax.add_patch(Rectangle((-l/2, -h/2), l, h, color="white", zorder=-10))

        self.borders()
        if sim_configs["other_cfgs"].get("stokes") is not None:
            self.stokes_obstacle(zorder=3)

        num_particles = self.sim_configs["creator_cfg"].num_particles
        self.active_rings = ActiveRings(num_particles, solver)

        self._root = None

    @property
    def root(self):
        if self._root is None:
            raise Exception("root ainda não foi setado!")
        return self._root

    @root.setter
    def root(self, value):
        self._root = value
        
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

class ParticleInfoWindow(tk.Toplevel):
    '''
    Janela que contém informações sobre a partícula clicada
    e o anel a qual ela pertence.
    '''
    def __init__(self, parent, solver: CppSolver, sim_configs):
        super().__init__(parent)
        self.title("Particle info")
        self.solver = solver
        self.sim_configs = sim_configs                

        self.label_text: list[tk.StringVar] = [tk.StringVar() for _ in range(8)]

        main_frame = ttk.Frame(self)

        self.info_text = tk.Text(main_frame, state="disabled")

        main_frame.grid(padx=10, pady=10)
        self.info_text.grid()

        self.is_active = True
        self.bind("<Destroy>", self.on_destroy)

    def update(self, ring_id, p_id):
        ring_area = self.solver.area_debug.area[ring_id]
        ring_rel_area = ring_area / self.sim_configs['dynamic_cfg'].area0
        pos = self.solver.pos[ring_id][p_id]
        area_force = self.solver.area_forces[ring_id][p_id]
        spring_force = self.solver.spring_forces[ring_id][p_id]
        vol_force = self.solver.vol_forces[ring_id][p_id]
        self_prop_vel = self.solver.self_prop_vel[ring_id]
        
        def format_vec(vec, decimal_places=3):
            return f"{round(vec[0], decimal_places)}, {round(vec[1], decimal_places)}"

        info_text = (
            f"Ring id: {ring_id} | Particle id: {p_id}\n"
            f"Area: {round(ring_area, 3)}\n"
            f"Relative area: {round(ring_rel_area, 3)}\n"
            f"Pos: {format_vec(pos)}\n"
            f"Area force: {format_vec(area_force)}\n"
            f"Spring Force: {format_vec(spring_force)}\n"
            f"Vol Force: {format_vec(vol_force)}\n"
            f"Polarization: {format_vec(self_prop_vel)}\n"
        )

        self.info_text["state"] = "normal"
        self.info_text.delete(1.0, "end")
        self.info_text.insert(1.0, info_text)
        self.info_text["state"] = "disabled"

    def on_destroy(self, event):
        if event.widget != self:
            return
        self.is_active = False

class MainGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs, graph_cfg: SimpleGraphCfg=None):
        super().__init__(fig, ax, solver, sim_configs, graph_cfg)
        if self.graph_cfg is None:
            self.graph_cfg = SimpleGraphCfg()

        self.particle_window: ParticleInfoWindow = None

        def onclick(event):
            print("show:", self.graph_cfg.show_particle_info)
            if not self.graph_cfg.show_particle_info or event.xdata is None or event.ydata is None:
                return

            if self.particle_window is None or not self.particle_window.is_active:
                self.particle_window = ParticleInfoWindow(self.root, self.solver, self.sim_configs)

            ids = solver.cpp_solver.get_particle_id(event.xdata, event.ydata)
            ring_id, p_id = ids
            self.particle_window.update(ring_id, p_id)

        fig.canvas.mpl_connect('button_press_event', onclick)

        self.ax.set(**graph_cfg.ax_kwargs)

        self.components: dict[str, GraphComponent] = {
            "scatter": ParticlesScatter(ax, self.active_rings, 
                zorder=2, 
                scatter_kwargs = self.graph_cfg.scatter_kwargs),
            "circles": ParticleCircles(ax, self.active_rings, 
                radius=sim_configs["dynamic_cfg"].diameter/2,
                # radius2=sim_configs["dynamic_cfg"].max_dist/2,
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
            "f_creation": RingForce(ax, self.active_rings,
                solver_forces = self.solver.creation_forces,
                color = self.graph_cfg.force_color[ForceName.creation],
                show_cfg_name = "show_f_creation"),
            "f_total": RingForce(ax, self.active_rings,
                solver_forces = self.solver.total_forces,
                color = self.graph_cfg.force_color[ForceName.total],
                show_cfg_name = "show_f_total"),
            "center_mass": CenterMass(ax, self.active_rings), 
            "invasion_points": InvasionPoints(ax, self.solver), 
            "ith_points": IthPoints(ax, self.active_rings,
                zorder = 3),
        }

        if sim_configs["other_cfgs"].get("stokes"):
            self.components["regions"] = Regions(
                ax, sim_configs["space_cfg"], sim_configs["other_cfgs"]["stokes"],
                self.graph_cfg.regions_cfg,
            )

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

class RandomColor(CustomColors):
    def __init__(self, solver: SolverReplay, colorbar_kwargs=None) -> None:
        super().__init__(cm.tab20, colorbar_kwargs)
        self.solver = solver
        self.uids_to_color = {}
        self.possible_values = np.arange(len(self.cmap.colors)) / (len(self.cmap.colors) - 1)
        self.update()

    def update(self):
        colors_values = np.empty((self.solver.pos.shape[0], self.solver.num_particles), dtype=float)

        for idx, uid in enumerate(self.solver.common_ids):
            color = self.uids_to_color.get(uid)
            if color is None:
                color = random.choice(self.possible_values)
                self.uids_to_color[uid] = color

            colors_values[idx] = color

        self.colors_values = colors_values.flatten() 
        self.colors_rgb = self.cmap(self.colors_values)

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

        self.active_rings.add_custom_colors(
            "vel",
            VelocityColor(solver, graph_cfg.colorbar_kwargs)
        )
        self.active_rings.add_custom_colors(
            "random",
            RandomColor(solver),
        )
        
        if self.graph_cfg.vel_colors:
            self.active_rings.set_custom_colors("vel")
            self.active_rings.custom_colors.add_colorbar(ax)
        else:
            self.active_rings.set_custom_colors("random")

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
