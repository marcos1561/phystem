import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PathCollection, PatchCollection
from matplotlib.patches import Circle
from matplotlib.quiver import Quiver 

from copy import deepcopy

from ui_phystem import graph
from ic_utils.timer import TimeIt 

from phystem.ring.solvers import CppSolver
from phystem.ring.configs import RingCfg, SpaceCfg, CreateCfg, RingCfg

class GraphCfg:
    def __init__(self, show_circles=False, show_f_spring=False, show_f_vol=False, show_f_total=False, 
        force_to_color=None) -> None:
        self.show_circles = show_circles
        self.show_f_spring = show_f_spring
        self.show_f_vol = show_f_vol
        self.show_f_total = show_f_total

        self.force_to_color = force_to_color
        if force_to_color is None:
            self.force_to_color = {
                "spring": "red",
                "vol": "blue",
                "total": "black",
            }

        self.f_name_to_show = {
            "spring": self.show_f_spring,
            "vol": self.show_f_vol,
            "total": self.show_f_total,
        }

    def get_show_force(self, name):
        return self.f_name_to_show[name]

    def set_show_force(self, name: str, value: bool):
        if name == "spring":
            self.show_f_spring = value
        elif name == "vol":
            self.show_f_vol = value
        elif name == "total":
            self.show_f_total = value

class MainGraph:
    def __init__(self, ax: Axes, solver: CppSolver, space_cfg: SpaceCfg, dynamic_cfg: RingCfg, graph_cfg: GraphCfg=None) -> None:
        '''
        Gráfico das partículas com a opção de desenhar os círculos dos raios de interação.
        '''
        self.ax = ax
        self.space_cfg = space_cfg
        self.dynamic_cfg = dynamic_cfg
        self.solver = solver
        self.graph_cfg = graph_cfg

        # self.event_handler = MainEventHandler(self, self.graph_cfg)
        self.forces_state = deepcopy(self.graph_cfg.f_name_to_show)

        self.circles: list[Circle] = None
        self.circles_col: PatchCollection = None

        self.arrows: dict[str, Quiver] = {}

        self.lines: LineCollection = None
        self.points: PathCollection = None
        
        self.pos_t = solver.pos_t
        self.pos = solver.pos
        self.graph_points = solver.graph_points


    def get_segments(self) -> list:
        n = len(self.pos)

        segments = [[self.graph_points[3*n - 1], self.graph_points[0]]]
        segments.append([self.graph_points[0], self.graph_points[1]])
        for id in range(1, n):
            g_id = 3 * id
            segments.append([self.graph_points[g_id-1], self.graph_points[g_id]])
            segments.append([self.graph_points[g_id], self.graph_points[g_id+1]])
        
        return segments

    def get_forces(self) -> dict[str, np.ndarray]:
        forces = {
            "spring": np.array(self.solver.spring_forces).T,
            "vol": np.array(self.solver.vol_forces).T,
            "total": np.array(self.solver.total_forces).T,
        }
        return forces


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

        self.points = self.ax.scatter(*self.pos_t)
        # self.gg_points = self.ax.scatter(*np.array(self.graph_points).T)

        self.lines = LineCollection(self.get_segments())
        self.ax.add_collection(self.lines)

        #==
        # Circles
        #==
        self.circles = []
        for x_i, y_i in zip(self.pos_t[0], self.pos_t[1]):
            self.circles.append(Circle((x_i, y_i), self.dynamic_cfg.diameter, fill=False))
        
        self.circles_col = PatchCollection(self.circles, match_original=True)
        if not self.graph_cfg.show_circles:
            self.circles_col.set_paths([])
        
        self.ax.add_collection(self.circles_col)

        #==
        # Forces
        #==
        forces = self.get_forces()
        for f_name, f_value in forces.items():
            self.arrows[f_name] = self.ax.quiver(
                self.pos_t[0],
                self.pos_t[1],
                f_value[0],    
                f_value[1],   
                scale=8, 
                color=self.graph_cfg.force_to_color[f_name],
            )
        
        for f_name, show_force in self.graph_cfg.f_name_to_show.items():
            if not show_force:
                self.arrows[f_name].remove()

    def update(self):
        # TODO: Setar os segmentos sem reconstruir os mesmos.
        #   Talvez criar os segmentos no c++ e apenas referenciar eles aqui.
        self.points.set_offsets(self.pos)
        # self.gg_points.set_offsets(self.graph_points)
        
        self.lines.set_segments(self.get_segments())

        #==
        # Circles
        #==
        if self.graph_cfg.show_circles:
            for id in range(len(self.pos_t[0])):
                self.circles[id].center = (self.pos_t[0][id], self.pos_t[1][id])
            self.circles_col.set_paths(self.circles)
        else:
            self.circles_col.set_paths([])

        #==
        # Arrows
        #==
        for name, forces in self.get_forces().items():
            show_force = self.graph_cfg.get_show_force(name) 
            if show_force:
                if self.forces_state[name] != show_force:
                    self.forces_state[name] = show_force
                    self.ax.add_artist(self.arrows[name])

                self.arrows[name].set_UVC(U=forces[0], V=forces[1])
                self.arrows[name].set_offsets(self.pos)
            else:
                if self.forces_state[name] != show_force:
                    self.forces_state[name] = show_force
                    self.arrows[name].remove()

        # return (self.lines, self.points, self.circles_col) + tuple(self.arrows.values())
        return

class Info(graph.Info):
    def __init__(self, ax: Axes, solver: CppSolver, time_it: TimeIt, 
        dynamic_cfg: RingCfg, create_cfg: CreateCfg, space_cfg: SpaceCfg) -> None:
        super().__init__(ax)
        self.solver = solver
        self.time_it = time_it
        self.cfg_info = dynamic_cfg.info() + "\n" f"N = {create_cfg.n}\nL = {space_cfg.size}\n" 

    def get_info(self):
        sim_info = (
            f"$\Delta$T (ms): {self.time_it.mean_time():.3f}\n\n"
            f"t : {self.solver.time:.3f}\n"
            f"dt: {self.solver.dt:.3f}\n"
            f"<V> = {self.solver.mean_vel():.3f}\n"
            "\n"
            f"overlap: {self.solver.count_overlap}\n"
            f"zero_speed: {self.solver.count_zero_speed}\n"
            "\n"
            f"{self.cfg_info}"
        )

        return sim_info