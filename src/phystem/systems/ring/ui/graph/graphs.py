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
from phystem.systems.ring import utils, rings_quantities

from .graphs_cfg import SimpleGraphCfg, ReplayGraphCfg, ForceName, ObstacleCfg
from .graphs_cfg import RandomColorsCfg, VelocityColorsCfg, AsphericityColorsCfg
from .graph_components import *
from .active_rings import ActiveRings, CustomColors

class BaseGraph(ABC):
    @abstractmethod
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs: dict, graph_cfg=None, obstacle_cfg=None):
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
            if obstacle_cfg is None:
                obstacle_cfg = ObstacleCfg()
            self.stokes_obstacle(fill=obstacle_cfg.fill, color=obstacle_cfg.color, zorder=3)

        num_particles = self.sim_configs["dynamic_cfg"].num_particles
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

    def stokes_obstacle(self, fill, color, zorder=3):
        stokes_cfg: StokesCfg = self.sim_configs["other_cfgs"]["stokes"] 
        self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=fill, color=color, zorder=zorder))

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
        dynamic_cfg: RingCfg = self.sim_configs['dynamic_cfg']

        ring_area = self.solver.area_debug.area[ring_id]
        ring_rel_area = ring_area / dynamic_cfg.area0
        pos = self.solver.pos[ring_id][p_id]
        area_force = self.solver.area_forces[ring_id][p_id]
        spring_force = self.solver.spring_forces[ring_id][p_id]
        vol_force = self.solver.vol_forces[ring_id][p_id]
        self_prop_vel = self.solver.self_prop_vel[ring_id]
        
        ring_area += dynamic_cfg.get_particles_area()

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
        super().__init__(fig, ax, solver, sim_configs, graph_cfg, graph_cfg.obstacle_cfg)
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
            "pol_vel": RingVelPos(ax, self.active_rings,
                solver=self.solver,
                show_cfg_name = "show_pol_vel",
                **graph_cfg.pol_vel_kwargs),
            "f_springs": RingForce(ax, self.active_rings,
                solver_forces = self.solver.spring_forces,
                color = self.graph_cfg.force_color[ForceName.spring],
                show_cfg_name = "show_f_springs",
                artist_kwargs = self.graph_cfg.force_kwargs[ForceName.spring],
                ),
            "f_vol": RingForce(ax, self.active_rings,
                solver_forces = self.solver.vol_forces,
                color = self.graph_cfg.force_color[ForceName.vol],
                show_cfg_name = "show_f_vol",
                artist_kwargs = self.graph_cfg.force_kwargs[ForceName.vol],
                ),
            "f_area": RingForce(ax, self.active_rings,
                solver_forces = self.solver.area_forces,
                color = self.graph_cfg.force_color[ForceName.area],
                show_cfg_name = "show_f_area",
                artist_kwargs = self.graph_cfg.force_kwargs[ForceName.area],
                ),
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
            "cell_area": CellArea(ax, self.active_rings, 
                configs=self.graph_cfg.cell_area_cfg, 
                sim_configs=sim_configs), 
        }

        if sim_configs["other_cfgs"].get("stokes"):
            self.components["regions"] = Regions(
                ax, sim_configs["space_cfg"], sim_configs["other_cfgs"]["stokes"],
                self.graph_cfg.regions_cfg,
            )

        self.update()


class RandomColor(CustomColors):
    def __init__(self, cfg: RandomColorsCfg,  solver: SolverReplay) -> None:
        super().__init__(cfg, solver, to_update=False)
        self.uids_to_color = {}
        print(self.cfg.cmap)
        self.possible_values = np.arange(len(self.cfg.cmap.colors)) / (len(self.cfg.cmap.colors) - 1)
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
        self.colors_rgb = self.cfg.cmap(self.colors_values)

class VelocityColor(CustomColors):
    def update(self):
        _, vel_cm_dir = self.solver.get_vel_cm()
        self.colors_value = (np.zeros((self.solver.num_particles, vel_cm_dir.size), dtype=np.float32) + vel_cm_dir).T.flatten() 
        self.colors_rgb = self.cfg.cmap.to_rgba(self.colors_value)
        # return (np.zeros((self.solver.num_particles, vel_cm_dir.size), dtype=np.float32) + vel_cm_dir).T.flatten()

class AsphericityColor(CustomColors):
    def update(self):
        _, _, asphericity = self.gyration_tensor()
        self.colors_value = np.repeat(asphericity, self.solver.num_particles)
        self.colors_rgb = self.cfg.cmap.to_rgba(self.colors_value)

    def gyration_tensor(self):
        solver = self.solver

        # Cpp Solver
        # ids = solver.rings_ids[:solver.num_active_rings]
        # centers_of_mass = solver.center_mass[ids]
        # positions = np.array(solver.pos)[ids, :, :]
        
        # Replay Solver
        centers_of_mass = solver.center_mass
        positions = solver.pos

        # Relative positions:
        # shape: (N, n, 2)
        relative_positions = positions - centers_of_mass[:, None, :]

        # R_ab = (1/n) sum_i r_{i,a} r_{i,b}
        # shape: (N, 2, 2)
        gyration_tensor = np.einsum(
            "npi,npj->nij",
            relative_positions,
            relative_positions,
        ) / positions.shape[1]

        # R_g² = Tr(R)
        radius_squared = np.trace(gyration_tensor, axis1=1, axis2=2)
        gyration_radius = np.sqrt(np.maximum(radius_squared, 0.0))

        # For a 2x2 tensor:
        #
        # A = (lambda_1 - lambda_2)² / (lambda_1 + lambda_2)²
        #   = 1 - 4 det(R) / Tr(R)²
        determinant = np.linalg.det(gyration_tensor)

        asphericity = np.zeros_like(radius_squared)

        nonzero = radius_squared > np.finfo(float).eps
        asphericity[nonzero] = 1.0 - 4.0 * determinant[nonzero] / radius_squared[nonzero]**2

        # Remove small floating-point violations of the theoretical range.
        asphericity = np.clip(asphericity, 0.0, 1.0)

        return gyration_tensor, gyration_radius, asphericity

def get_ring_colors(cfg, solver):
    ring_cfg_to_cls = {
        RandomColorsCfg: RandomColor,
        VelocityColorsCfg: VelocityColor,
        AsphericityColorsCfg: AsphericityColor,
    }
    if type(cfg) is str:
        for Cfg_i in ring_cfg_to_cls.keys():
            if cfg == Cfg_i.name:
                cfg = Cfg_i()
                break
        else:
            valid_name = [c.name for c in ring_cfg_to_cls.keys()]
            raise Exception(f"RingColorCfg name `{cfg}` in not valid. Valid names: {valid_name}")
    
    return ring_cfg_to_cls[type(cfg)](cfg, solver)

class ReplayGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: SolverReplay, sim_configs: dict, graph_cfg: ReplayGraphCfg=None):
        if type(solver) != SolverReplay:
            raise Exception("Tipo de solver incompatível. 'ReplayGraph' apenas aceita 'SolverReplay'.")

        super().__init__(fig, ax, solver, sim_configs, graph_cfg, graph_cfg.obstacle_cfg)

        if self.graph_cfg is None:
            self.graph_cfg = ReplayGraphCfg()
        
        if self.graph_cfg.x_lims is not None:
            self.ax.set_xlim(*self.graph_cfg.x_lims)

        self.ax.set(**self.graph_cfg.ax_kwargs)

        # self.active_rings.add_custom_colors(
        #     "vel",
        #     VelocityColor(solver, graph_cfg.colorbar_kwargs)
        # )
        # self.active_rings.add_custom_colors(
        #     "random",
        #     RandomColor(solver),
        # )
        
        # if self.graph_cfg.vel_colors:
        #     self.active_rings.set_custom_colors("vel")
        #     self.active_rings.custom_colors.add_colorbar(ax)
        # else:
        #     self.active_rings.set_custom_colors("random")
        
        ring_colors = get_ring_colors(graph_cfg.ring_colors_cfg, self.solver)
        self.active_rings.add_custom_colors(
            ring_colors.cfg.name,
            ring_colors
        )
        self.active_rings.set_custom_colors(ring_colors.cfg.name)
        if ring_colors.cfg.name == "vel":
            self.active_rings.custom_colors.add_colorbar(ax)

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
