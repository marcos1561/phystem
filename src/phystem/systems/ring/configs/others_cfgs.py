class StokesCfg:
    def __init__(self, obstacle_r: float, obstacle_x: float, obstacle_y: float,
        create_length: float, remove_length: float, flux_force: float, 
        obs_force: float, num_max_rings: int, vel_dispersion: float=0,
    ) -> None:
        self.obstacle_r = obstacle_r
        self.obstacle_x = obstacle_x
        self.obstacle_y = obstacle_y
        self.create_length = create_length
        self.remove_length = remove_length
        self.vel_dispersion = vel_dispersion
        self.flux_force = flux_force
        self.obs_force = obs_force
        self.num_max_rings = num_max_rings

    @staticmethod
    def get_null_cpp_cfg():
        return {
            "obstacle_r": 0,
            "obstacle_x": 0,
            "obstacle_y": 0,
            "create_length": 0,
            "remove_length": 0,
            "vel_dispersion": 0,
            "flux_force": 0,
            "obs_force": 0,
            "num_max_rings": -1,
        }

    def cpp_constructor_args(self):
        return {
            "obstacle_r": self.obstacle_r,
            "obstacle_x": self.obstacle_x,
            "obstacle_y": self.obstacle_y,
            "create_length": self.create_length,
            "remove_length": self.remove_length,
            "vel_dispersion": self.vel_dispersion,
            "flux_force": self.flux_force,
            "obs_force": self.obs_force,
            "num_max_rings": self.num_max_rings,
        }

class InvaginationCfg:
    def __init__(self, upper_k: float, bottom_k: float, num_affected: int):
        self.upper_k = upper_k
        self.bottom_k = bottom_k
        self.num_affected = num_affected 