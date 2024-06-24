from enum import Enum, auto

class BaseGraphCfg:
    def __init__(self, begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True) -> None:
        self.begin_paused = begin_paused
        self.pause_on_high_vel = pause_on_high_vel
        self.cpp_is_debug = cpp_is_debug

class ParticleCircleCfg:
    def __init__(self, color=None, facecolor=False) -> None:
        self.color = color
        self.facecolor = facecolor

class SimpleGraphCfg(BaseGraphCfg):
    class ForceName(Enum):
        spring = auto()
        vol = auto()
        area = auto()
        total = auto()
        obs = auto()
        format = auto()
        invasion = auto()

    def __init__(self, begin_paused=False, pause_on_high_vel=False, show_scatter=True, show_density=False,
        show_circles=False, show_springs=False, show_cms=False, show_invasion=False,
        show_ith_points=False, show_scatter_cont=False,
        show_f_springs=False, show_f_vol = False, show_f_area = False, show_f_total = False,
        show_f_format=False, show_f_obs=False, show_f_invasion=False,
        force_color: dict[ForceName, str] = None, circles_color: str = None, circle_facecolor=False,
        density_kwargs=None, rings_kwargs=None, cbar_kwargs=None, ax_kwargs=None,
        cell_shape=None, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug)
        self.show_scatter = show_scatter
        self.show_scatter_cont = show_scatter_cont
        self.show_density = show_density
        self.show_circles = show_circles
        self.show_springs = show_springs
        self.show_cms = show_cms
        self.show_invasion = show_invasion
        self.show_ith_points = show_ith_points
        self.cell_shape = cell_shape

        self.circles_cfg = ParticleCircleCfg(
            color=circles_color, facecolor=circle_facecolor
        )

        self.show_f_springs = show_f_springs
        self.show_f_vol = show_f_vol
        self.show_f_area = show_f_area
        self.show_f_format = show_f_format
        self.show_f_obs = show_f_obs
        self.show_f_total = show_f_total
        self.show_f_invasion = show_f_invasion

        self.force_color = {
            self.ForceName.spring: "red",
            self.ForceName.vol: "blue",
            self.ForceName.area: "green",
            self.ForceName.format: "purple",
            self.ForceName.obs: "gray",
            self.ForceName.invasion: "orange",
            self.ForceName.total: "black",
        }
        if force_color:
            for fname, color in force_color.items():
                self.force_color[fname] = color

        self.density_kwargs = density_kwargs
        self.cbar_kwargs = cbar_kwargs
        self.ax_kwargs = ax_kwargs
        self.rings_kwargs = rings_kwargs
        
        for name in ["density_kwargs", "cbar_kwargs", "ax_kwargs", "rings_kwargs"]:
            if getattr(self, name) is None:
                setattr(self, name, {})

class ReplayGraphCfg(BaseGraphCfg):
    def __init__(self, scatter_kwargs=None, density_kwargs=None, colorbar_kwargs=None, x_lims=None, vel_colors=False,
        show_rings=True, show_density=False, show_cm=False,
        begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug)
        self.x_lims = x_lims
        self.vel_colors=  vel_colors
        self.show_density = show_density
        self.show_rings = show_rings
        self.show_cm = show_cm

        self.scatter_kwargs = scatter_kwargs
        if scatter_kwargs is None:
            self.scatter_kwargs = {}
        
        self.density_kwargs = density_kwargs
        if density_kwargs is None:
            self.density_kwargs = {}
        
        self.colorbar_kwargs = colorbar_kwargs
        if colorbar_kwargs is None:
            self.colorbar_kwargs = {}

if __name__ == "__main__":
    print(type(SimpleGraphCfg) == type)