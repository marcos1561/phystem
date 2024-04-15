class BaseGraphCfg:
    def __init__(self, begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True) -> None:
        self.begin_paused = begin_paused
        self.pause_on_high_vel = pause_on_high_vel
        self.cpp_is_debug = cpp_is_debug


class MainGraphCfg(BaseGraphCfg):
    def __init__(self, show_circles=False, show_f_spring=False, show_f_vol=False, show_f_area=False, 
        show_f_total=False, show_center_mass=False, show_inside=False, force_to_color=None, begin_paused=False, 
        pause_on_high_vel=False, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug)

        self.show_circles = show_circles
        self.show_f_spring = show_f_spring
        self.show_f_vol = show_f_vol
        self.show_f_area = show_f_area
        self.show_f_total = show_f_total
        self.show_center_mass = show_center_mass
        self.show_inside = show_inside

        self.show_pos_cont = False

        self.force_to_color = force_to_color
        if force_to_color is None:
            self.force_to_color = {
                "spring": "red",
                "vol": "blue",
                "area": "green",
                "total": "black",
            }

    def get_show_forces(self):
        # return self.f_name_to_show[name]
        return {
            "spring": self.show_f_spring,
            "vol": self.show_f_vol,
            "area": self.show_f_area,
            "total": self.show_f_total,
        }

    def set_show_force(self, name: str, value: bool):
        if name == "spring":
            self.show_f_spring = value
        elif name == "vol":
            self.show_f_vol = value
        elif name == "area":
            self.show_f_area = value
        elif name == "total":
            self.show_f_total = value

class SimpleGraphCfg(BaseGraphCfg):
    def __init__(self, begin_paused=False, pause_on_high_vel=False, show_rings=True, show_density=False,
        density_kwargs=None, rings_kwargs=None, cell_shape=None, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug)
        self.show_rings = show_rings
        self.show_density = show_density
        self.cell_shape = cell_shape

        self.density_kwargs = density_kwargs
        if density_kwargs is None:
            self.density_kwargs = {}
        
        self.rings_kwargs = rings_kwargs
        if rings_kwargs is None:
            self.rings_kwargs = {}

class ReplayGraphCfg(BaseGraphCfg):
    def __init__(self, scatter_kwargs=None, density_kwargs=None, x_lims=None, vel_colors=False,
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

