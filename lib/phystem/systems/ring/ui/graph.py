import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection, PatchCollection
from matplotlib.patches import Circle
from matplotlib.quiver import Quiver 
from matplotlib import colors 

from copy import deepcopy

from phystem.gui_phystem import graph
from phystem.utils.timer import TimeIt 

from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.configs import RingCfg, SpaceCfg, CreatorCfg, RingCfg

class GraphCfg:
    def __init__(self, show_circles=False, show_f_spring=False, show_f_vol=False, show_f_area=False, 
        show_f_total=False, force_to_color=None, begin_paused=False, cpp_is_debug=True) -> None:
        self.show_circles = show_circles
        self.show_f_spring = show_f_spring
        self.show_f_vol = show_f_vol
        self.show_f_area = show_f_area
        self.show_f_total = show_f_total

        self.show_pos_cont = False

        self.begin_paused = begin_paused
        self.cpp_is_debug = cpp_is_debug

        self.force_to_color = force_to_color
        if force_to_color is None:
            self.force_to_color = {
                "spring": "red",
                "vol": "blue",
                "area": "green",
                "total": "black",
            }

        self.f_name_to_show = {
            "spring": self.show_f_spring,
            "vol": self.show_f_vol,
            "area": self.show_f_area,
            "total": self.show_f_total,
        }

    def get_show_force(self, name):
        return self.f_name_to_show[name]

    def set_show_force(self, name: str, value: bool):
        if name == "spring":
            self.show_f_spring = value
        elif name == "vol":
            self.show_f_vol = value
        elif name == "area":
            self.show_f_area = value
        elif name == "total":
            self.show_f_total = value

class MainGraph:
    def __init__(self, ax: Axes, solver: CppSolver, space_cfg: SpaceCfg, dynamic_cfg: RingCfg, graph_cfg: GraphCfg=None) -> None:
        '''
        Gráfico das partículas com a opção de desenhar os círculos dos raios de interação.
        '''
        self.num_rings = solver.num_rings

        self.ax = ax
        self.space_cfg = space_cfg
        self.dynamic_cfg = dynamic_cfg
        self.solver = solver
        self.graph_cfg = graph_cfg

        # self.event_handler = MainEventHandler(self, self.graph_cfg)
        self.forces_state = deepcopy(self.graph_cfg.f_name_to_show)
        self.pos_cont_state = self.graph_cfg.show_pos_cont

        self.circles: list[list[Circle]] = None
        self.circles_col: list[PatchCollection] = None

        self.arrows: list[dict[str, Quiver]] = []

        self.lines: list[LineCollection] = None
        self.points: list[PathCollection] = None
        self.points_continuos: list[PathCollection] = None
        
        self.pos_t_ref = solver.pos_t

        self.pos = solver.pos
        self.graph_points = solver.graph_points

        self.cpp_is_debug = self.graph_cfg.cpp_is_debug

    @property
    def pos_t(self):
        if self.cpp_is_debug:
            return self.pos_t_ref
        else:
            return np.array([np.array(p).T for  p in self.pos]) 

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
        for ring_pos in self.pos:
            x.append(ring_pos[id][0])
            y.append(ring_pos[id][1])
        return x, y

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

        self.points = [self.ax.scatter(*ring_pos_t, s=16, zorder=2) for ring_pos_t in self.pos_t]
        self.ith_points = self.ax.scatter(*self.get_ith_points(), c="black", s=22, zorder=2)
       
        self.points_continuos = [self.ax.scatter(*(np.array(self.solver.pos_continuos[ring_id]).T)) for ring_id in range(self.num_rings)]
        if not self.graph_cfg.show_pos_cont:
            [artist.remove() for artist in self.points_continuos]

        # self.gg_points = self.ax.scatter(*np.array(self.graph_points).T)

        if self.cpp_is_debug:
            dr = self.dynamic_cfg.spring_r/2
            self.lines = []
            for ring_id in range(self.num_rings):
                ring_lines = LineCollection(self.get_segments(ring_id),
                    norm=colors.Normalize(self.dynamic_cfg.spring_r - dr , self.dynamic_cfg.spring_r + dr),
                    cmap=colors.LinearSegmentedColormap.from_list("spring_tension", ["blue", "black", "red"]),
                    linewidths=3,
                    zorder=1,
                )
                self.lines.append(ring_lines)

                self.ax.add_collection(ring_lines)

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
                self.circles_col[-1].set_paths([])
            
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
                        scale=8, 
                        color=self.graph_cfg.force_to_color[f_name],
                    )
                
                self.arrows.append(ring_arrows)
                
                for f_name, show_force in self.graph_cfg.f_name_to_show.items():
                    if not show_force:
                        self.arrows[-1][f_name].remove()
                

    def update(self):
        # TODO: Setar os segmentos sem reconstruir os mesmos.
        #   Talvez criar os segmentos no c++ e apenas referenciar eles aqui.
        
        ith_points = np.array(self.get_ith_points()).T
        self.ith_points.set_offsets(ith_points)

        for ring_id in range(self.num_rings):
            self.points[ring_id].set_offsets(self.pos[ring_id])
            
            if self.cpp_is_debug:
                self.lines[ring_id].set_segments(self.get_segments(ring_id))
                self.lines[ring_id].set_array(self.get_distances(ring_id))

        #==
        # Pos Continuos
        #==
        if self.graph_cfg.show_pos_cont:
            if not self.pos_cont_state:
                for ring_id in range(self.num_rings):
                    self.ax.add_artist(self.points_continuos[ring_id])
                self.pos_cont_state = True

            for ring_id in range(self.num_rings):
                self.points_continuos[ring_id].set_offsets(self.solver.pos_continuos[ring_id])
        else:
            if self.pos_cont_state:
                for ring_id in range(self.num_rings):
                    self.points_continuos[ring_id].remove()
                self.pos_cont_state = False

        #==
        # Circles
        #==
        if self.graph_cfg.show_circles:
            for ring_id in range(self.num_rings):
                for id in range(len(self.pos_t[ring_id][0])):
                    self.circles[ring_id][id].center = (self.pos_t[ring_id][0][id], self.pos_t[ring_id][1][id])
                self.circles_col[ring_id].set_paths(self.circles[ring_id])
        else:
            for ring_id in range(self.num_rings):
                self.circles_col[ring_id].set_paths([])

        #==
        # Arrows
        #==
        if self.cpp_is_debug:
            forces_names = self.graph_cfg.f_name_to_show.keys()
            for f_name in forces_names:
                show_force = self.graph_cfg.get_show_force(f_name) 
                if show_force:
                    if self.forces_state[f_name] != show_force:
                        self.forces_state[f_name] = show_force
                        for ring_id in range(self.num_rings):
                            self.ax.add_artist(self.arrows[ring_id][f_name])
                    
                    for ring_id in range(self.num_rings):
                        forces = self.get_force(ring_id, f_name)
                        self.arrows[ring_id][f_name].set_UVC(U=forces[0], V=forces[1])
                        self.arrows[ring_id][f_name].set_offsets(self.pos[ring_id])
                else:
                    if self.forces_state[f_name] != show_force:
                        self.forces_state[f_name] = show_force
                        for ring_id in range(self.num_rings):
                            self.arrows[ring_id][f_name].remove()

        # if self.cpp_is_debug:
        #     for ring_id in range(self.num_rings):
        #         for name, forces in self.get_forces(ring_id).items():
        #             show_force = self.graph_cfg.get_show_force(name) 
        #             if show_force:
        #                 if self.forces_state[name] != show_force:
        #                     self.forces_state[name] = show_force
        #                     self.ax.add_artist(self.arrows[ring_id][name])

        #                 self.arrows[ring_id][name].set_UVC(U=forces[0], V=forces[1])
        #                 self.arrows[ring_id][name].set_offsets(self.pos[ring_id])
        #             else:
        #                 if self.forces_state[name] != show_force:
        #                     self.forces_state[name] = show_force
        #                     self.arrows[ring_id][name].remove()

        # return (self.lines, self.points, self.circles_col) + tuple(self.arrows.values())
        return

class Info(graph.Info):
    def __init__(self, ax: Axes, solver: CppSolver, time_it: TimeIt, 
        dynamic_cfg: RingCfg, creator_cfg: CreatorCfg, space_cfg: SpaceCfg) -> None:
        super().__init__(ax)
        self.solver = solver
        self.time_it = time_it
        self.cfg_info = dynamic_cfg.info() + f"N = {creator_cfg.num_p}\n" 

    def get_info(self):
        sim_info = (
            f"$\Delta$T (ms): {self.time_it.mean_time():.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.5f}\n"
            f"Area = {self.solver.cpp_solver.area_debug.area[0]:.3f}\n"
            "\n"
            f"spring_overlap: {self.solver.spring_debug.count_overlap}\n"
            f"vol_overlap   : {self.solver.excluded_vol_debug.count_overlap}\n"
            f"area_overlap  : {self.solver.area_debug.count_overlap}\n"
            f"zero_speed    : {self.solver.update_debug.count_zero_speed}\n"
            "\n"
            f"{self.cfg_info}"
        )

        return sim_info