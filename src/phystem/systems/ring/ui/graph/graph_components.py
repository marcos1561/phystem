import copy
import numpy as np

from matplotlib import collections
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Circle, Rectangle
from matplotlib import colors, colorbar

from phystem.systems.ring.solvers import CppSolver
from phystem.systems.ring.configs import RingCfg, SpaceCfg, StokesCfg
from phystem.systems.ring import utils
from phystem.systems.ring import rings_quantities
from .active_rings import ActiveRings
from .graphs_cfg import ParticleCircleCfg, RegionsCfg

class ArtistList:
    def __init__(self):
        self._artist_list: dict[str, Artist] = {}

    def add(self, name, artist: Artist):
        self._artist_list[name] = artist

    def get(self, name):
        return self._artist_list[name]
    
    def remove(self):
        for artist in self._artist_list.values():
            artist.remove()

    @property
    def items(self):
        return self._artist_list.values()

class GraphComponent:
    def __init__(self, ax: Axes, show_cfg_name: str):
        self.ax = ax
        self.show_cfg_name = show_cfg_name

        self.has_added = False
        self.has_removed = True
        self.artist_list = ArtistList()

    def add(self):
        self.ax.set_anchor('C') 
    
    def remove(self):
        self.artist_list.remove()

    def update_artists(self):
        pass

    def update(self, to_show):
        if to_show:
            if not self.has_added:
                self.add()
                self.has_added = True
                self.has_removed = False
            self.update_artists()
        else:
            if not self.has_removed:
                self.remove()
                self.has_added = False
                self.has_removed = True

class CollectionComp(GraphComponent):
    def add(self):
        super().add()
        for artist in self.artist_list.items:
            self.ax.add_collection(artist)

class PatchComp(GraphComponent):
    def add(self):
        super().add()
        for artist in self.artist_list.items:
            self.ax.add_patch(artist)

class ColorBarableComp(CollectionComp):
    def get_color_bar(self) -> colorbar.Colorbar:
        pass

    def add(self):
        self.colormap = self.get_color_bar()
        return super().add()
    
    def remove(self):
        self.colormap.remove()
        return super().remove()

class ParticleCircles(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, radius, radius2=None, cfg: ParticleCircleCfg=None):
        super().__init__(ax, show_cfg_name="show_circles")
        if cfg is None:
            cfg = ParticleCircleCfg()

        self.has_radius2 = radius2 is not None
        self.cfg = cfg

        
        num_max_rings = active_rings.solver.num_max_rings
        num_particles = active_rings.num_particles

        self.active_rings = active_rings
        self.circles = []
        self.circles_adh = []
        for _ in range(num_max_rings * num_particles):
            self.circles.append(Circle((0, 0), radius))
            if self.has_radius2:
                self.circles_adh.append(Circle((0, 0), radius2))
        self.circles = np.array(self.circles)
        self.circles_adh = np.array(self.circles_adh)

        self.color = cfg.color
        kwargs = {}
        if cfg.color is not None:
            kwargs["edgecolor"] = cfg.color
        
        self.artist = PatchCollection([],
            facecolors="none",
            **kwargs,
        )

        self.artist_adh = PatchCollection([],
            facecolors="none",
            edgecolor="yellow",
        )

        self.artist_list.add("main", self.artist)
        if self.has_radius2:
            self.artist_list.add("adh", self.artist_adh)

    def update_artists(self):
        pos = self.active_rings.pos

        for idx, pos_i in enumerate(pos):
            self.circles[idx].center = pos_i
        self.artist.set_paths(self.circles[:self.active_rings.num_particles_active])

        if self.has_radius2:
            for idx, pos_i in enumerate(pos):
                self.circles_adh[idx].center = pos_i
            self.artist_adh.set_paths(self.circles_adh[:self.active_rings.num_particles_active])

        if self.cfg.color is None:
            if self.cfg.facecolor:
                if self.cfg.match_face_edge_color:
                    self.artist.set(edgecolor=self.active_rings.colors_rgb)
                else:
                    self.artist.set(edgecolor="black")
                
                self.artist.set(facecolors=self.active_rings.colors_rgb)
            else:
                self.artist.set(facecolors="none")
                self.artist.set_edgecolor(self.active_rings.colors_rgb)
        else:
            if self.cfg.facecolor:
                self.artist.set(facecolors=self.cfg.color)
                if self.cfg.match_face_edge_color:
                    self.artist.set_edgecolor(self.cfg.color)
                else:
                    self.artist.set_edgecolor("black")
            else:
                self.artist.set(facecolors="none")
                self.artist.set_edgecolor(self.cfg.color)

class ParticlesScatter(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, zorder, scatter_kwargs):
        super().__init__(ax, show_cfg_name="show_scatter")
        self.active_rings = active_rings
        
        self.unique_ring_color = False
        if scatter_kwargs.get("c") is not None:
            self.unique_ring_color = True
            self.artist = self.ax.scatter(*self.active_rings.pos.T, zorder=zorder, 
                **scatter_kwargs)
        else:
            # self.artist = self.ax.scatter(*self.active_rings.pos.T, zorder=zorder,
            #     cmap=self.active_rings.cmap, c=self.active_rings.colors_value, vmin=0, vmax=1, **scatter_kwargs)
            self.artist = self.ax.scatter(*self.active_rings.pos.T, zorder=zorder,
                c=self.active_rings.colors_rgb, **scatter_kwargs)
        self.artist.remove()
        self.artist_list.add("main", self.artist)
        
    def update_artists(self):
        self.artist.set_offsets(self.active_rings.pos)
        if not self.unique_ring_color:
            # self.artist.set_array(self.active_rings.colors_value)
            self.artist.set_color(self.active_rings.colors_rgb)

class ParticlesScatterCont(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, zorder, scatter_kwargs):
        super().__init__(ax, show_cfg_name="show_scatter_cont")
        self.active_rings = active_rings

        self.unique_ring_color = False
        if scatter_kwargs.get("c", None) is not None:
            self.unique_ring_color = True
            self.artist = self.ax.scatter([], [], zorder=zorder, 
                **scatter_kwargs)
        else:
            # self.artist = self.ax.scatter([], [], zorder=zorder,
            #     cmap=self.active_rings.cmap, vmin=0, vmax=1, **scatter_kwargs)
            self.artist = self.ax.scatter([], [], zorder=zorder, **scatter_kwargs)
        self.artist.remove()
        self.artist_list.add("main", self.artist)
        
    def update_artists(self):
        self.artist.set_offsets(self.active_rings.pos_continuos)
        if not self.unique_ring_color:
            # self.artist.set_array(self.active_rings.colors_value)
            self.artist.set_color(self.active_rings.colors_rgb)

class RingSprings(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, solver: CppSolver, dynamic_cfg: RingCfg):
        super().__init__(ax, show_cfg_name="show_springs")
        self.active_rings = active_rings
        self.num_particles = active_rings.num_particles
        self.solver = solver
        self.graph_points = solver.graph_points

        dr = dynamic_cfg.spring_r/2
        self.artist = LineCollection([],
            norm=colors.Normalize(dynamic_cfg.spring_r - dr , dynamic_cfg.spring_r + dr),
            cmap=colors.LinearSegmentedColormap.from_list("spring_tension", ["blue", "black", "red"]),
            linewidths=1,
            zorder=1,
        )
        self.artist_list.add("main", self.artist)

    def get_segments(self) -> list:
        segments = []

        n = self.num_particles
        for ring_id in self.active_rings.ids:
            for id in range(n-1):
                g_id = 3 * id
                segments.append([self.graph_points[ring_id][g_id], self.graph_points[ring_id][g_id+1]])
                segments.append([self.graph_points[ring_id][g_id+2], self.graph_points[ring_id][g_id+3]])
        
            g_id = 3 * (n - 1)
            segments.append([self.graph_points[ring_id][g_id], self.graph_points[ring_id][g_id+1]])
            segments.append([self.graph_points[ring_id][g_id+2], self.graph_points[ring_id][0]])
        
        return segments

    def get_distances(self):
        dist_to_colors = []
        for ring_id in self.active_rings.ids:
            diff = np.array(self.solver.differences[ring_id])
            distances = np.sqrt(diff[:, 0]**2 + diff[:, 1]**2)

            for d in distances:
                dist_to_colors.append(d)
                dist_to_colors.append(d)

        return dist_to_colors

    def update_artists(self):
        self.artist.set_segments(self.get_segments())
        self.artist.set_array(self.get_distances())

class Density(ColorBarableComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, cell_shape: tuple, sim_configs, artist_kwargs, colorbar_kwargs=None):
        super().__init__(ax, show_cfg_name="show_density")
        if colorbar_kwargs is None:
            colorbar_kwargs = {}
        self.colorbar_kwargs = colorbar_kwargs
        
        self.active_rings = active_rings

        l, h = sim_configs["space_cfg"].length, sim_configs["space_cfg"].height
        ring_d = utils.get_ring_radius(sim_configs["dynamic_cfg"].diameter, sim_configs["creator_cfg"].num_particles) * 2
        num_rows = int(h/(ring_d * cell_shape[0]))
        num_cols = int(l/(ring_d * cell_shape[1]))

        print(f"grid_shape: {num_rows}, {num_cols}")
        self.density_eq = cell_shape[0]*cell_shape[1]
        self.density_calc = rings_quantities.Density(utils.RegularGrid(l, h, num_cols, num_rows))
        # self.grid = utils.RegularGrid(l, h, num_cols, num_rows)

        self.artist = ax.pcolormesh(*self.density_calc.grid.edges, self.get_density(), shading='flat',
                zorder=1, cmap="coolwarm" ,**artist_kwargs)
        self.artist.remove()

        self.artist_list.add("main", self.artist)

    def get_color_bar(self):
        return self.ax.figure.colorbar(self.artist, ax=self.ax, **self.colorbar_kwargs)

    def get_density(self):
        cm = np.array(self.active_rings.solver.center_mass)[self.active_rings.ids]
        # coords = self.grid.coords(cm)
        # count = self.grid.count(coords)/self.density_eq - 1
        # return count
        return self.density_calc.get_from_cm(cm)/self.density_eq - 1

    def update_artists(self):
        self.artist.set_array(self.get_density())

class RingForce(CollectionComp):
    artist: collections.PolyCollection
    def __init__(self, ax: Axes, active_rings: ActiveRings, solver_forces, color: str, show_cfg_name, artist_kwargs=None):
        super().__init__(ax, show_cfg_name)
        self.active_rings = active_rings
        self.solver_forces = solver_forces
        self.forces = np.empty((self.active_rings.total_num_particles, 2), dtype=float)
        
        if artist_kwargs is None:
            artist_kwargs = {}
        
        self.artist_kwargs = {
            "color": color, 
            "scale": 1,
            "angles": "xy",
            "scale_units": "xy",
        }
        self.artist_kwargs.update(artist_kwargs)

        self.artist = self.ax.quiver(
                [], [], [], [],   
                scale=20, 
                color=color,
                **artist_kwargs
        )
        self.artist.remove()
        self.artist_list.add("main", self.artist)
    
    def update_forces(self):
        count = 0
        for ring_id in self.active_rings.ids:
            for p_id in range(self.active_rings.num_particles):
                self.forces[count] = self.solver_forces[ring_id][p_id]
                count += 1

    def update_artists(self):
        self.update_forces()

        if self.artist in self.ax.collections:
            self.artist.remove()
        
        self.artist = self.ax.quiver(
            self.active_rings.pos[:, 0], self.active_rings.pos[:, 1], 
            self.forces[:self.active_rings.num_particles_active, 0], self.forces[:self.active_rings.num_particles_active, 1],   
            **self.artist_kwargs
        )

        # self.artist.set_offsets(self.active_rings.pos)
        # self.artist.set_UVC(U=self.forces[:self.active_rings.num_particles_active, 0], V=self.forces[:self.active_rings.num_particles_active, 1])

        self.artist_list.add("main", self.artist)

class CenterMass(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings):
        super().__init__(ax, "show_cms")
        self.active_rings = active_rings

        self.artist = self.ax.scatter([], [], c="black")
        self.artist.remove()

        self.artist_list.add("main", self.artist)

    def update_artists(self):
        self.artist.set_offsets(self.active_rings.cms)

class InvasionPoints(CollectionComp):
    def __init__(self, ax: Axes, solver: CppSolver):
        super().__init__(ax, "show_invasion")
        self.solver = solver
        self.artist = self.ax.scatter([], [],
            c="black", marker="x", zorder=10)
        self.artist.remove()

        self.artist_list.add("main", self.artist)

    def update_artists(self):
        inside_points = self.solver.in_pol_checker.inside_points
        num_inside_points = self.solver.in_pol_checker.num_inside_points 
        if num_inside_points > 0:
            self.artist.set_visible(True)
            self.artist.set_offsets(inside_points[:num_inside_points])
        else:
            self.artist.set_visible(False)

class IthPoints(CollectionComp):
    def __init__(self, ax: Axes, active_rings: ActiveRings, zorder, particle_idx="last"):
        super().__init__(ax, "show_ith_points")
        self.active_rings = active_rings

        if particle_idx == "last":
            particle_idx = self.active_rings.num_particles - 1
        self.particle_idx = particle_idx

        self.artist = ax.scatter([], [], c="black", zorder=zorder)
        self.artist.remove()

        self.artist_list.add("main", self.artist)

    def update_artists(self):
        num_p = self.active_rings.num_particles
        end_idx = self.particle_idx + (len(self.active_rings.ids) - 1) * num_p
        ith_ids = np.arange(self.particle_idx, end_idx+1, num_p)
        
        ith_pos = self.active_rings.pos[ith_ids]
        self.artist.set_offsets(ith_pos)

class Regions(PatchComp):
    def __init__(self, ax, space_cfg: SpaceCfg, stokes_cfg: StokesCfg,
            configs: RegionsCfg=None,       
        ):
        super().__init__(ax, "show_regions")
        if configs is None:
            configs = RegionsCfg()

        h, l = space_cfg.height, space_cfg.length
        cl = stokes_cfg.create_length
        rl = stokes_cfg.remove_length

        self.create_rect = Rectangle(
            xy=[-l/2, -h/2], width=cl, height=h,
            color=configs.create_color, alpha=configs.alpha,
        )

        self.remove_rect = Rectangle(
            xy=[l/2-rl, -h/2], width=rl, height=h,
            color=configs.remove_color, alpha=configs.alpha,
        )

        self.artist_list.add("create", self.create_rect)
        self.artist_list.add("remove", self.remove_rect)
