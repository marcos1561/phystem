from abc import ABC, abstractmethod
from copy import deepcopy
import numpy as np

from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection, PatchCollection
from matplotlib.patches import Circle
from matplotlib.quiver import Quiver 
from matplotlib import colors, cm

from .graphs_cfg import MainGraphCfg, SimpleGraphCfg, ReplayGraphCfg
from phystem.systems.ring.solvers import CppSolver, SolverReplay
from phystem.systems.ring.configs import RingCfg, SpaceCfg, RingCfg
from phystem.systems.ring import utils


class BaseGraph(ABC):
    @abstractmethod
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs: dict, graph_cfg=None):
        pass

    @abstractmethod
    def update(self):
        pass

class MainGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs: dict, graph_cfg: MainGraphCfg=None) -> None:
        '''
        Gráfico das partículas com a opção de desenhar os círculos dos raios de interação.
        '''
        if graph_cfg is None:
            graph_cfg = MainGraphCfg()

        self.num_rings = solver.num_max_rings

        self.ax = ax
        self.space_cfg: SpaceCfg = sim_configs["space_cfg"]
        self.dynamic_cfg: RingCfg = sim_configs["dynamic_cfg"]
        self.solver = solver
        self.graph_cfg = graph_cfg

        # self.event_handler = MainEventHandler(self, self.graph_cfg)
        self.forces_state = deepcopy(self.graph_cfg.get_show_forces())
        self.pos_cont_state = self.graph_cfg.show_pos_cont
        self.center_mass_state = self.graph_cfg.show_center_mass
        self.inside_state = self.graph_cfg.show_inside

        self.circles: list[list[Circle]] = None
        self.circles_col: list[PatchCollection] = None

        self.arrows: list[dict[str, Quiver]] = []

        self.lines: list[LineCollection] = None
        self.points: PathCollection = None
        self.points_continuos: list[PathCollection] = None
        
        self.pos_t_ref = solver.pos_t

        self.rings_ids = solver.rings_ids
        self.pos = solver.pos
        self.graph_points = solver.graph_points

        self.cpp_is_debug = self.graph_cfg.cpp_is_debug

        self.init()

    @property
    def pos_t(self):
        if self.cpp_is_debug:
            return self.pos_t_ref
        else:
            return np.array([np.array(p).T for  p in self.pos]) 

    @property
    def num_active_rings(self):
        return self.solver.num_active_rings

    def get_segments(self, ring_id: int) -> list:
        n = len(self.pos[ring_id])

        # segments = [[self.graph_points[3*n - 1], self.graph_points[0]]]
        # segments.append([self.graph_points[0], self.graph_points[1]])
        # for id in range(1, n):
        #     g_id = 3 * id
        #     segments.append([self.graph_points[g_id-1], self.graph_points[g_id]])
        #     segments.append([self.graph_points[g_id], self.graph_points[g_id+1]])
        
        segments = []
        for id in range(n-1):
            g_id = 3 * id
            segments.append([self.graph_points[ring_id][g_id], self.graph_points[ring_id][g_id+1]])
            segments.append([self.graph_points[ring_id][g_id+2], self.graph_points[ring_id][g_id+3]])
        
        g_id = 3 * (n - 1)
        segments.append([self.graph_points[ring_id][g_id], self.graph_points[ring_id][g_id+1]])
        segments.append([self.graph_points[ring_id][g_id+2], self.graph_points[ring_id][0]])
        
        return segments

    def get_distances(self, ring_id: int):
        diff = np.array(self.solver.differences[ring_id])
        distances = np.sqrt(diff[:, 0]**2 + diff[:, 1]**2)

        dist_to_colors = []
        for d in distances:
            dist_to_colors.append(d)
            dist_to_colors.append(d)

        return dist_to_colors

    def get_forces(self, ring_id: int) -> dict[str, np.ndarray]:
        forces = {
            "spring": np.array(self.solver.spring_forces[ring_id]).T,
            "vol": np.array(self.solver.vol_forces[ring_id]).T,
            "area": np.array(self.solver.area_forces[ring_id]).T,
            "total": np.array(self.solver.total_forces[ring_id]).T,
        }
        return forces
    
    def get_force(self, ring_id: int, f_name: str) -> np.ndarray:
        if f_name == "spring":
            force_cpp = self.solver.spring_forces[ring_id]
        if f_name == "vol":
            force_cpp = self.solver.vol_forces[ring_id]
        if f_name == "area":
            force_cpp = self.solver.area_forces[ring_id]
        if f_name == "total":
            force_cpp = self.solver.total_forces[ring_id]
            
        return np.array(force_cpp).T

    def get_ith_points(self):
        x, y = [], []
        id = len(self.pos[0]) - 1
        # for ring_pos in self.pos:
        for ring_id in self.rings_ids[:self.num_active_rings]:
            ring_pos = self.pos[ring_id]
            x.append(ring_pos[id][0])
            y.append(ring_pos[id][1])
        return x, y
    
    def get_pos(self):
        pos = np.array(self.solver.pos)[self.ring_ids]
        return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])
    
    def init(self):
        h = self.space_cfg.height/2
        l = self.space_cfg.length/2
        r_scale = 1
        self.ax.set_ylim(-r_scale*h, r_scale*h)
        self.ax.set_xlim(-r_scale*l, r_scale*l)

        self.ax.set_aspect(1)

        # Borders
        self.ax.plot([-l, -l], [ h, -h], color="black")
        self.ax.plot([ l,  l], [ h, -h], color="black")
        self.ax.plot([ l, -l], [ h,  h], color="black")
        self.ax.plot([ l, -l], [-h, -h], color="black")

        self.update_ring_ids()        

        points_s = 5
        # self.points = [self.ax.scatter(*ring_pos_t, s=16, zorder=2) for ring_pos_t in self.pos_t]
        # self.points = [self.ax.scatter(*self.pos_t[ring_id], s=16, zorder=2) for ring_id in self.rings_ids[:self.num_active_rings]]
        self.points = [self.ax.scatter(*ring_pos_t, s=points_s, zorder=2) for ring_pos_t in self.pos_t]
        # self.points = self.ax.scatter(*self.get_pos().T, s=points_s, zorder=2)
       
        self.ith_points = self.ax.scatter(*self.get_ith_points(), c="black", s=points_s, zorder=2)

        inside_points_arr = np.array(self.solver.in_pol_checker.inside_points).T
        if inside_points_arr.size == 0:
            inside_points_arr = np.array([[], []])

        self.inside_points = self.ax.scatter(
            *inside_points_arr, 
            c="black", marker="x", zorder=10,
        )
        if not self.graph_cfg.show_inside:
            self.inside_points.set_visible(False)
       
        self.center_mass = self.ax.scatter(*np.array(self.solver.center_mass).T, c="black")
        if not self.graph_cfg.show_center_mass:
            self.center_mass.set_visible(False)

        self.points_continuos = [self.ax.scatter(*(np.array(self.solver.pos[ring_id]).T)) for ring_id in range(self.num_rings)]
        if not self.graph_cfg.show_pos_cont:
            [artist.set_visible(False) for artist in self.points_continuos]

        if self.cpp_is_debug:
            dr = self.dynamic_cfg.spring_r/2
            self.lines = []
            for ring_id in range(self.num_rings):
                ring_lines = LineCollection(self.get_segments(ring_id),
                    norm=colors.Normalize(self.dynamic_cfg.spring_r - dr , self.dynamic_cfg.spring_r + dr),
                    cmap=colors.LinearSegmentedColormap.from_list("spring_tension", ["blue", "black", "red"]),
                    linewidths=1,
                    zorder=1,
                )
                self.lines.append(ring_lines)

                self.ax.add_collection(ring_lines)

        stokes_cfg = self.solver.cpp_solver.stokes_cfg
        self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=False))

        #==
        # Circles
        #==
        self.circles = []
        self.circles_col = []
        for ring_id in range(self.num_rings):
            ring_circles = []
            for x_i, y_i in zip(self.pos_t[ring_id][0], self.pos_t[ring_id][1]):
                ring_circles.append(Circle((x_i, y_i), self.dynamic_cfg.diameter/2, fill=False))
            
            self.circles.append(ring_circles)
            self.circles_col.append(PatchCollection(ring_circles, match_original=True))
            if not self.graph_cfg.show_circles:
                self.circles_col[-1].set_visible(False)
            
            self.ax.add_collection(self.circles_col[-1])

        #==
        # Forces
        #==
        if self.cpp_is_debug:
            for ring_id in range(self.num_rings):
                forces = self.get_forces(ring_id)
                ring_arrows = {}
                for f_name, f_value in forces.items():
                    ring_arrows[f_name] = self.ax.quiver(
                        self.pos_t[ring_id][0],
                        self.pos_t[ring_id][1],
                        f_value[0],    
                        f_value[1],   
                        scale=20, 
                        color=self.graph_cfg.force_to_color[f_name],
                    )
                
                self.arrows.append(ring_arrows)
                
                for f_name, show_force in self.graph_cfg.get_show_forces().items():
                    if not show_force:
                        self.arrows[-1][f_name].set_visible(False)

    def update_ring_ids(self):
        self.ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]

    def update(self):
        # TODO: Setar os segmentos sem reconstruir os mesmos.
        #   Talvez criar os segmentos no c++ e apenas referenciar eles aqui.

        # self.update_ring_ids()        

        # Distinct ring point for rotation visualization
        ith_points = np.array(self.get_ith_points()).T
        self.ith_points.set_offsets(ith_points)

        #==
        # Inside Points
        #==
        if self.graph_cfg.show_inside:
            inside_points = self.solver.in_pol_checker.inside_points
            num_inside_points = self.solver.in_pol_checker.num_inside_points
            if num_inside_points > 0:
                self.inside_points.set_visible(True)
                self.inside_points.set_offsets(inside_points[:num_inside_points])
            else:
                self.inside_points.set_visible(False)
        else:
            self.inside_points.set_visible(False)


        #==
        # Center of mass
        #==
        if self.graph_cfg.show_center_mass:
            if self.center_mass.get_visible() == False:
                self.center_mass.set_visible(True)
            self.center_mass.set_offsets(np.array(self.solver.center_mass)[self.rings_ids[:self.num_active_rings]])
        else:
            if self.center_mass.get_visible() == True:
                self.center_mass.set_visible(False)


        #==
        # Ring lines
        #==
        # self.points.set_offsets(self.get_pos())
        
        for i in range(self.num_rings):
            self.points[i].set_visible(False)
            if self.cpp_is_debug:
                self.lines[i].set_visible(False)

        for ring_id in self.rings_ids[:self.num_active_rings]:
            self.points[ring_id].set_visible(True)
            self.points[ring_id].set_offsets(self.pos[ring_id])
            if self.cpp_is_debug:
                self.lines[ring_id].set_visible(True)
                self.lines[ring_id].set_segments(self.get_segments(ring_id))
                self.lines[ring_id].set_array(self.get_distances(ring_id))

        #==
        # Pos Continuos
        #==
        if self.graph_cfg.show_pos_cont:
            for i in range(self.num_rings):
                self.points_continuos[i].set_visible(False)

            for ring_id in self.rings_ids[:self.num_active_rings]:
                self.points_continuos[ring_id].set_visible(True)
                self.points_continuos[ring_id].set_offsets(
                    self.solver.pos_continuos[ring_id])
        else:
            for ring_id in self.rings_ids[:self.num_active_rings]:
                self.points_continuos[ring_id].set_visible(False)

        #==
        # Circles
        #==
        if self.graph_cfg.show_circles:
            for i in range(self.num_rings):
                self.circles_col[i].set_visible(False)

            for ring_id in self.rings_ids[:self.num_active_rings]:
                self.circles_col[ring_id].set_visible(True)

                for id in range(len(self.pos_t[ring_id][0])):
                    self.circles[ring_id][id].center = (self.pos_t[ring_id][0][id], self.pos_t[ring_id][1][id])
                self.circles_col[ring_id].set_paths(self.circles[ring_id])
        else:
            for ring_id in self.rings_ids[:self.num_active_rings]:
                self.circles_col[ring_id].set_visible(False)

        #==
        # Arrows
        #==
        if self.cpp_is_debug:
            for f_name, show_force in self.graph_cfg.get_show_forces().items():
                if show_force:

                    for i in range(self.num_rings):
                        self.arrows[i][f_name].set_visible(False)
                    
                    for ring_id in self.rings_ids[:self.num_active_rings]:
                        forces = self.get_force(ring_id, f_name)
                        self.arrows[ring_id][f_name].set_visible(True)
                        self.arrows[ring_id][f_name].set_UVC(U=forces[0], V=forces[1])
                        self.arrows[ring_id][f_name].set_offsets(self.pos[ring_id])
                else:
                    for ring_id in self.rings_ids[:self.num_active_rings]:
                        self.arrows[ring_id][f_name].set_visible(False)

        return

class SimpleGraph(BaseGraph):
    def __init__(self, fig: Figure, ax: Axes, solver: CppSolver, sim_configs, graph_cfg: SimpleGraphCfg=None):
        self.ax = ax
        self.solver = solver
        self.graph_cfg = graph_cfg
        space_cfg: SpaceCfg = sim_configs["space_cfg"]

        if self.graph_cfg is None:
            self.graph_cfg = SimpleGraphCfg()

        h = space_cfg.height/2
        l = space_cfg.length/2
        r_scale = 1
        self.ax.set_ylim(-r_scale*h, r_scale*h)
        self.ax.set_xlim(-r_scale*l, r_scale*l)

        self.ax.set_aspect(1)

        # Borders
        self.ax.plot([-l, -l], [ h, -h], color="black")
        self.ax.plot([ l,  l], [ h, -h], color="black")
        self.ax.plot([ l, -l], [ h,  h], color="black")
        self.ax.plot([ l, -l], [-h, -h], color="black")

        self.cmap = cm.Set1
        
        stokes_cfg = self.solver.cpp_solver.stokes_cfg
        self.ax.add_patch(Circle((stokes_cfg.obstacle_x, stokes_cfg.obstacle_y), stokes_cfg.obstacle_r, fill=False,  zorder=3))

        self.update_ring_ids()
        self.colors = self.init_colors(self.solver.num_max_rings, self.solver.num_particles) 

        if self.graph_cfg.show_rings:
            self.unique_ring_color = False
            if self.graph_cfg.rings_kwargs.get("c", None) is not None:
                self.unique_ring_color = True
                self.points = self.ax.scatter(*self.get_pos().T, zorder=2, 
                   **self.graph_cfg.rings_kwargs)
            else:
                self.points = self.ax.scatter(*self.get_pos().T, cmap=self.cmap, zorder=2, 
                    c=self.colors[self.ring_ids].flatten(), vmin=0, vmax=len(self.cmap.colors)-1, **self.graph_cfg.rings_kwargs)
        
        if self.graph_cfg.show_density:
            cell_shape = self.graph_cfg.cell_shape
            l, h = space_cfg.length, space_cfg.height
            ring_d = utils.get_ring_radius(sim_configs["dynamic_cfg"].diameter, sim_configs["creator_cfg"].num_p) * 2
            num_rows = int(h/(ring_d * cell_shape[0]))
            num_cols = int(l/(ring_d * cell_shape[1]))

            print(f"grid_shape: {num_rows}, {num_cols}")
            self.density_eq = cell_shape[0]*cell_shape[1]
            self.grid = utils.RegularGrid(space_cfg.length, space_cfg.height, num_cols, num_rows)

            self.density = ax.pcolormesh(*self.grid.edges, self.get_density(), shading='flat',
                    zorder=1, cmap="coolwarm" ,**self.graph_cfg.density_kwargs)
            
            fig.colorbar(self.density, **self.graph_cfg.cbar_kwargs)
            ax.set(**self.graph_cfg.ax_kwargs)

        # self.points = self.ax.scatter(*self.get_pos().T, s=points_s, cmap=cm.hsv, 
        #     c=self.get_colors(), vmin=-np.pi, vmax=np.pi)
        
    def update_ring_ids(self):
        self.ring_ids = self.solver.rings_ids[:self.solver.num_active_rings]

    def get_pos(self):
        pos = np.array(self.solver.pos)[self.ring_ids]
        
        # self.colors[self.ring_ids] = pos[:,0,0].reshape(pos.shape[0], 1)

        return pos.reshape(pos.shape[0] * pos.shape[1], pos.shape[2])
    
    def get_density(self):
        cm = utils.get_cm(np.array(self.solver.pos)[self.ring_ids])
        coords = self.grid.coords(cm)
        count = self.grid.count(coords)/self.density_eq - 1
        return count

    def init_colors(self, num_rings, num_particles):
        c = np.zeros((num_rings, num_particles), dtype=np.int16)
        color_id = np.random.choice(range(len(self.cmap.colors)), num_rings)
        for i in range(num_rings):
            c[i] = color_id[i]

        return c
    
    def get_colors(self):
        return self.colors[self.ring_ids].flatten()
    
    def update(self):
        self.update_ring_ids()
        if self.graph_cfg.show_rings:
            self.points.set_offsets(self.get_pos())
            if not self.unique_ring_color:
                self.points.set_array(self.get_colors())

        if self.graph_cfg.show_density:
            self.density.set_array(self.get_density())

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
                
                fig.colorbar(self.points, location="right", label="(rad)")
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