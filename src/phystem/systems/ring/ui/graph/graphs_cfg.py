from enum import Enum, auto

class BaseGraphCfg:
    def __init__(self, begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True, 
        ax_kwargs=None, figure_kwargs=None) -> None:
        if figure_kwargs is None:
            figure_kwargs = {
                "facecolor": "white",
            }
        if ax_kwargs is None:
            ax_kwargs = {}

        self.begin_paused = begin_paused
        self.pause_on_high_vel = pause_on_high_vel
        self.cpp_is_debug = cpp_is_debug
        self.figure_kwargs = figure_kwargs
        self.ax_kwargs = ax_kwargs

class ParticleCircleCfg:
    DEFAULT_COLOR = "#1f77b4"

    def __init__(self, color=None, facecolor=True, match_face_edge_color=False) -> None:
        self.color = color
        self.facecolor = facecolor
        self.match_face_edge_color = match_face_edge_color

class ForceName(Enum):
    spring = auto()
    vol = auto()
    area = auto()
    total = auto()
    obs = auto()
    format = auto()
    invasion = auto()
    creation = auto()

class RegionsCfg:
    def __init__(self, alpha=0.4, create_color="green", remove_color="red"):
        self.alpha = alpha
        self.create_color = create_color
        self.remove_color = remove_color

class SimpleGraphCfg(BaseGraphCfg):
    def __init__(self, begin_paused=False, pause_on_high_vel=False, show_scatter=True, show_density=False,
        show_circles=False, show_springs=False, show_cms=False, show_invasion=False,
        show_ith_points=False, show_scatter_cont=False,
        show_f_springs=False, show_f_vol=False, show_f_area=False, show_f_total=False,
        show_f_format=False, show_f_obs=False, show_f_invasion=False, show_f_creation=False,
        show_regions=False, figure_kwargs=None,
        force_color: dict[ForceName, str]=None, circles_cfg: ParticleCircleCfg=None,
        regions_cfg: RegionsCfg=None,
        density_kwargs=None, scatter_kwargs=None, cbar_kwargs=None, ax_kwargs=None,
        show_particle_info=False,
        cell_shape=None, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug, ax_kwargs, figure_kwargs)
        if cell_shape is None:
            cell_shape = [1, 1]

        self.show_scatter = show_scatter
        self.show_scatter_cont = show_scatter_cont
        self.show_density = show_density
        self.show_circles = show_circles
        self.show_springs = show_springs
        self.show_cms = show_cms
        self.show_invasion = show_invasion
        self.show_ith_points = show_ith_points
        self.show_regions = show_regions
        self.cell_shape = cell_shape

        if circles_cfg is None:
            circles_cfg = ParticleCircleCfg()
        self.circle_cfg = circles_cfg
        
        if regions_cfg is None:
            regions_cfg = RegionsCfg()
        self.regions_cfg = regions_cfg

        self.show_f_springs = show_f_springs
        self.show_f_vol = show_f_vol
        self.show_f_area = show_f_area
        self.show_f_format = show_f_format
        self.show_f_obs = show_f_obs
        self.show_f_total = show_f_total
        self.show_f_invasion = show_f_invasion
        self.show_f_creation = show_f_creation

        self.show_particle_info = show_particle_info

        self.force_color = {
            ForceName.spring: "red",
            ForceName.vol: "blue",
            ForceName.area: "green",
            ForceName.format: "purple",
            ForceName.obs: "gray",
            ForceName.invasion: "orange",
            ForceName.creation: "gray",
            ForceName.total: "black",
        }
        if force_color:
            for fname, color in force_color.items():
                self.force_color[fname] = color

        self.density_kwargs = density_kwargs
        self.cbar_kwargs = cbar_kwargs
        self.scatter_kwargs = scatter_kwargs
        
        for name in ["density_kwargs", "cbar_kwargs", "scatter_kwargs"]:
            if getattr(self, name) is None:
                setattr(self, name, {})

class ReplayGraphCfg(BaseGraphCfg):
    def __init__(self, scatter_kwargs=None, density_kwargs=None, colorbar_kwargs=None, 
        x_lims=None, vel_colors=False, circles_cfg: ParticleCircleCfg=None,
        cell_shape=None, figure_kwargs=None, ax_kwargs=None,
        show_scatter=True, show_circles=False, show_density=False, show_cms=False,
        begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug, ax_kwargs, figure_kwargs)
        if cell_shape is None:
            cell_shape = [1, 1]
            

        self.show_scatter = show_scatter
        self.show_circles = show_circles
        self.show_density = show_density
        self.show_cms = show_cms

        self.x_lims = x_lims
        self.vel_colors =  vel_colors
        self.cell_shape = cell_shape

        if circles_cfg is None:
            circles_cfg = ParticleCircleCfg(color="#1f77b4")
        self.circle_cfg = circles_cfg

        self.scatter_kwargs = scatter_kwargs
        if scatter_kwargs is None:
            self.scatter_kwargs = {}

        # if "c" not in self.scatter_kwargs.keys():
        #     self.scatter_kwargs["c"] = "#1f77b4"

        self.density_kwargs = density_kwargs
        if density_kwargs is None:
            self.density_kwargs = {}
        
        self.colorbar_kwargs = colorbar_kwargs
        if colorbar_kwargs is None:
            self.colorbar_kwargs = {}

        if vel_colors:
            if self.scatter_kwargs.get("c"):
                del self.scatter_kwargs["c"]
            self.circle_cfg.color = None

if __name__ == "__main__":
    print(type(SimpleGraphCfg) == type)