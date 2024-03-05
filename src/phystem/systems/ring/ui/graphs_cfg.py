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
    def __init__(self, begin_paused=False, pause_on_high_vel=False, cpp_is_debug=True) -> None:
        super().__init__(begin_paused, pause_on_high_vel, cpp_is_debug)